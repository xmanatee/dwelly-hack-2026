"""Small provisional plan vocabulary: decisions and concrete operations, not programs."""

from typing import Annotated, Literal, Protocol, Self

from pydantic import Field, model_validator

from dwelly_bot.channels.intake import Contract, Text


class ReplyToTrigger(Contract):
    kind: Literal["reply_to_trigger"] = "reply_to_trigger"
    id: Text
    message: Text


class SendEmail(Contract):
    kind: Literal["send_email"] = "send_email"
    id: Text
    recipient: Text
    subject: Text
    message: Text


class CallCustomer(Contract):
    kind: Literal["call_customer"] = "call_customer"
    id: Text
    phone: Text
    message: Text


class UpdateTicket(Contract):
    kind: Literal["update_ticket"] = "update_ticket"
    id: Text
    ticket_id: Text
    status: Literal["open", "pending", "closed"]
    note: Text


class Handoff(Contract):
    kind: Literal["handoff"] = "handoff"
    id: Text
    queue: Text
    reason: Text


Action = Annotated[
    ReplyToTrigger | SendEmail | CallCustomer | UpdateTicket | Handoff,
    Field(discriminator="kind"),
]

ACTION_CATALOG = {
    "reply_to_trigger": "message -> original email thread, active call session, or ticket comment",
    "send_email": "recipient, subject, message -> a separate outgoing email",
    "call_customer": "phone, message -> a separate outgoing call",
    "update_ticket": "ticket_id, status (open/pending/closed), note -> a ticket update",
    "handoff": "queue, reason -> a human review request for the current case",
}


class Plan(Contract):
    decision: Text
    disposition: Literal["human_review", "respond", "act", "awaiting_input"]
    actions: tuple[Action, ...] = ()
    rationale: Text

    @model_validator(mode="after")
    def unique_action_ids(self) -> Self:
        ids = [action.id for action in self.actions]
        if len(ids) != len(set(ids)):
            raise ValueError("Plan action IDs must be unique")
        return self


class Planner(Protocol):
    async def plan(self, context: str) -> Plan: ...
