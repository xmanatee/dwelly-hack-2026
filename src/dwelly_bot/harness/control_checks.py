"""Experimental evidence checklist; model observations never confer authority."""

from __future__ import annotations

from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field
from pydantic_ai import ModelRetry

from dwelly_bot.context.evidence import Citation, EvidenceText
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.resources import text
from dwelly_bot.storage import fingerprint


class Guard(Protocol):
    def guard(self, name: str, read_only: bool) -> None: ...


class ControlQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str = Field(min_length=1)
    question: str = Field(min_length=1)
    required_action: str = Field(min_length=1)
    handling: Literal["adapt", "clarify", "human_review", "deny"]
    blocked_tools: tuple[str, ...] = ()
    policy_source: str = Field(min_length=1)


class ControlAnswer(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    value: Literal["yes", "no", "unknown"]
    reason: str = Field(min_length=1)
    evidence: tuple[Citation, ...] = ()


class ControlAnswers(BaseModel):
    model_config = ConfigDict(extra="forbid")
    answers: list[ControlAnswer]


class ControlRequired(ValueError):
    """Covered operation is waiting for information or the configured human route."""


class ControlChecklist:
    def __init__(self, questions: list[ControlQuestion], *, parent: Guard | None = None) -> None:
        self._questions = tuple(questions)
        if not questions or len({q.id for q in questions}) != len(questions):
            raise ValueError("Configure nonempty, unique control questions")
        self.parent = parent
        self._sources: tuple[EvidenceText, ...] = ()
        self._answers: dict[str, ControlAnswer] = {}
        self.revision = "not_assessed"

    @property
    def questions(self) -> tuple[ControlQuestion, ...]:
        return self._questions

    def set_sources(self, sources: list[EvidenceText]) -> None:
        if len({s.id for s in sources}) != len(sources) or any(
            s.role == "evaluation_only" for s in sources
        ):
            self._answers.clear()
            raise ValueError("Use unique case evidence sources, never evaluator-only context")
        revision = fingerprint(
            {
                "questions": [q.model_dump(mode="json") for q in self.questions],
                "sources": [s.model_dump(mode="json") for s in sources],
            }
        )
        if revision != self.revision:
            self._sources = tuple(s.model_copy(deep=True) for s in sources)
            self._answers.clear()
            self.revision = revision

    def check(self, result: ControlAnswers, revision: str) -> None:
        if revision != self.revision or revision == "not_assessed":
            raise ValueError("Assessment refers to stale or missing context")
        ids = [answer.id for answer in result.answers]
        if len(ids) != len(set(ids)) or set(ids) != {q.id for q in self.questions}:
            raise ValueError("Answer every configured question exactly once")
        sources = {source.id: source.text for source in self._sources}
        for answer in result.answers:
            if answer.value != "unknown" and not answer.evidence:
                raise ValueError("Yes/no observations require explicit source evidence")
            for citation in answer.evidence:
                if not citation.quote.strip() or citation.quote not in sources.get(
                    citation.source_id, ""
                ):
                    raise ValueError("Control answer cites unsupported evidence")

    def accept(self, result: ControlAnswers, revision: str) -> None:
        self.check(result, revision)
        self._answers = {answer.id: answer.model_copy(deep=True) for answer in result.answers}

    def classify(self) -> dict[str, Any]:
        checks = []
        for question in self.questions:
            answer = self._answers.get(question.id)
            value = answer.value if answer else "unknown"
            checks.append(
                {
                    **question.model_dump(mode="json"),
                    "value": value,
                    "reason": answer.reason
                    if answer
                    else "Required context check has not completed",
                    "evidence": [c.model_dump() for c in answer.evidence] if answer else [],
                    "next_step": "obtain_missing_evidence"
                    if value == "unknown"
                    else question.handling
                    if value == "yes"
                    else "no_trigger_observed",
                }
            )
        return {
            "context_revision": self.revision,
            "coverage": "configured_questions_only",
            "checks": checks,
        }

    def guard(self, name: str, read_only: bool) -> None:
        if self.parent:
            self.parent.guard(name, read_only)
        pending = [
            row
            for row in self.classify()["checks"]
            if row["value"] != "no" and name in row["blocked_tools"]
        ]
        if pending:
            raise ControlRequired(
                "Required controls block "
                + name
                + ": "
                + "; ".join(
                    row["id"] + " — " + row["next_step"] + ": " + row["required_action"]
                    for row in pending
                )
            )

    async def assess(self, runtime: CaseRuntime, sources: list[EvidenceText]) -> dict[str, Any]:
        """Pipeline checkpoint, not an optional tool offered to the acting agent."""
        self.set_sources(sources)
        revision = self.revision
        self._answers.clear()
        agent = runtime.agent(
            output_type=ControlAnswers,
            output_name="control_observations",
            role="policy",
            instructions=text("prompts/control-checks.md", package="dwelly_bot"),
        )

        @agent.output_validator
        def grounded(result: ControlAnswers) -> ControlAnswers:
            try:
                self.check(result, revision)
            except ValueError as error:
                raise ModelRetry(str(error)) from error
            return result

        async def inspect(**_: Any) -> ControlAnswers:
            result = await runtime.ask(
                agent,
                {
                    "questions": [q.model_dump(mode="json") for q in self.questions],
                    "sources": [s.model_dump(mode="json") for s in self._sources],
                },
                role="policy",
            )
            return ControlAnswers.model_validate(result.output)

        saved = await runtime.journal.call(
            "assess_controls",
            {"context_revision": revision, "question_ids": [q.id for q in self.questions]},
            inspect,
            kind="control_check",
            role="policy",
            read_only=True,
        )

        self.accept(ControlAnswers.model_validate(saved), revision)
        return self.classify()
