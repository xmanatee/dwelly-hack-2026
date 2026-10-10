"""Banking development cases with a strict, case-local decision-time evidence boundary."""

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dwelly_bot.context.documents import Documents
from dwelly_bot.contracts import AgentCase, RunConfig, SolutionOutput
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.paths import DATASET
from dwelly_bot.planner.context import case_input, tool_specs
from dwelly_bot.planner.contracts import PlanInput
from dwelly_bot.planner.planner import advisory, plan_case
from dwelly_bot.tools.arithmetic import calculate

TRACK = "Banking & Financial Services"
DATASET_NAME = "dwelly-banking"


class DevelopmentCase(BaseModel):
    """The installed view contract; public examples can never become challenge cases."""

    model_config = ConfigDict(extra="forbid", strict=True)
    id: str
    organizer_id: str = Field(pattern=r"^\d{3}$")
    track: Literal["Banking & Financial Services"]
    split: Literal["development"]
    request: str = Field(min_length=1)
    decision_time: str
    visible_events: int = Field(ge=1)
    sources: list[str]
    view_version: Literal[1, 2] = 1
    decision_profile: str | None = None
    evidence_documents: list[str] = Field(default_factory=lambda: ["request.md", "history.md"])

    @model_validator(mode="after")
    def identity_and_view(self) -> "DevelopmentCase":
        if self.id != f"banking-{self.organizer_id}":
            raise ValueError("Invalid organizer case identity")
        names = self.evidence_documents
        if len(names) != len(set(names)) or not {"request.md", "history.md"} <= set(names):
            raise ValueError("Invalid evidence document inventory")
        if any(
            not re.fullmatch(r"(?:attachments/)?[\w.-]+\.md", name) or ".." in name
            for name in names
        ):
            raise ValueError("Invalid evidence document path")
        if self.view_version == 1 and (self.visible_events != 2 or len(names) != 2):
            raise ValueError("Historical v1 means two events with no attachments")
        if self.view_version == 2 and not self.decision_profile:
            raise ValueError("A v2 view needs an explicit decision profile")
        return self


def initial_view(index: str, history: str, *, events: int = 2) -> tuple[str, str, str]:
    """Select the initial request and an explicit chronological prefix, never a summary.

    Headings, completed status, totals, overview, next-action and outcome sections can
    reveal the ending. Attachments require separate time-of-availability evidence.
    """
    request = re.search(r"^## Initial request\s*\n(.*?)(?=^## |\Z)", index, re.M | re.S)
    matches = list(
        re.finditer(r"^## (\d{4}-\d{2}-\d{2} [\d:]+ UTC) — event (\d+)\s*$", history, re.M)
    )
    if request is None or events < 1 or len(matches) <= events:
        raise ValueError("Missing initial request or insufficient history for a held-out future")
    if [int(m[2]) for m in matches] != list(range(1, len(matches) + 1)):
        raise ValueError("History event IDs are not contiguous")
    if [m[1] for m in matches] != sorted(m[1] for m in matches):
        raise ValueError("History is not chronological")
    # Start at the first event, omitting the outcome-revealing history title and total.
    visible = history[matches[0].start() : matches[events].start()]
    visible = re.sub(r'<a id="event-\d+"></a>\s*', "", visible).strip()
    return request[1].strip(), visible + "\n", matches[events - 1][1]


def decision_input(
    identifier: str,
    request: str,
    number: str,
    decision_time: str,
    visible_events: int,
    *,
    attachments: bool,
) -> dict[str, Any]:
    """The solver's case input; plan evaluation builds the same fields for its cut-off points."""
    return {
        "request": request,
        "organizer_id": number,
        "track": TRACK,
        "decision_time": decision_time,
        "visible_events": visible_events,
        "evidence_directory": identifier,
        "task": "Review the available case evidence and give the next supported response and action plan. Clearly state what remains unverified and which actions require a bank operator.",
        "capabilities": "Read-only case evidence and arithmetic. No bank systems, customer messaging or operational write tools are connected.",
        "attachment_policy": (
            "Only the listed attachment text is available at this decision point. "
            "A supplied file does not establish bank receipt, validation, authorisation or execution."
            if attachments
            else "Attachments are withheld: availability at this decision time has not been established."
        ),
    }


class BankingAdapter:
    name = DATASET_NAME
    dataset_root = DATASET
    state_mode: Literal["static"] = "static"

    def load_cases(self, root: Path, ids: list[str] | None = None) -> list[AgentCase]:
        rows = json.loads((root / "cases.json").read_text())
        cases = []
        for row in rows:
            record = DevelopmentCase.model_validate(row)
            row = record.model_dump()
            number = row["organizer_id"]
            cases.append(
                AgentCase(
                    id=row["id"],
                    dataset=self.name,
                    title=f"Banking case {number}",
                    input=decision_input(
                        row["id"],
                        row["request"],
                        number,
                        row["decision_time"],
                        row["visible_events"],
                        attachments=record.view_version == 2,
                    ),
                    metadata={
                        "split": "development",
                        "organizer_id": number,
                        "evidence_documents": record.evidence_documents,
                        "view_version": record.view_version,
                        "decision_profile": record.decision_profile,
                    },
                    sources=row["sources"],
                )
            )
        if len({c.id for c in cases}) != len(cases):
            raise ValueError("Duplicate case IDs")
        if ids is None:
            return cases
        by_id = {c.id: c for c in cases}
        if set(ids) - by_id.keys():
            raise ValueError(f"Unknown case IDs: {sorted(set(ids) - by_id.keys())}")
        return [by_id[cid] for cid in ids]

    def prepare(self, case: AgentCase, root: Path, config: RunConfig) -> "BankingSession":
        # Derive from the validated ID, never an arbitrary path in case input.
        if not re.fullmatch(r"banking-\d{3}", case.id):
            raise ValueError("Invalid case evidence boundary")
        folder = root / "documents" / case.id
        if not folder.resolve().is_relative_to((root / "documents").resolve()):
            raise ValueError("Case evidence escapes its root")
        documents = Documents(folder)
        expected = set(case.metadata.get("evidence_documents", ["request.md", "history.md"]))
        if set(documents.files) != expected:
            raise ValueError("Case evidence differs from the declared decision-point inventory")
        history = (folder / "history.md").read_text()
        events = re.findall(r"^## (\d{4}-\d{2}-\d{2} [\d:]+ UTC) — event (\d+)\s*$", history, re.M)
        if (
            not events
            or len(events) != case.input["visible_events"]
            or [int(event[1]) for event in events] != list(range(1, len(events) + 1))
            or [event[0] for event in events] != sorted(event[0] for event in events)
            or events[-1][0] != case.input["decision_time"]
        ):
            raise ValueError("History does not match the declared decision point")
        return BankingSession(case, documents)

    def grade_saved(
        self, case: AgentCase, root: Path, config: RunConfig, execution: dict[str, Any]
    ) -> dict[str, Any]:
        completed = execution.get("execution_status") == "completed"
        answer = str(execution.get("answer") or "")
        rationale = str(execution.get("public_rationale") or "")
        reads = [
            e
            for e in execution.get("tool_events", [])
            if e.get("tool") == "read_document" and e.get("status") == "returned"
        ]
        citations = re.findall(
            r"(?<![\w./-])((?:[\w-]+/)*[\w.-]+\.md):L(\d+)(?:-L?(\d+))?",
            answer + "\n" + rationale,
        )
        observed = set()
        for event in reads:
            result = event.get("result", {})
            if isinstance(result, dict):
                for line in str(result.get("text", "")).splitlines():
                    match = re.match(r"(\d+):", line)
                    if match:
                        observed.add((result.get("document"), int(match[1])))
        valid_citations = bool(citations) and all(
            int(end or start) >= int(start)
            and int(end or start) - int(start) <= 200
            and all(
                (document, line) in observed for line in range(int(start), int(end or start) + 1)
            )
            for document, start, end in citations
        )
        return {
            "status": "available",
            "goal_pass": None,
            "reason": "No trusted outcome labels at this decision point; correctness is unknown.",
            "checks": [
                {
                    "id": "answer_present",
                    "label": "Answer and public rationale present",
                    "status": "pass"
                    if completed and answer.strip() and rationale.strip()
                    else "fail",
                },
                {
                    "id": "evidence_read",
                    "label": "Case evidence read",
                    "status": "pass" if reads else "fail",
                },
                {
                    "id": "citation_observed",
                    "label": "Cited lines were observed",
                    "status": "pass" if valid_citations else "fail",
                    "reason": "Checks citation existence only, not whether the evidence supports the claim.",
                },
                {
                    "id": "outcome_correctness",
                    "label": "Outcome correctness",
                    "status": "unknown",
                    "reason": "Completed public histories are examples, not independent ground truth.",
                },
            ],
        }


class BankingSession:
    def __init__(self, case: AgentCase, documents: Documents) -> None:
        self.case, self.documents = case, documents
        self.plan: dict[str, Any] | None = None

    def tool_groups(self) -> list[tuple[str, dict[str, Callable[..., Any]], str]]:
        """Solver tools by toolset and module; the planner's catalogue uses the same bindings."""
        return [
            (
                "documents",
                {
                    "list_documents": self.documents.list_documents,
                    "read_document": self.documents.read_document,
                    "search_documents": self.documents.search_documents,
                },
                "knowledge",
            ),
            ("calculator", {"calculate": calculate}, "calculator"),
        ]

    def plan_input(self, config: RunConfig) -> PlanInput:
        enabled = {
            name: function
            for _, bindings, module in self.tool_groups()
            if getattr(config.modules, module)
            for name, function in bindings.items()
            if name not in config.disabled_tools
        }
        texts = {name: path.read_text() for name, path in self.documents.files.items()}
        return case_input(self.case, texts, tool_specs(enabled))

    async def run(self, runtime: CaseRuntime) -> SolutionOutput:
        planner = runtime.config.planner
        advice: list[str] = []
        if planner and planner.mode == "advisory":
            self.plan = await plan_case(runtime, self.plan_input(runtime.config), planner)
            if self.plan["status"] == "available":
                advice.append(advisory(self.plan["plan"]))
        agent = runtime.agent(
            output_type=SolutionOutput,
            output_name="case_answer",
            instructions=runtime.instructions("banking", *advice),
            toolsets=[
                runtime.toolset(name, bindings, module=module)
                for name, bindings, module in self.tool_groups()
            ],
        )
        result = await runtime.ask(agent, self.case.input)
        return SolutionOutput.model_validate(result.output)

    def snapshot(self) -> dict[str, Any]:
        return {
            "case_id": self.case.id,
            "decision_time": self.case.input["decision_time"],
            "documents": self.documents.list_documents(),
            "operational_writes_available": False,
            **({"plan": self.plan} if self.plan is not None else {}),
        }
