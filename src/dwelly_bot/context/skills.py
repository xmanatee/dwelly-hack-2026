"""Bounded access to trusted configured workflow instructions."""

from pathlib import Path
from typing import Any

from dwelly_bot.paths import ROOT
from dwelly_bot.storage import file_hash


class SkillLibrary:
    def __init__(self, paths: list[str]) -> None:
        self.files: dict[str, Path] = {
            f"skill-{i}": (ROOT / path).resolve() for i, path in enumerate(paths)
        }
        for path in self.files.values():
            if not path.is_file() or path.stat().st_size > 50_000_000:
                raise ValueError("Skills must be configured local text files below 50 MB")

    def list_skills(self, offset: int = 0, limit: int = 50) -> dict[str, Any]:
        if offset < 0 or not 1 <= limit <= 100:
            raise ValueError("Use nonnegative offset and limit between 1 and 100")
        return {
            "documents": [
                {
                    "source_id": key,
                    "path": path.name,
                    "bytes": path.stat().st_size,
                    "sha256": file_hash(path),
                }
                for key, path in list(self.files.items())[offset : offset + limit]
            ],
            "total": len(self.files),
            "next_offset": offset + limit if offset + limit < len(self.files) else None,
        }

    def read_skill(self, skill_id: str, offset: int = 0, limit: int = 5000) -> dict[str, Any]:
        if offset < 0 or not 1 <= limit <= 8000:
            raise ValueError("Use nonnegative offset and limit between 1 and 8000")
        text = self.files[skill_id].read_text(encoding="utf-8")
        return {
            "source_id": skill_id,
            "offset": offset,
            "text": text[offset : offset + limit],
            "total_characters": len(text),
            "next_offset": offset + limit if offset + limit < len(text) else None,
            "trusted_workflow": True,
        }
