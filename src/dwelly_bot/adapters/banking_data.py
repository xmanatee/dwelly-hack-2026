"""Developer-selected public-case snapshots; never a source of outcome labels.

The organizer supplies completed case folders, not a fixed two-event benchmark.
Attachment availability is a reviewed assertion about a history event, not a file
timestamp or an automatic consequence of mentioning a filename.
"""

from pathlib import Path, PurePosixPath

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AttachmentAvailability(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    path: str
    available_after_event: int = Field(ge=1)
    basis: str = Field(min_length=1)

    @field_validator("path")
    @classmethod
    def attachment_path(cls, value: str) -> str:
        path = PurePosixPath(value)
        if (
            len(path.parts) != 2
            or path.parts[0] != "attachments"
            or path.name in {".", ".."}
            or "\\" in value
            or str(path) != value
        ):
            raise ValueError("Use a case-local attachments/filename path")
        return value


class DecisionProfile(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    name: str = Field(min_length=1)
    default_after_event: int = Field(ge=1)
    after_event: dict[str, int] = Field(default_factory=dict)
    attachments: dict[str, list[AttachmentAvailability]] = Field(default_factory=dict)

    def validate_cases(self, case_numbers: set[str]) -> None:
        unknown = (self.after_event.keys() | self.attachments.keys()) - case_numbers
        if unknown:
            raise ValueError(f"Profile names unknown cases: {sorted(unknown)}")
        if any(type(value) is not int or value < 1 for value in self.after_event.values()):
            raise ValueError("Decision points must be positive event numbers")


def visible_attachments(
    folder: Path, history: str, after_event: int, rules: list[AttachmentAvailability]
) -> dict[str, str]:
    """Return text renderings of explicitly available originals, failing on unsupported media.

    No future filenames, inventory counts or availability declarations enter the
    agent's view. Original bytes remain in the original case folder.
    """
    import re

    events = list(re.finditer(r"^## .* UTC — event (\d+)\s*$", history, re.M))
    seen: set[str] = set()
    documents = {}
    for rule in rules:
        if rule.path in seen:
            raise ValueError(f"Duplicate attachment availability: {rule.path}")
        seen.add(rule.path)
        source = folder / rule.path
        if not source.resolve().is_relative_to(folder.resolve()) or not source.is_file():
            raise ValueError(f"Missing or escaping original attachment: {rule.path}")
        event = rule.available_after_event
        if event > len(events):
            raise ValueError(f"Attachment availability event does not exist: {rule.path}")
        start = events[event - 1].start()
        end = events[event].start() if event < len(events) else len(history)
        if source.name not in history[start:end]:
            raise ValueError(f"Availability evidence does not identify the file: {rule.path}")
        if event > after_event:
            continue
        if source.suffix.lower() not in {".csv", ".txt", ".md"}:
            raise ValueError(
                f"Available attachment {rule.path} needs a supported media reader; "
                "do not silently drop it or move the decision point to hide it"
            )
        documents[rule.path + ".md"] = (
            f"# Source attachment: {rule.path}\n\n"
            f"Available by event {event:03}. This is supplied case evidence, not a live tool result.\n\n"
            + source.read_text(encoding="utf-8")
        )
    inventory = {
        str(path.relative_to(folder))
        for path in (folder / "attachments").rglob("*")
        if path.is_file()
    }
    if inventory != seen:
        raise ValueError("Every original attachment needs an explicit reviewed availability rule")
    return documents
