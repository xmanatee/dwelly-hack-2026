"""Execution consumes decisions; mock receipts never claim real external effects."""

from dwelly_bot.execution.contracts import ExecutionResult, Executor
from dwelly_bot.execution.mock import MockExecutor

__all__ = ["ExecutionResult", "Executor", "MockExecutor"]
