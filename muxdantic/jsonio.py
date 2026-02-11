"""JSON/std stream helpers for CLI adapters."""

from __future__ import annotations

import json
import sys
from typing import Any

from pydantic import BaseModel


def _to_jsonable(obj: Any) -> Any:
    if isinstance(obj, BaseModel):
        return obj.model_dump(mode="json")
    return obj


def print_json(obj: Any) -> None:
    """Write compact JSON to stdout."""
    json.dump(_to_jsonable(obj), sys.stdout)
    sys.stdout.write("\n")


def print_error(msg: str) -> None:
    """Write diagnostic text to stderr."""
    sys.stderr.write(f"{msg}\n")
