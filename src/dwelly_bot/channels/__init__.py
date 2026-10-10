"""Normalize transport events without collecting context or making decisions."""

from dwelly_bot.channels.intake import CallInput, EmailInput, TicketInput, Trigger, normalize

__all__ = ["CallInput", "EmailInput", "TicketInput", "Trigger", "normalize"]
