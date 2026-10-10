"""Build planner input from a case's decision-point evidence and the solver's tool bindings."""

import re
from collections.abc import Callable
from typing import Any

from pydantic_ai import Tool

from dwelly_bot.contracts import AgentCase
from dwelly_bot.planner.contracts import PlanDocument, PlanEvent, PlanInput, ToolSpec

EVENT = re.compile(
    r"^## (?P<at>[^\n]+?) — event (?P<number>\d+)\n+"
    r"- \*\*Channel:\*\* (?P<channel>[^\n]*)\n"
    r"- \*\*From:\*\* (?P<sender>[^\n]*)\n"
    r"- \*\*To:\*\* (?P<recipient>[^\n]*)\n+"
    r"(?P<text>.*?)(?=^## [^\n]+ — event \d+$|\Z)",
    re.MULTILINE | re.DOTALL,
)


def parse_events(history: str) -> list[PlanEvent]:
    """Timed events from a history document; an unparsed history stays a plain document."""
    return [
        PlanEvent(
            id=f"event-{m['number']}",
            at=m["at"].strip(),
            channel=m["channel"].strip(),
            sender=m["sender"].strip(),
            recipient=m["recipient"].strip(),
            text=re.sub(r'<a id="[^"]*"></a>\s*', "", m["text"]).strip(),
        )
        for m in EVENT.finditer(history)
    ]


def tool_specs(bindings: dict[str, Callable[..., Any]], read_only: bool = True) -> list[ToolSpec]:
    specs = []
    for name, function in bindings.items():
        definition = Tool(function, name=name, takes_ctx=False).tool_def
        specs.append(
            ToolSpec(
                name=name,
                description=definition.description or name,
                parameters=definition.parameters_json_schema,
                read_only=read_only,
            )
        )
    return specs


def case_input(
    case: AgentCase, documents: dict[str, str], tools: list[ToolSpec], history: str = "history.md"
) -> PlanInput:
    """Only the case's decision-point documents are used; adapters own that boundary."""
    events = parse_events(documents.get(history, ""))
    others = {
        name: text
        for name, text in documents.items()
        if name != "request.md" and not (name == history and events)
    }
    datapoints = {key: value for key, value in case.input.items() if key not in {"request", "task"}}
    return PlanInput(
        case_id=case.id,
        decision_time=str(case.input.get("decision_time", "")),
        request=str(case.input.get("request", "")),
        task=str(case.input.get("task", "")),
        events=events,
        documents=[PlanDocument(name=name, text=text) for name, text in others.items()],
        datapoints=datapoints,
        solver_tools=tools,
    )


def history_view(history: str, *, events: int) -> tuple[str, str, str]:
    """The first `events` events of a history, from history.md alone.

    Returns the first non-bank message as the request, the visible events as Markdown and
    the last visible timestamp. The title and total-count header are dropped; at least one
    later event must remain held out.
    """
    parsed = parse_events(history)
    if not 1 <= events < len(parsed):
        raise ValueError("A history view needs at least one visible and one held-out event")
    visible = parsed[:events]
    customer = next(
        (e for e in visible if not e.sender.lower().startswith(("h&v", "harrow"))), None
    )
    text = "\n\n".join(
        f"## {e.at} — event {e.id.removeprefix('event-')}\n\n"
        f"- **Channel:** {e.channel}\n- **From:** {e.sender}\n- **To:** {e.recipient}\n\n{e.text}"
        for e in visible
    )
    return (customer.text if customer else ""), text + "\n", visible[-1].at
