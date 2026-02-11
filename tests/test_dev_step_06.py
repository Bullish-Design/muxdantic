from __future__ import annotations

from pathlib import Path

import pytest

from muxdantic.logging import attach_pipe_pane, build_sink_command, resolve_log_file
from muxdantic.models import RunRequest, TmuxServerArgs


def test_dev_step_06_logging_contract(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    req_dir = RunRequest(workspace=tmp_path / ".tmuxp.yaml", tag="Build", cmd=["echo", "ok"], log_dir=tmp_path / "logs")
    assert resolve_log_file(req_dir, "job123") == tmp_path / "logs" / "job123.jsonl"

    req_file = RunRequest(
        workspace=tmp_path / ".tmuxp.yaml",
        tag="Build",
        cmd=["echo", "ok"],
        log_file=tmp_path / "custom" / "run.jsonl",
    )
    assert resolve_log_file(req_file, "job123") == tmp_path / "custom" / "run.jsonl"

    req_none = RunRequest(workspace=tmp_path / ".tmuxp.yaml", tag="Build", cmd=["echo", "ok"])
    assert resolve_log_file(req_none, "job123") is None

    called: dict[str, object] = {}

    monkeypatch.setattr(
        "muxdantic.logging.pipe_pane",
        lambda pane_id, cmd, server: called.update({"pane_id": pane_id, "cmd": cmd, "server": server}),
    )

    server = TmuxServerArgs(socket_name="mx")
    target_file = tmp_path / "logs" / "job123.jsonl"
    attach_pipe_pane(server, "%7", "job123", target_file)

    assert called["pane_id"] == "%7"
    assert called["cmd"] == build_sink_command("job123", target_file)
    assert called["server"] == server
