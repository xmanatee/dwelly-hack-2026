"""Transport-neutral intake. Routing scope is supplied by a trusted adapter."""

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, TypeAdapter

Text = Annotated[str, Field(min_length=1, pattern=r"\S")]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class IdentityHints(Contract):
    """Search hints only; none of these fields establishes verified identity."""

    customer_id: Text | None = None
    name: Text | None = None
    email: Text | None = None
    phone: Text | None = None
    references: tuple[Text, ...] = ()


class Event(Contract):
    event_id: Text
    scope_id: Text  # Trusted case/access boundary, never inferred from message text.
    received_at: AwareDatetime
    text: Text
    hints: IdentityHints = Field(default_factory=IdentityHints)


class EmailInput(Event):
    channel: Literal["email"] = "email"
    sender: Text
    thread_id: Text


class CallInput(Event):
    channel: Literal["call"] = "call"
    caller: Text
    session_id: Text
    active: bool = True


class TicketInput(Event):
    channel: Literal["ticket"] = "ticket"
    ticket_id: Text


Inbound = Annotated[EmailInput | CallInput | TicketInput, Field(discriminator="channel")]
inbound_adapter: TypeAdapter[Inbound] = TypeAdapter(Inbound)


class EmailRoute(Contract):
    channel: Literal["email"] = "email"
    recipient: Text
    thread_id: Text


class CallRoute(Contract):
    channel: Literal["call"] = "call"
    session_id: Text
    active: bool


class TicketRoute(Contract):
    channel: Literal["ticket"] = "ticket"
    ticket_id: Text


ReplyRoute = Annotated[EmailRoute | CallRoute | TicketRoute, Field(discriminator="channel")]


class Trigger(Event):
    reply_route: ReplyRoute


def normalize(event: Inbound) -> Trigger:
    """Capture the original response route; the planner cannot replace it implicitly."""
    hints = event.hints
    route: ReplyRoute
    if isinstance(event, EmailInput):
        route = EmailRoute(recipient=event.sender, thread_id=event.thread_id)
        hints = hints.model_copy(update={"email": hints.email or event.sender})
    elif isinstance(event, CallInput):
        route = CallRoute(session_id=event.session_id, active=event.active)
        hints = hints.model_copy(update={"phone": hints.phone or event.caller})
    else:
        route = TicketRoute(ticket_id=event.ticket_id)
    return Trigger(
        event_id=event.event_id,
        scope_id=event.scope_id,
        received_at=event.received_at,
        text=event.text,
        hints=hints,
        reply_route=route,
    )
