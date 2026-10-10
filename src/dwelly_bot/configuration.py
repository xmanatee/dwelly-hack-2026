"""Read trusted TOML/JSON run configuration through one validated schema."""

import json
import tomllib
from pathlib import Path
from typing import Any

from dwelly_bot.contracts import RunConfig


def read_settings(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    value = tomllib.loads(text) if path.suffix == ".toml" else json.loads(text)
    if not isinstance(value, dict):
        raise ValueError("Run configuration must be a mapping")
    return value


def read_config(path: Path) -> RunConfig:
    return RunConfig.model_validate(read_settings(path))
