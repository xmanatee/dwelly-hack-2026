"""A read-only context agent; business decisions remain in Vera's Planner."""

from dwelly_bot.channels.intake import Contract
from dwelly_bot.context.collector import (
    ContextQuery,
    ContextSource,
    Investigation,
    SourceResult,
    visible_result,
)
from dwelly_bot.contracts import RunConfig
from dwelly_bot.experiments.journal import Journal
from dwelly_bot.harness.runtime import CaseRuntime
from dwelly_bot.models import BudgetedModel
from dwelly_bot.resources import text


class ResearchSummary(Contract):
    needs: tuple[str, ...]
    gaps: tuple[str, ...] = ()


class AgentInvestigator:
    def __init__(self, model: BudgetedModel, config: RunConfig | None = None) -> None:
        self.model = model
        self.config = config or RunConfig(max_requests=8, max_tool_calls=12)

    async def gather(
        self, query: ContextQuery, sources: tuple[ContextSource, ...], journal: Journal
    ) -> Investigation:
        model = self.model.scoped(f"context/{query.scope_id}")
        runtime = CaseRuntime(model, self.config, journal)
        available = {s.name: s for s in sources}
        observed: list[SourceResult] = []

        async def read_source(source: str, question: str) -> dict[str, object]:
            """Read a named source for a specific information need; scope and time cannot be changed."""
            if source not in available:
                raise ValueError("Choose a source from the supplied catalogue")
            request = query.model_copy(update={"question": question})
            result = visible_result(request, await available[source].lookup(request))
            observed.append(result)
            return result.model_dump(mode="json")

        agent = runtime.agent(
            output_type=ResearchSummary,
            output_name="context_research",
            instructions=text("prompts/context-investigator.md"),
            role="context",
            tools=[
                runtime.tool(
                    "read_source", read_source.__doc__ or "Read source", read_source, read_only=True
                )
            ],
        )
        try:
            response = await runtime.ask(
                agent,
                {
                    "request": query.question,
                    "hints": query.hints.model_dump(mode="json"),
                    "sources": [
                        {"name": s.name, "description": s.__doc__ or s.name} for s in sources
                    ],
                },
                role="context",
            )
            summary = ResearchSummary.model_validate(response.output)
            return Investigation(
                records=tuple(r for batch in observed for r in batch.records),
                needs=summary.needs,
                warnings=(*summary.gaps, *(w for batch in observed for w in batch.warnings)),
            )
        finally:
            journal.append(
                {"kind": "context_model_trace", "roles": runtime.role_records, "costs": model.calls}
            )
