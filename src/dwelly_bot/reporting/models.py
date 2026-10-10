"""Ordered presentation blocks shared by source analysis and case reporting."""

from __future__ import annotations

import json
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from dwelly_bot.contracts import JsonRecord
from dwelly_bot.evaluation.checks import pointer

type BlockKind = Literal["text", "metrics", "table", "chart", "records", "flow"]


class Block(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    kind: BlockKind
    title: str
    note: str = ""
    caption: str = ""
    width: Literal["half", "full"] = "full"
    collapsed: bool = False
    section: str = ""
    data: JsonRecord = Field(default_factory=dict)


class Report(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    schema_version: Literal[1] = 1
    title: str
    subtitle: str = ""
    blocks: list[Block] = Field(default_factory=list)
    receipt: JsonRecord = Field(default_factory=dict)

    def _add(self, kind: BlockKind, title: str, data: JsonRecord, **options: Any) -> None:
        self.blocks.append(Block(kind=kind, title=title, data=data, **options))

    def text(self, title: str, text: str, *, collapsed: bool = True) -> None:
        self._add("text", title, {"text": text}, collapsed=collapsed)

    def metrics(self, values: JsonRecord, *, title: str = "Overview") -> None:
        self._add("metrics", title, values)

    def table(
        self,
        title: str,
        rows: list[JsonRecord],
        *,
        note: str = "",
        total: int | None = None,
        caption: str = "",
        collapsed: bool = False,
    ) -> None:
        self._add(
            "table",
            title,
            {"rows": rows, "total": total},
            note=note,
            caption=caption,
            collapsed=collapsed,
        )

    def chart(
        self,
        title: str,
        figure: Any,
        *,
        note: str = "",
        caption: str = "",
        width: Literal["half", "full"] = "half",
        details: dict[str, JsonRecord] | None = None,
    ) -> None:
        self._add(
            "chart",
            title,
            {**json.loads(figure.to_json()), "details": details or {}},
            note=note,
            caption=caption,
            width=width,
        )

    def records(
        self,
        title: str,
        rows: list[JsonRecord],
        *,
        note: str = "",
        caption: str = "",
        collapsed: bool = False,
    ) -> None:
        self._add("records", title, {"rows": rows}, note=note, caption=caption, collapsed=collapsed)

    def flow(self, title: str, steps: list[JsonRecord], *, note: str = "") -> None:
        self._add("flow", title, {"steps": steps}, note=note)


class ReportProfile(BaseModel):
    """Display-only customization; paths inspect captures and cannot change verdicts."""

    model_config = ConfigDict(extra="forbid")
    title: str | None = None
    fields: dict[str, str] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_fields(self) -> ReportProfile:
        if self.fields.keys() & {
            "Case",
            "Execution",
            "Disposition",
            "Verified outcome",
            "Critical failure",
            "Execution error",
            "Judge status",
            "Verification status",
            "Evaluation error",
        }:
            raise ValueError(
                "Standard outcome labels are reserved; choose a distinct context label"
            )
        for label, path in self.fields.items():
            if not label.strip():
                raise ValueError("Fields require nonempty labels")
            pointer({}, path)
        return self
