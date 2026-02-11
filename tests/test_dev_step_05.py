from __future__ import annotations

from pathlib import Path

import pytest

from muxdantic.jobs import kill, list_jobs, run
from muxdantic.models import JobRef, KillResult, RunRequest, TmuxServerArgs


def test_dev_step_05_end_to_end_contract(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = tmp_path / ".tmuxp.yaml"
    req = RunRequest(workspace=workspace, server=TmuxServerArgs(), tag="Build", cmd=["python", "-V"])

    monkeypatch.setattr(
        "muxdantic.jobs.ensure",
        lambda ensure_req: type("EnsureResult", (), {"session_name": "dev", "workspace": workspace, "created": False})(),
    )
    monkeypatch.setattr("muxdantic.jobs._generate_job_id", lambda: "abc123")
    monkeypatch.setattr("muxdantic.jobs._now_utc_ts", lambda: "20260211T143012Z")

    recorded: dict[str, object] = {}

    monkeypatch.setattr(
        "muxdantic.jobs.new_window",
        lambda session_name, window_name, server: ("@9", window_name, "%11"),
    )
    monkeypatch.setattr(
        "muxdantic.jobs.set_window_option",
        lambda window_id, option, value, server: recorded.update({"remain": (window_id, option, value)}),
    )
    monkeypatch.setattr(
        "muxdantic.jobs.send_keys",
        lambda pane_id, string, server: recorded.update({"send": (pane_id, string)}),
    )

    job_ref = run(req)

    assert isinstance(job_ref, JobRef)
    assert job_ref.window_name == "job:build:20260211T143012Z:abc123"
    assert recorded["remain"] == ("@9", "remain-on-exit", "failed")
    assert recorded["send"] == ("%11", "exec python -V")

    monkeypatch.setattr("muxdantic.jobs.resolve_workspace", lambda p: workspace)
    monkeypatch.setattr("muxdantic.jobs.load_tmuxp_config", lambda p: {"session_name": "dev"})
    monkeypatch.setattr("muxdantic.jobs.extract_session_name", lambda cfg: "dev")
    monkeypatch.setattr(
        "muxdantic.jobs.list_windows",
        lambda session, server: [("@9", "job:build:20260211T143012Z:abc123")],
    )
    monkeypatch.setattr("muxdantic.jobs.list_panes", lambda target, server: [("%11", 0, None, None)])

    jobs = list_jobs(workspace, TmuxServerArgs())
    assert len(jobs) == 1

    monkeypatch.setattr("muxdantic.jobs.kill_window", lambda window_id, server: None)
    result = kill(workspace, TmuxServerArgs(), job_id="abc123", tag=None, all_jobs=False)
    assert isinstance(result, KillResult)
    assert result.killed == ["@9"]
