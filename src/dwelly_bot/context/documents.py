"""Read-only, line-addressable Markdown evidence inside an explicit document boundary."""

from pathlib import Path
from typing import Any

from pydantic_ai import ModelRetry


class Documents:
    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.files = {str(p.relative_to(self.root)): p for p in sorted(self.root.rglob("*.md"))}
        if not self.files:
            raise ValueError(f"No Markdown documents in {root}")
        if any(not p.resolve().is_relative_to(self.root) for p in self.files.values()):
            raise ValueError("Document symlink escapes the evidence directory")

    def list_documents(self) -> list[dict[str, Any]]:
        """List available evidence documents and their line counts."""
        return [
            {"document": name, "lines": len(path.read_text().splitlines())}
            for name, path in self.files.items()
        ]

    def read_document(self, document: str, start_line: int = 1, limit: int = 100) -> dict[str, Any]:
        """Read numbered lines; follow next_line until all relevant evidence is inspected."""
        if document not in self.files or start_line < 1 or not 1 <= limit <= 200:
            raise ModelRetry(
                "Select a listed document, start_line >= 1 and limit between 1 and 200"
            )
        lines = self.files[document].read_text().splitlines()
        end = min(start_line - 1 + limit, len(lines))
        return {
            "document": document,
            "text": "\n".join(f"{i + 1}: {lines[i]}" for i in range(start_line - 1, end)),
            "total_lines": len(lines),
            "next_line": end + 1 if end < len(lines) else None,
        }

    def search_documents(self, query: str, limit: int = 20, offset: int = 0) -> dict[str, Any]:
        """Find literal text across documents; returns numbered matching lines with pagination."""
        if not query.strip() or not 1 <= limit <= 50 or offset < 0:
            raise ModelRetry("Supply nonempty text, limit 1-50 and offset >= 0")
        hits = [
            {"document": name, "line": i, "text": line}
            for name, path in self.files.items()
            for i, line in enumerate(path.read_text().splitlines(), 1)
            if query.casefold() in line.casefold()
        ]
        end = offset + limit
        return {
            "matches": hits[offset:end],
            "total_matches": len(hits),
            "next_offset": end if end < len(hits) else None,
        }
