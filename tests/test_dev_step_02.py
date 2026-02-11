from __future__ import annotations

from pathlib import Path

from muxdantic.workspace import extract_session_name, load_tmuxp_config, resolve_workspace


def test_dev_step_02_workspace_flow(tmp_path: Path) -> None:
    workspace = tmp_path / ".tmuxp.yaml"
    workspace.write_text("session_name: dev-step-02\n", encoding="utf-8")

    resolved = resolve_workspace(tmp_path)
    cfg = load_tmuxp_config(resolved)
    session_name = extract_session_name(cfg)

    assert resolved == workspace
    assert session_name == "dev-step-02"
