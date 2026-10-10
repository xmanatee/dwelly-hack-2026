"""Rebuild taxonomy from saved cited extractions; never rerun the subject or screening."""

from dwelly_bot.analysis import AnalysisContext, Report
from dwelly_bot.analysis.discovery_report import add_discovery_views
from dwelly_bot.analysis.discovery_types import DiscoveryRecord, ScreenedRecord
from dwelly_bot.analysis.taxonomy import build_taxonomy
from dwelly_bot.context.evidence import check_citations
from dwelly_bot.storage import file_hash, load_json, save_json


async def build(ctx: AnalysisContext) -> Report:
    source = ctx.data / "discovery.json"
    result = load_json(source)
    saved = ctx.data / "records.json"
    original = [DiscoveryRecord.model_validate(value) for value in load_json(saved)]
    records = {record.id: record for record in original}
    if len(records) != len(original):
        raise ValueError("Saved analysis contains duplicate source records")
    ctx.sources["records.json"] = file_hash(saved)
    screens = {id: ScreenedRecord.model_validate(value) for id, value in result["screens"].items()}
    if len(records) != result["eligible_records"] or screens.keys() - records.keys():
        raise ValueError("Saved analysis is missing original source records")
    check_citations(
        [], (source for record in records.values() for source in record.sources), unique=False
    )
    for id, row in screens.items():
        row.check(records[id])
    ctx.sources["discovery.json"] = file_hash(source)
    taxonomy = await build_taxonomy(ctx, screens, kinds=sorted({r.kind for r in records.values()}))
    result = {
        **result,
        "taxonomy": taxonomy.model_dump(mode="json"),
        "parent_discovery": str(source),
        "errors": [e for e in result["errors"] if not e.get("stage", "").startswith("taxonomy")]
        + [
            {"stage": "taxonomy-assignments", "error": error}
            for error in taxonomy.assignment_errors
        ],
        # These artifacts refer to the previous taxonomy and must be recomputed explicitly.
        "observed_patterns": {"patterns": []},
        "procedure_drafts": [],
        "observed_pattern_eligible_intents": None,
        "taxonomy_dependents_status": "not_recomputed",
    }
    save_json(ctx.output / "records.json", [r.model_dump(mode="json") for r in records.values()])
    save_json(ctx.output / "discovery.json", result)
    save_json(ctx.output / "intent_taxonomy.json", result["taxonomy"])
    report = Report(
        title="Refined operational discovery",
        subtitle="Saved screening · fresh taxonomy · procedures not recomputed",
    )
    add_discovery_views(
        report, list(records.values()), result, scope="Previously screened source records"
    )
    return report
