"""Tag and job-window naming helpers."""

from __future__ import annotations

import re

_TAG_ALLOWED = re.compile(r"[^a-zA-Z0-9._-]+")
_WINDOW_RE = re.compile(
    r"^job:(?P<tag>[a-z0-9][a-z0-9._-]*):(?P<ts_utc>\d{8}T\d{6}Z):(?P<job_id>[a-z0-9]+)$"
)


def sanitize_tag(tag: str) -> str:
    """Normalize tags used in job identifiers/window names."""
    normalized = _TAG_ALLOWED.sub("-", tag.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-._")
    if not normalized:
        raise ValueError("tag must contain at least one alphanumeric character")
    return normalized


def build_job_window_name(tag: str, ts_utc: str, job_id: str) -> str:
    """Build a deterministic job window name from normalized parts."""
    return f"job:{sanitize_tag(tag)}:{ts_utc}:{job_id}"


def parse_job_window_name(window_name: str) -> tuple[str, str, str]:
    """Parse ``job:<tag>:<utc_ts>:<job_id>`` names."""
    match = _WINDOW_RE.match(window_name)
    if not match:
        raise ValueError(f"Invalid job window name: {window_name!r}")
    return match.group("tag"), match.group("ts_utc"), match.group("job_id")
