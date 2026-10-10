"""Banking development cases with a strict, case-local decision-time evidence boundary."""

import json
import re
from pathlib import Path
from typing import Any, Literal

from dwelly_bot.context.documents import Documents
from dwelly_bot.contracts import AgentCase, RunConfig, SolutionOutput
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.paths import DATASET
from dwelly_bot.tools.arithmetic import calculate

TRACK = "Banking & Financial Services"
DATASET_NAME = "dwelly-banking"


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


class BankingAdapter:
    name = DATASET_NAME
    dataset_root = DATASET
    state_mode: Literal["static"] = "static"

    def load_cases(self, root: Path, ids: list[str] | None = None) -> list[AgentCase]:
        rows = json.loads((root / "cases.json").read_text())
        cases = []
        for row in rows:
            number = row["organizer_id"]
            if not re.fullmatch(r"\d{3}", number) or row["id"] != f"banking-{number}":
                raise ValueError("Invalid organizer case identity")
            if row["track"] != TRACK or row["split"] != "development":
                raise ValueError("Expected Banking development data")
            cases.append(
                AgentCase(
                    id=row["id"],
                    dataset=self.name,
                    title=f"Banking case {number}",
                    input={
                        "request": row["request"],
                        "organizer_id": number,
                        "track": TRACK,
                        "decision_time": row["decision_time"],
                        "visible_events": row["visible_events"],
                        "evidence_directory": row["id"],
                        "task": "Review the available case evidence and give the next supported response and action plan. Clearly state what remains unverified and which actions require a bank operator.",
                        "capabilities": "Read-only case evidence and arithmetic. No bank systems, customer messaging or operational write tools are connected.",
                        "attachment_policy": "Attachments are withheld: availability at this decision time has not been established.",
                    },
                    metadata={"split": "development", "organizer_id": number},
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
        return BankingSession(case, Documents(folder))

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
        citations = re.findall(r"([\w-]+\.md):L(\d+)(?:-L?(\d+))?", answer + "\n" + rationale)
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

    async def run(self, runtime: CaseRuntime) -> SolutionOutput:
        agent = runtime.agent(
            output_type=SolutionOutput,
            output_name="case_answer",
            instructions=runtime.instructions("banking"),
            toolsets=[
                runtime.toolset(
                    "documents",
                    {
                        "list_documents": self.documents.list_documents,
                        "read_document": self.documents.read_document,
                        "search_documents": self.documents.search_documents,
                    },
                    module="knowledge",
                ),
                runtime.toolset("calculator", {"calculate": calculate}, module="calculator"),
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
        }
