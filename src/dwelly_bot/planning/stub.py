"""Deliberately constant offline placeholder; no skills, policy inference or model calls."""

from dwelly_bot.planning.contracts import Handoff, Plan, ReplyToTrigger


class HumanReviewPlanner:
    async def plan(self, context: str) -> Plan:
        if not context.strip():
            raise ValueError("Planner requires context text")
        return Plan(
            decision="Request human review and acknowledge the original request.",
            disposition="human_review",
            actions=(
                Handoff(
                    id="review",
                    queue="human-support",
                    reason="Placeholder planner; human review required.",
                ),
                ReplyToTrigger(
                    id="acknowledge", message="Your request needs review by a human support agent."
                ),
            ),
            rationale="This scaffold always chooses human review. No banking decision has been made.",
        )
