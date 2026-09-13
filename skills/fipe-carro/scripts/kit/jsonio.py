"""Atomic JSON persistence: a failed write never corrupts the previous state."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path


def load_json(path: str | Path, default: object) -> object:
    """The parsed file, or `default` when it does not exist. A corrupt file raises."""
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        return default


def save_json_atomic(path: str | Path, payload: object) -> None:
    """Write JSON whole: temp file in the same directory, fsync, then rename."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(dir=target.parent, prefix=f".{target.name}.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
    except BaseException:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise
