"""Optional cited extraction and policy-grounded drafts, separate from grading."""

from dwelly_bot.analysis.session import AnalysisContext
from dwelly_bot.context.evidence import (
    EvidenceText,
    ProcedureDraft,
    RecordInsights,
    check_citations,
)
from dwelly_bot.resources import text


async def extract(
    ctx: AnalysisContext, sources: list[EvidenceText], *, source_kind: str | None = None
) -> RecordInsights:
    if not sources:
        raise ValueError("Extraction requires public or explicitly historical sources")
    check_citations([], sources)

    def check(result: RecordInsights) -> None:
        result.check_sources(sources)
        if source_kind in {"question", "policy", "document"} and result.reported_actions:
            raise ValueError(
                "There is no observed agent in this source type; reported_actions must be empty"
            )

    return await ctx.ask(
        "fact-extraction",
        {"sources": [s.model_dump() for s in sources], "source_kind": source_kind},
        RecordInsights,
        text("prompts/fact-extraction.md"),
        validate=check,
        repair=source_kind is not None,
    )


async def draft_procedure(
    ctx: AnalysisContext,
    intent: str,
    policies: list[EvidenceText],
    tools: list[str],
) -> ProcedureDraft:
    if not policies or any(s.role != "public" for s in policies):
        raise ValueError(
            "No current public policy supplied; procedure mining cannot infer authority"
        )
    return await ctx.ask(
        "procedure-draft",
        {
            "intent": intent,
            "policies": [s.model_dump() for s in policies],
            "available_tools": tools,
        },
        ProcedureDraft,
        text("prompts/procedure-draft.md"),
        validate=lambda result: result.check_sources(policies, tools),
        repair=True,
    )
