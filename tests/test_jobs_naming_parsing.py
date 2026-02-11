from __future__ import annotations

from pathlib import Path

import pytest

from muxdantic.jobs import list_jobs
from muxdantic.models import TmuxServerArgs
from muxdantic.tags import build_job_window_name, parse_job_window_name


def test_job_window_name_roundtrip() -> None:
    window_name = build_job_window_name("CI Build", "20260211T143012Z", "abc123")
    assert window_name == "job:ci-build:20260211T143012Z:abc123"
    assert parse_job_window_name(window_name) == ("ci-build", "20260211T143012Z", "abc123")


def test_list_jobs_parses_tmux_tabular_data(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setattr("muxdantic.jobs.resolve_workspace", lambda p: tmp_path / ".tmuxp.yaml")
    monkeypatch.setattr("muxdantic.jobs.load_tmuxp_config", lambda p: {"session_name": "dev"})
    monkeypatch.setattr("muxdantic.jobs.extract_session_name", lambda cfg: "dev")
    monkeypatch.setattr(
        "muxdantic.jobs.list_windows",
        lambda session, server: [
            ("@1", "editor"),
            ("@2", "job:build:20260211T143012Z:abc123"),
            ("@3", "job:broken-name"),
        ],
    )
    monkeypatch.setattr(
        "muxdantic.jobs.list_panes",
        lambda target, server: [("%9", 1, 2, 1700000000)] if target == "@2" else [("%10", 0, None, None)],
    )

    jobs = list_jobs(tmp_path, TmuxServerArgs())

    assert len(jobs) == 1
    assert jobs[0].model_dump() == {
        "job_id": "abc123",
        "tag": "build",
        "ts_utc": "20260211T143012Z",
        "session_name": "dev",
        "window_id": "@2",
        "window_name": "job:build:20260211T143012Z:abc123",
        "pane_id": "%9",
        "pane_dead": 1,
        "pane_dead_status": 2,
        "pane_dead_time": 1700000000,
        "state": "exited",
    }
