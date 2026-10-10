"""Reusable exploration of configured text and actual saved benchmark runs."""

from pathlib import Path

from dwelly_bot.analysis.charts import ranking
from dwelly_bot.analysis.data import Table
from dwelly_bot.analysis.discovery_types import SourceKind
from dwelly_bot.analysis.llm import extract
from dwelly_bot.analysis.recipes import conversation_functions, sample, text_groups
from dwelly_bot.analysis.session import AnalysisContext
from dwelly_bot.budget import BudgetExceeded
from dwelly_bot.context.evidence import EvidenceText
from dwelly_bot.contracts import JsonRecord
from dwelly_bot.reporting.html import build
from dwelly_bot.reporting.models import Report
from dwelly_bot.storage import file_hash


async def add_text_analysis(
    report: Report,
    ctx: AnalysisContext,
    table: Table,
    *,
    text: str,
    id_column: str,
    title: str = "Source examples",
    note: str = "",
    source_kind: SourceKind | None = None,
) -> None:
    if table.role == "evaluation_only":
        raise ValueError("Evaluation-only tables cannot be explored by a model")
    table.require(text, id_column)
    selected = sample(
        table.rows, int(ctx.parameters.get("sample", 200)), int(ctx.parameters.get("seed", 0))
    )
    records: list[JsonRecord] = [
        {
            "id": str(row[id_column]),
            "title": str(row.get("title", row[id_column])),
            "text": str(row[text]),
            "flags": conversation_functions(str(row[text])),
            "sources": row.get("sources", []),
        }
        for row in selected
    ]
    if ctx.parameters.get("text_groups") and not ctx.parameters.get("deep_analysis"):
        groups = ctx.cached(
            "text-groups",
            records,
            lambda: text_groups(Table(table.name, selected), text, id_column),
        )
        report.table(
            "Text groups",
            groups,
            collapsed=True,
        )
        if groups:
            report.chart(
                "Text group sizes",
                ranking(groups, "group", unit="Sample records"),
                caption=f"{len(selected)} sampled records",
                note=note,
            )
    if ctx.model and not ctx.parameters.get("deep_analysis"):
        limit = int(ctx.parameters.get("llm_sample", 3))
        for row in records[:limit]:
            sources = (
                [EvidenceText.model_validate(s) for s in row["sources"]]
                if row["sources"]
                else [
                    EvidenceText(id=row["id"], text=row["text"], source=table.name, role=table.role)
                ]
            )
            row["sources"] = [s.model_dump() for s in sources]
            ctx.last_model_trace = None
            try:
                row["insights"] = (await extract(ctx, sources, source_kind=source_kind)).model_dump(
                    mode="json"
                )
            except Exception as error:
                row["flags"].append(f"Extraction failed: {type(error).__name__}")
                row["extraction_error"] = str(error)
                if isinstance(error, BudgetExceeded):
                    break
            finally:
                row["analysis_trace"] = ctx.last_model_trace
    report.records(
        title,
        records,
        caption=f"{len(selected)} / {len(table.rows)} records · seed {ctx.parameters.get('seed', 0)}",
        note=note,
    )


def add_saved_run(report: Report, ctx: AnalysisContext) -> None:
    """Show captured results separately from source analysis; never prepare/run an adapter."""
    if not ctx.parameters.get("saved_run"):
        return
    path = Path(ctx.parameters["saved_run"]).resolve()
    bundle = ctx.saved_run()
    ctx.sources["saved_run:" + str(path)] = file_hash(path)
    report.blocks.extend(build(bundle).blocks)
