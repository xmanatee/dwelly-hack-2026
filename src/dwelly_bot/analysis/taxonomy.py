"""Draft definitions and alias assignment are separate bounded model tasks."""

import asyncio
import random
from collections import Counter
from typing import Any, Literal, cast

from pydantic import BaseModel, Field, create_model

from dwelly_bot.analysis.discovery_types import ScreenedRecord, TaxonomyDraft
from dwelly_bot.analysis.session import AnalysisContext
from dwelly_bot.resources import text


class AliasAssignment(BaseModel):
    alias_id: str
    intent_ids: list[str] = Field(max_length=3)
    status: Literal["matched", "unmapped", "uncertain"]


class AssignmentBatch(BaseModel):
    assignments: list[AliasAssignment]


async def build_taxonomy(
    ctx: AnalysisContext, screens: dict[str, ScreenedRecord], *, kinds: list[str]
) -> TaxonomyDraft:
    if not screens:
        raise ValueError("Taxonomy requires saved screened records")
    labels = Counter(
        label
        for row in screens.values()
        for label in dict.fromkeys([row.topic, *row.secondary_topics])
    )
    names = {f"L{i:04d}": label for i, label in enumerate(sorted(labels))}
    inputs: list[dict[str, Any]] = [
        {
            "alias_id": id,
            "label": label,
            "count": labels[label],
            "examples": [
                {"id": row.id, "domain": row.domain, "summary": row.summary[:160]}
                for row in screens.values()
                if label in [row.topic, *row.secondary_topics]
            ][:1],
        }
        for id, label in names.items()
    ]

    def check_draft(draft: TaxonomyDraft) -> None:
        ids = [intent.id for intent in draft.intents]
        if not ids or len(ids) > 20 or len(ids) != len(set(ids)):
            raise ValueError("Return unique canonical IDs")
        for intent in draft.intents:
            if set(intent.aliases) - {row["alias_id"] for row in proposal} or set(
                intent.representative_ids + intent.counterexample_ids
            ) - {example["id"] for row in proposal for example in row["examples"]}:
                raise ValueError("Only supplied alias/example IDs are allowed")

    head = sorted(inputs, key=lambda row: row["count"], reverse=True)[:40]
    tail = [row for row in inputs if row not in head]
    proposal = head + random.Random(0).sample(tail, min(20, len(tail)))
    draft = await ctx.ask(
        "taxonomy-definitions",
        {"candidate_labels": proposal, "all_alias_count": len(inputs), "source_kinds": kinds},
        TaxonomyDraft,
        text("prompts/intent-taxonomy.md"),
        validate=check_draft,
        repair=True,
    )
    definitions = {intent.id: intent for intent in draft.intents}
    mappings: dict[str, list[str]] = {}
    semaphore = asyncio.Semaphore(3)

    async def assign(batch: list[dict[str, Any]]) -> None:
        expected = {row["alias_id"] for row in batch}
        schema = cast(
            type[AssignmentBatch],
            create_model(
                "AssignAliases" + str(len(batch)),
                __base__=AssignmentBatch,
                assignments=(
                    list[AliasAssignment],
                    Field(min_length=len(batch), max_length=len(batch)),
                ),
            ),
        )

        def check(result: AssignmentBatch) -> None:
            if (
                len(result.assignments) != len(expected)
                or {a.alias_id for a in result.assignments} != expected
            ):
                raise ValueError("Return every supplied alias_id exactly once")
            if any(
                (a.status == "matched" and not a.intent_ids)
                or (a.status == "unmapped" and a.intent_ids)
                or len(a.intent_ids) != len(set(a.intent_ids))
                for a in result.assignments
            ):
                raise ValueError("Matched aliases need unique IDs; unmapped aliases need no IDs")
            if any(set(a.intent_ids) - set(definitions) for a in result.assignments):
                raise ValueError("Only listed canonical intent IDs are allowed")

        async with semaphore:
            result = await ctx.ask(
                "taxonomy-assignments",
                {
                    "aliases": batch,
                    "definitions": [
                        i.model_dump(
                            exclude={"aliases", "representative_ids", "counterexample_ids"}
                        )
                        for i in draft.intents
                    ],
                },
                schema,
                text("prompts/taxonomy-assignments.md"),
                validate=check,
                repair=True,
            )
        mappings.update(
            {a.alias_id: a.intent_ids if a.status == "matched" else [] for a in result.assignments}
        )

    outcomes = await asyncio.gather(
        *(assign(inputs[start : start + 16]) for start in range(0, len(inputs), 16)),
        return_exceptions=True,
    )
    for error in outcomes:
        if isinstance(error, BaseException):
            ctx.event({"stage": "taxonomy-assignment-error", "error": str(error)})
    return draft.model_copy(
        update={
            "assignment_errors": [str(error) for error in outcomes if isinstance(error, Exception)],
            "unmapped_aliases": [names[id] for id in names if not mappings.get(id)],
            "intents": [
                intent.model_copy(
                    update={
                        "aliases": [names[id] for id in names if intent.id in mappings.get(id, [])]
                    }
                )
                for intent in draft.intents
            ],
        }
    )
