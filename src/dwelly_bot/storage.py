"""Strict JSON receipts and atomic local publication."""

import gzip
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

from pydantic_core import to_jsonable_python


def load_json(path: Path) -> Any:
    """Read plain or gzip-compressed saved evidence."""
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def json_bytes(value: Any) -> bytes:
    """SDK-compatible JSON values; non-finite numbers and unsupported objects are errors."""
    value = to_jsonable_python(value, by_alias=False, inf_nan_mode="constants")
    return json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":")).encode()


def fingerprint(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()
    ).hexdigest()


def file_hash(path: Path) -> str:
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def write_bytes(path: Path, data: bytes, *, overwrite: bool = False) -> None:
    """Readers see complete files; immutable receipts never replace prior evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        try:
            temporary.write(data)
            temporary.flush()
            os.fsync(temporary.fileno())
            temporary.close()
            if overwrite:
                os.replace(temporary.name, path)
            else:
                os.link(temporary.name, path)
        finally:
            Path(temporary.name).unlink(missing_ok=True)


def save_json(path: Path, value: Any, *, overwrite: bool = False) -> None:
    data = (
        gzip.compress(json_bytes(value), mtime=0)
        if path.suffix == ".gz"
        else (json.dumps(value, ensure_ascii=False, allow_nan=False, indent=2) + "\n").encode()
    )
    write_bytes(path, data, overwrite=overwrite)
