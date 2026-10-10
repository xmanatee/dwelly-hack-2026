"""Execution consumes decisions; mock receipts never claim real external effects."""

from dwelly_bot.execution.mock import ExecutionResult, Executor, MockExecutor

__all__ = ["ExecutionResult", "Executor", "MockExecutor"]
