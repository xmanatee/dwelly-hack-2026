"""JSON action sets configured outside the text -> Plan call."""

import re
from typing import Literal, Self

from pydantic import model_validator

from dwelly_bot.channels.intake import Contract
from dwelly_bot.planning.contracts import (
    ACTION_CATALOG,
    Calculate,
    CallCustomer,
    Handoff,
    Plan,
    ReplyToTrigger,
    SendEmail,
    UpdateTicket,
)
from dwelly_bot.resources import text

ACTION_TYPES = {
    cls.model_fields["kind"].default: cls
    for cls in (ReplyToTrigger, SendEmail, CallCustomer, UpdateTicket, Handoff, Calculate)
}
REFERENCE = re.compile(r"\{\{([^{}]+)\}\}")


class ActionProfile(Contract):
    name: str
    execution: Literal["mock", "proposal"]
    allowed_actions: tuple[str, ...]
    handoff_queues: tuple[str, ...] = ("human-support",)

    @model_validator(mode="after")
    def known_actions(self) -> Self:
        if not set(self.allowed_actions) <= ACTION_TYPES.keys():
            raise ValueError("Action profile contains unknown action kinds")
        return self

    @classmethod
    def load(cls, name: Literal["production", "contest"] = "production") -> Self:
        return cls.model_validate_json(text(f"planning/profiles/{name}.json"))

    def catalog(self) -> dict[str, object]:
        return {
            "profile": self.model_dump(mode="json"),
            "actions": [
                {
                    "kind": kind,
                    "description": ACTION_CATALOG[kind],
                    "schema": ACTION_TYPES[kind].model_json_schema(),
                }
                for kind in self.allowed_actions
            ],
        }

    def validate_plan(self, plan: Plan) -> None:
        available: set[str] = set()
        for action in plan.actions:
            if action.kind not in self.allowed_actions:
                raise ValueError(f"Action {action.kind} is unavailable in profile {self.name}")
            if isinstance(action, Handoff) and action.queue not in self.handoff_queues:
                raise ValueError(f"Unknown handoff queue: {action.queue}")
            # Only messages/notes have data substitution. Routing and formulas are concrete.
            values = action.model_dump(include={"message", "note", "subject"})
            for value in values.values():
                for reference in REFERENCE.findall(value):
                    if reference not in available:
                        raise ValueError(f"Unknown or forward calculation reference: {reference}")
            if isinstance(action, Calculate):
                available.add(action.id + ".value")


def render_message(value: str, results: dict[str, str]) -> str:
    return REFERENCE.sub(lambda match: results[match.group(1)], value)
