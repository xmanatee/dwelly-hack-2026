"""Record construction from explicit fields; never bulk-import verifier or private prompts."""

from pathlib import Path

from dwelly_bot.analysis.data import Table
from dwelly_bot.analysis.discovery import DiscoveryConfig, discover
from dwelly_bot.analysis.discovery_report import add_discovery_views
from dwelly_bot.analysis.discovery_types import DiscoveryRecord, SourceKind
from dwelly_bot.analysis.semantic import EmbeddingConfig
from dwelly_bot.analysis.session import AnalysisContext
from dwelly_bot.context.evidence import EvidenceText
from dwelly_bot.reporting.models import Report
from dwelly_bot.storage import load_json


def text_records(
    table: Table, *, id_column: str, text: str, kind: SourceKind, domain: str
) -> list[DiscoveryRecord]:
    if table.role == "evaluation_only":
        raise ValueError("Private evaluation data is not an analysis corpus")
    table.require(id_column, text)
    return [
        DiscoveryRecord(
            id=str(row[id_column]),
            title=str(row.get("title", row[id_column])),
            kind=kind,
            domain=domain,
            sources=[EvidenceText.model_validate(s) for s in row["sources"]]
            if row.get("sources")
            else [
                EvidenceText(
                    id=table.name + "/" + str(row[id_column]),
                    text=str(row[text]),
                    source=table.name,
                    role=table.role,
                )
            ],
        )
        for row in table.rows
    ]


def saved_conversations(path: Path, *, domain: str = "") -> list[DiscoveryRecord]:
    """Actual public messages only; no model-role prompts, labels, reference actions or private context."""
    bundle = load_json(path)
    result = []
    for run in bundle["runs"]:
        for case in run["cases"]:
            conversation = (case.get("state_snapshots", {}).get("after") or {}).get(
                "conversation", []
            )
            sources = []
            for index, turn in enumerate(conversation):
                role = str(turn.get("role", "unknown"))
                message = turn.get("message")
                if message is not None:
                    sources.append(
                        EvidenceText(
                            id=f"{run['id']}/{case['id']}/turn-{index}",
                            text=str(message),
                            speaker=role,
                            origin="message",
                            timestamp=str(turn["timestamp"])
                            if turn.get("timestamp") is not None
                            else None,
                            source="captured_conversation",
                            role="historical",
                        )
                    )
            if sources:
                result.append(
                    DiscoveryRecord(
                        id=run["id"] + "/" + case["id"],
                        title=case.get("title", case["id"]),
                        kind="conversation",
                        domain=domain,
                        sources=sources,
                    )
                )
    return result


async def requested_discovery(
    report: Report,
    ctx: AnalysisContext,
    records: list[DiscoveryRecord],
    *,
    scope: str,
    tools: list[str],
) -> None:
    if not ctx.parameters.get("deep_analysis"):
        return
    ctx.parameters["analysis_tools"] = tools
    embedding = (
        EmbeddingConfig(
            model=ctx.parameters["embedding_model"],
            provider=ctx.parameters.get("embedding_provider", "openrouter"),
            key_env=ctx.parameters.get("embedding_key_env", "OPENROUTER_API_KEY"),
        )
        if ctx.parameters.get("embedding_model") != "lexical"
        else None
    )
    cfg = DiscoveryConfig(
        batch_size=int(ctx.parameters.get("screen_batch", 12)),
        deep_sample=int(ctx.parameters.get("deep_sample", 12)),
        audit_sample=int(ctx.parameters.get("audit_sample", 5)),
        seed=int(ctx.parameters.get("seed", 0)),
        embedding=embedding,
    )
    view = Report(title=report.title, subtitle=report.subtitle)
    result = await discover(ctx, records, cfg)
    add_discovery_views(view, records, result, scope=scope)
    report.blocks = view.blocks + report.blocks
