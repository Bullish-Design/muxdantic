from __future__ import annotations

import json
from pathlib import Path

import pytest

from muxdantic.errors import MuxdanticUsageError
from muxdantic.workspace import extract_session_name, load_tmuxp_config, resolve_workspace


def test_resolve_workspace_directory_none_found(tmp_path: Path) -> None:
    with pytest.raises(MuxdanticUsageError, match="No workspace file found"):
        resolve_workspace(tmp_path)


def test_resolve_workspace_directory_more_than_one_found(tmp_path: Path) -> None:
    (tmp_path / ".tmuxp.yaml").write_text("session_name: a\n", encoding="utf-8")
    (tmp_path / ".tmuxp.json").write_text('{"session_name": "b"}', encoding="utf-8")

    with pytest.raises(MuxdanticUsageError, match="Multiple workspace files found"):
        resolve_workspace(tmp_path)


def test_resolve_workspace_wrong_file_suffix(tmp_path: Path) -> None:
    bad = tmp_path / "workspace.yaml"
    bad.write_text("session_name: dev\n", encoding="utf-8")

    with pytest.raises(MuxdanticUsageError, match="must be one of"):
        resolve_workspace(bad)


def test_load_tmuxp_config_supports_yaml_and_json(tmp_path: Path) -> None:
    yaml_file = tmp_path / ".tmuxp.yaml"
    yaml_file.write_text("session_name: yaml-dev\nwindows: []\n", encoding="utf-8")

    json_file = tmp_path / ".tmuxp.json"
    json_file.write_text(json.dumps({"session_name": "json-dev", "windows": []}), encoding="utf-8")

    assert load_tmuxp_config(yaml_file)["session_name"] == "yaml-dev"
    assert load_tmuxp_config(json_file)["session_name"] == "json-dev"


def test_extract_session_name_tolerates_session_alias() -> None:
    assert extract_session_name({"session_name": "main"}) == "main"
    assert extract_session_name({"session": "fallback"}) == "fallback"

    with pytest.raises(MuxdanticUsageError, match="session_name"):
        extract_session_name({})
