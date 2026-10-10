"""Read shipped resources through Python's package API, including installed wheels."""

from importlib.resources import files
from pathlib import PurePosixPath


def text(name: str, *, package: str = "dwelly_bot") -> str:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Use a resource path inside the package")
    return files(package).joinpath(name).read_text(encoding="utf-8")
