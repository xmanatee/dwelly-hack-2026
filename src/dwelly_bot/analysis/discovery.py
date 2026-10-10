"""Meaningful discovery over explicit source units; frequency, risk and novelty stay separate."""

from __future__ import annotations

import asyncio
import random
from collections import Counter, defaultdict
from dataclasses import dataclass, replace
from itertools import chain, islice, zip_longest
from typing import cast

from pydantic import Field, create_model

from dwelly_bot.analysis.discovery_types import (
    AuditBatch,
    ConflictBatch,
    DiscoveryRecord,
    PatternBatch,
    ScreenBatch,
    ScreenedRecord,
    TaxonomyDraft,
)
from dwelly_bot.analysis.semantic import (
    EmbeddingConfig,
    map_records,
)
from dwelly_bot.analysis.session import AnalysisContext
from dwelly_bot.budget import BudgetExceeded
from dwelly_bot.context.evidence import check_citations
from dwelly_bot.contracts import JsonRecord
from dwelly_bot.resources import text
from dwelly_bot.storage import save_json


@dataclass(frozen=True)
class DiscoveryConfig:
    batch_size: int = 12
    min_cluster_size: int = 4
    deep_sample: int = 12
    audit_sample: int = 5
    conflict_pairs: int = 10
    flagged_audit: int = 3
    # None proposes the taxonomy from every candidate label instead of a head/tail sample.
    taxonomy_labels: int | None = 60
    seed: int = 0
    embedding: EmbeddingConfig | None = None

    def exhaustive(self, records: int) -> DiscoveryConfig:
        """Review, audit, compare and name every record and label; no sampled stage."""
        return replace(
            self,
            deep_sample=records,
            audit_sample=records,
            flagged_audit=records,
            conflict_pairs=records,
            taxonomy_labels=None,
        )


def select_review(
    records: list[DiscoveryRecord],
    screens: dict[str, ScreenedRecord],
    geometry: JsonRecord,
    *,
    limit: int,
    seed: int,
) -> list[JsonRecord]:
    reasons: dict[str, list[str]] = defaultdict(list)
    topics = Counter(row.topic for row in screens.values())
    for id, row in screens.items():
        if row.findings:
            reasons[id].append("operational_issue")
        if topics[row.topic] <= 2:
            reasons[id].append("rare_topic")
        if row.secondary_topics:
            reasons[id].append("multi_topic")
    for cluster in geometry["clusters"]:
        for id in cluster["representatives"]:
            reasons[id].append("representative")
        for id in cluster["boundary_ids"]:
            reasons[id].append("cluster_boundary")
    assignments = sorted(
        geometry["assignments"], key=lambda r: r.get("neighbor_distance") or 0, reverse=True
    )
    for row in assignments[: max(1, limit // 4)]:
        reasons[row["id"]].append("semantic_novelty")
    for record in random.Random(seed).sample(records, min(len(records), max(1, limit // 4))):
        reasons[record.id].append("random_audit")
    if limit >= len(records):
        for record in records:
            reasons[record.id].append("full_coverage")
    buckets = [
        "operational_issue",
        "rare_topic",
        "multi_topic",
        "semantic_novelty",
        "cluster_boundary",
        "representative",
        "random_audit",
        "full_coverage",
    ]
    queues = ([id for id, rs in reasons.items() if reason in rs] for reason in buckets)
    ordered = (id for row in zip_longest(*queues) for id in row if id is not None)
    selected = islice(dict.fromkeys(ordered), limit)
    return [{"id": id, "reasons": reasons[id], "inclusion_probability": None} for id in selected]


async def discover(
    ctx: AnalysisContext, records: list[DiscoveryRecord], config: DiscoveryConfig
) -> JsonRecord:
    if not records or len({r.id for r in records}) != len(records):
        raise ValueError("Discovery requires nonempty, uniquely identified records")
    check_citations([], chain.from_iterable(r.sources for r in records), unique=False)
    save_json(ctx.output / "records.json", [record.model_dump(mode="json") for record in records])
    geometry = await map_records(
        ctx, records, embedding=config.embedding, min_cluster_size=config.min_cluster_size
    )
    screens: dict[str, ScreenedRecord] = {}
    errors: list[JsonRecord] = []
    by_id = {record.id: record for record in records}
    if ctx.model:
        semaphore = asyncio.Semaphore(3)

        async def screen_batch(batch: list[DiscoveryRecord]) -> None:
            expected = {r.id: r for r in batch}
            output_schema = cast(
                type[ScreenBatch],
                create_model(
                    "DiscoveryBatch" + str(len(batch)),
                    __base__=ScreenBatch,
                    records=(
                        list[ScreenedRecord],
                        Field(min_length=len(batch), max_length=len(batch)),
                    ),
                ),
            )

            def check(result: ScreenBatch, expected: dict[str, DiscoveryRecord] = expected) -> None:
                if len(result.records) != len(expected) or {r.id for r in result.records} != set(
                    expected
                ):
                    missing = set(expected) - {r.id for r in result.records}
                    extra = {r.id for r in result.records} - set(expected)
                    raise ValueError(
                        f"Return ONE complete batch array. Missing IDs: {sorted(missing)}; unexpected: {sorted(extra)}"
                    )

            try:
                async with semaphore:
                    output = await ctx.ask(
                        "discovery-screen",
                        {"records": [r.model_dump() for r in batch]},
                        output_schema,
                        text("prompts/discovery-screen.md"),
                        validate=check,
                        repair=True,
                    )
                for row in output.records:
                    original = expected[row.id]
                    try:
                        row.check(original)
                        screens[row.id] = row
                    except ValueError as validation_error:

                        def check_one(
                            revised: ScreenedRecord, original: DiscoveryRecord = original
                        ) -> None:
                            revised.check(original)

                        try:
                            async with semaphore:
                                revised = await ctx.ask(
                                    "repair-discovery-record",
                                    {
                                        "record": original.model_dump(),
                                        "invalid_output": row.model_dump(),
                                        "validation_error": str(validation_error),
                                    },
                                    ScreenedRecord,
                                    text("prompts/discovery-screen.md")
                                    + " Re-extract this ONE record. The previous output failed validation; don't preserve unsupported claims. Return one ScreenedRecord.",
                                    validate=check_one,
                                    repair=True,
                                )
                            screens[row.id] = revised
                            ctx.event(
                                {"stage": "record-repair", "id": row.id, "status": "completed"}
                            )
                        except Exception as repair_error:
                            errors.append(
                                {
                                    "id": row.id,
                                    "stage": "record-validation",
                                    "error": str(repair_error),
                                }
                            )
                ctx.event(
                    {"stage": "discovery-coverage", "screened": len(screens), "total": len(records)}
                )
                print(f"  discovery: {len(screens)}/{len(records)} screened", flush=True)
            except Exception as error:
                errors.extend(
                    {"id": r.id, "stage": "screen", "error": f"{type(error).__name__}: {error}"}
                    for r in batch
                )
                if isinstance(error, BudgetExceeded):
                    return

        await asyncio.gather(
            *(
                screen_batch(records[start : start + config.batch_size])
                for start in range(0, len(records), config.batch_size)
            )
        )
        screens = {id: screens[id] for id in by_id if id in screens}
    taxonomy = TaxonomyDraft(intents=[])
    if screens:
        from dwelly_bot.analysis.taxonomy import build_taxonomy

        try:
            taxonomy = await build_taxonomy(
                ctx,
                screens,
                kinds=sorted({record.kind for record in records}),
                label_limit=config.taxonomy_labels,
            )
        except Exception as error:
            errors.append({"stage": "taxonomy", "error": str(error)})
    selection = select_review(
        records, screens, geometry, limit=config.deep_sample, seed=config.seed
    )
    deep: dict[str, JsonRecord] = {}
    if ctx.model:
        from dwelly_bot.analysis.llm import extract

        stage = asyncio.Semaphore(3)

        async def deep_extract(record: DiscoveryRecord) -> None:
            try:
                async with stage:
                    deep[record.id] = (
                        await extract(ctx, record.sources, source_kind=record.kind)
                    ).model_dump(mode="json")
            except Exception as error:
                errors.append({"id": record.id, "stage": "deep-extraction", "error": str(error)})

        await asyncio.gather(*(deep_extract(by_id[item["id"]]) for item in selection))
        deep = {item["id"]: deep[item["id"]] for item in selection if item["id"] in deep}
    conflicts = ConflictBatch(conflicts=[])
    pairs = geometry["pairs"][: config.conflict_pairs]
    if ctx.model and pairs:
        stage = asyncio.Semaphore(3)

        async def compare(chunk: list[JsonRecord]) -> None:
            pair_records = [by_id[id] for id in dict.fromkeys(id for p in chunk for id in p["ids"])]

            def check_conflicts(result: ConflictBatch) -> None:
                allowed = {frozenset(pair["ids"]) for pair in chunk}
                for conflict in result.conflicts:
                    conflict.check(pair_records)
                    if (
                        conflict.status != "internal_inconsistency"
                        and frozenset(conflict.record_ids) not in allowed
                    ):
                        raise ValueError("Only supplied neighbor pairs may be compared")

            try:
                async with stage:
                    found = await ctx.ask(
                        "cross-record-conflicts",
                        {"pairs": chunk, "records": [r.model_dump() for r in pair_records]},
                        ConflictBatch,
                        text("prompts/cross-record-conflicts.md"),
                        validate=check_conflicts,
                        repair=True,
                    )
                conflicts.conflicts.extend(found.conflicts)
            except Exception as error:
                errors.append({"stage": "conflicts", "error": str(error)})

        # Small pair chunks keep each comparison within one request's token limit.
        await asyncio.gather(*(compare(pairs[i : i + 4]) for i in range(0, len(pairs), 4)))
    audit_ids = [r.id for r in screens.values() if not r.findings]
    audit_ids = sorted(
        random.Random(config.seed).sample(audit_ids, min(config.audit_sample, len(audit_ids)))
    )
    flagged = [r.id for r in screens.values() if r.findings]
    flagged_ids = sorted(
        random.Random(config.seed + 1).sample(
            flagged, min(config.flagged_audit, config.audit_sample, len(flagged))
        )
    )
    audit_ids = list(dict.fromkeys(audit_ids + flagged_ids))
    audits = AuditBatch(records=[])
    if ctx.model and audit_ids:
        stage = asyncio.Semaphore(3)

        async def audit(chunk: list[str]) -> None:
            def check_audit(result: AuditBatch) -> None:
                if {r.id for r in result.records} != set(chunk) or len(result.records) != len(
                    chunk
                ):
                    raise ValueError("Audit must cover exactly its assigned IDs")
                for row in result.records:
                    check_citations(
                        row.evidence + (row.issue.evidence if row.issue else []),
                        by_id[row.id].sources,
                    )
                    if (
                        by_id[row.id].kind != "conversation"
                        and row.issue
                        and row.issue.scope == "observed_case"
                    ):
                        raise ValueError(
                            "Audit inferred an observed customer from policy/task text"
                        )

            try:
                async with stage:
                    found = await ctx.ask(
                        "unflagged-audit",
                        {
                            "records": [by_id[id].model_dump() for id in chunk],
                            "extractions": [screens[id].model_dump() for id in chunk],
                        },
                        AuditBatch,
                        text("prompts/unflagged-audit.md"),
                        validate=check_audit,
                        repair=True,
                    )
                audits.records.extend(found.records)
            except Exception as error:
                errors.append({"stage": "audit", "error": str(error)})

        await asyncio.gather(
            *(
                audit(audit_ids[i : i + config.batch_size])
                for i in range(0, len(audit_ids), config.batch_size)
            )
        )
        order = {id: index for index, id in enumerate(audit_ids)}
        audits.records.sort(key=lambda row: order[row.id])
    patterns = PatternBatch(patterns=[])
    groups: dict[str, list[DiscoveryRecord]] = defaultdict(list)
    for id, row in screens.items():
        if by_id[id].kind == "conversation":
            for intent in taxonomy.intents:
                if set([row.topic, *row.secondary_topics]).intersection(intent.aliases):
                    groups[intent.id].append(by_id[id])
    eligible = {intent: cases for intent, cases in groups.items() if len(cases) >= 2}
    if ctx.model and eligible:

        def check_patterns(output: PatternBatch) -> None:
            for pattern in output.patterns:
                pattern.check(eligible.get(pattern.intent_id, []))

        try:
            patterns = await ctx.ask(
                "observed-procedures",
                {
                    "groups": {
                        intent: [r.model_dump() for r in cases]
                        for intent, cases in eligible.items()
                    }
                },
                PatternBatch,
                text("prompts/observed-procedures.md"),
                validate=check_patterns,
                repair=True,
            )
        except Exception as error:
            errors.append({"stage": "observed-procedures", "error": str(error)})
    procedures: list[JsonRecord] = []
    if ctx.model:
        from dwelly_bot.analysis.llm import draft_procedure

        for intent in taxonomy.intents[:3]:
            policies = [
                source
                for record in records
                if record.kind == "policy"
                and record.id in screens
                and set(
                    [screens[record.id].topic, *screens[record.id].secondary_topics]
                ).intersection(intent.aliases)
                for source in record.sources
            ][:5]
            if not policies:
                continue
            try:
                procedures.append(
                    {
                        "intent_id": intent.id,
                        **(
                            await draft_procedure(
                                ctx,
                                intent.definition,
                                policies,
                                list(ctx.parameters.get("analysis_tools", [])),
                            )
                        ).model_dump(mode="json"),
                    }
                )
            except Exception as error:
                errors.append(
                    {"stage": "procedure-draft", "intent": intent.id, "error": str(error)}
                )
    errors.extend(
        {"stage": "taxonomy-assignments", "error": error} for error in taxonomy.assignment_errors
    )
    result: JsonRecord = {
        "schema_version": 1,
        "eligible_records": len(records),
        "screened_records": len(screens),
        "screens": {id: row.model_dump(mode="json") for id, row in screens.items()},
        "taxonomy": taxonomy.model_dump(mode="json"),
        "geometry": geometry,
        "review_sample": selection,
        "deep_extractions": deep,
        "conflicts": conflicts.model_dump(mode="json"),
        "audits": audits.model_dump(mode="json"),
        "errors": errors,
        "unavailable_customer_history": sum(r.kind != "conversation" for r in records),
        "ground_truth_metrics": None,
        "observed_patterns": patterns.model_dump(mode="json"),
        "procedure_drafts": procedures,
        "observed_pattern_eligible_intents": len(eligible),
        "audit_flagged_ids": flagged_ids,
    }
    for name, value in [
        ("discovery.json", result),
        ("intent_taxonomy.json", result["taxonomy"]),
        ("edge_case_findings.json", result["screens"]),
        (
            "analysis_quality.json",
            {"audits": result["audits"], "errors": errors, "labelled_precision_recall": None},
        ),
    ]:
        save_json(ctx.output / name, value)
    return result
