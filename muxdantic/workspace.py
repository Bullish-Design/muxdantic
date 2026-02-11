"""Workspace resolution and tmuxp config parsing helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from muxdantic.errors import MuxdanticUsageError

try:
    import yaml  # type: ignore
except ModuleNotFoundError:  # pragma: no cover - exercised in minimal environments
    yaml = None

_WORKSPACE_FILENAMES = (".tmuxp.yaml", ".tmuxp.yml", ".tmuxp.json")


def _workspace_candidates(directory: Path) -> list[Path]:
    return [directory / filename for filename in _WORKSPACE_FILENAMES]


def _format_expected_filenames() -> str:
    return ", ".join(_WORKSPACE_FILENAMES)


def resolve_workspace(path: Path) -> Path:
    """Resolve a workspace path from a config file path or a directory."""

    target = path.expanduser()

    if target.is_file():
        if target.name not in _WORKSPACE_FILENAMES:
            raise MuxdanticUsageError(
                f"Workspace file must be one of {_format_expected_filenames()}, got: {target}"
            )
        return target

    if target.is_dir():
        matches = [candidate for candidate in _workspace_candidates(target) if candidate.is_file()]
        if not matches:
            raise MuxdanticUsageError(
                f"No workspace file found in {target}. Expected one of: {_format_expected_filenames()}"
            )
        if len(matches) > 1:
            listed = ", ".join(str(match) for match in matches)
            raise MuxdanticUsageError(
                f"Multiple workspace files found in {target}; expected exactly one. Found: {listed}"
            )
        return matches[0]

    raise MuxdanticUsageError(f"Workspace path does not exist: {target}")


def _fallback_yaml_load(raw: str) -> dict[str, Any]:
    """Minimal YAML mapping parser for constrained test environments.

    Supports simple top-level `key: value` pairs and empty lists (`[]`).
    """

    parsed: dict[str, Any] = {}
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in stripped:
            raise MuxdanticUsageError("Invalid YAML line (expected key:value)")
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        if value == "[]":
            parsed[key] = []
        elif value in {"{}"}:
            parsed[key] = {}
        elif value.startswith(("'", '"')) and value.endswith(("'", '"')):
            parsed[key] = value[1:-1]
        elif value == "":
            parsed[key] = ""
        else:
            parsed[key] = value
    return parsed


def load_tmuxp_config(path: Path) -> dict[str, Any]:
    """Load tmuxp config as a dictionary from YAML or JSON."""

    workspace = resolve_workspace(path)

    try:
        raw = workspace.read_text(encoding="utf-8")
    except OSError as exc:
        raise MuxdanticUsageError(f"Unable to read workspace file {workspace}: {exc}") from exc

    try:
        if workspace.suffix == ".json":
            loaded = json.loads(raw)
        elif yaml is not None:
            loaded = yaml.safe_load(raw)
        else:
            loaded = _fallback_yaml_load(raw)
    except Exception as exc:  # noqa: BLE001
        raise MuxdanticUsageError(f"Invalid workspace config format in {workspace}: {exc}") from exc

    if not isinstance(loaded, dict):
        raise MuxdanticUsageError(f"Workspace config must be a mapping object in {workspace}")

    return loaded


def extract_session_name(cfg: dict[str, Any]) -> str:
    """Extract session name from tmuxp config dict."""

    session = cfg.get("session_name") or cfg.get("session")
    if not isinstance(session, str) or not session.strip():
        raise MuxdanticUsageError("Workspace config missing required 'session_name'")
    return session.strip()
