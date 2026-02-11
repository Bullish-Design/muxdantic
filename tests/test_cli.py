from __future__ import annotations

from pathlib import Path

import pytest

from muxdantic import cli
from muxdantic.errors import MuxdanticSubprocessError
from muxdantic.models import EnsureResult, JobInfo, JobRef, KillResult


def test_main_ensure_calls_ensure_and_prints_json(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    captured: dict[str, object] = {}

    def fake_ensure(req):
        captured["req"] = req
        return EnsureResult(workspace=req.workspace, session_name="dev", created=False)

    monkeypatch.setattr("muxdantic.cli.ensure", fake_ensure)

    rc = cli.main(["ensure", "workspace/.tmuxp.yaml", "-L", "named"])

    assert rc == 0
    req = captured["req"]
    assert req.workspace == Path("workspace/.tmuxp.yaml")
    assert req.server.socket_name == "named"
    out = capsys.readouterr().out
    assert '"session_name": "dev"' in out


def test_main_run_requires_separator(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli.main(["run", "workspace/.tmuxp.yaml", "--tag", "build", "echo", "ok"])

    assert rc == 2
    err = capsys.readouterr().err
    assert "requires '--'" in err


def test_main_run_builds_request(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    captured: dict[str, object] = {}

    def fake_run(req):
        captured["req"] = req
        return JobRef(
            job_id="abc123",
            tag=req.tag,
            ts_utc="20260211T143012Z",
            session_name="dev",
            window_id="@9",
            window_name="job:build:20260211T143012Z:abc123",
            pane_id="%11",
            log_file=req.log_file,
        )

    monkeypatch.setattr("muxdantic.cli.run", fake_run)

    rc = cli.main(
        [
            "run",
            "workspace/.tmuxp.yaml",
            "--tag",
            "Build",
            "--rm",
            "--no-keep-on-fail",
            "--log-file",
            "logs/job.log",
            "--",
            "python",
            "-V",
        ]
    )

    assert rc == 0
    req = captured["req"]
    assert req.rm is True
    assert req.keep is False
    assert req.keep_on_fail is False
    assert req.log_file == Path("logs/job.log")
    assert req.cmd == ["python", "-V"]
    out = capsys.readouterr().out
    assert '"job_id": "abc123"' in out


def test_main_ls_jobs_prints_json_array(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.setattr(
        "muxdantic.cli.list_jobs",
        lambda workspace, server: [
            JobInfo(
                job_id="abc123",
                tag="build",
                ts_utc="20260211T143012Z",
                session_name="dev",
                window_id="@9",
                window_name="job:build:20260211T143012Z:abc123",
                pane_id="%11",
                pane_dead=0,
                pane_dead_status=None,
                pane_dead_time=None,
                state="running",
            )
        ],
    )

    rc = cli.main(["ls-jobs", "workspace/.tmuxp.yaml"])

    assert rc == 0
    out = capsys.readouterr().out.strip()
    assert out.startswith("[")
    assert '"job_id": "abc123"' in out


def test_main_kill_and_subprocess_error_mapping(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("muxdantic.cli.kill", lambda *args, **kwargs: KillResult(killed=["@9"]))
    rc = cli.main(["kill", "workspace/.tmuxp.yaml", "--job-id", "abc123", "-S", "/tmp/tmux.sock"])
    assert rc == 0
    assert '"killed": ["@9"]' in capsys.readouterr().out

    def raise_subprocess(*args, **kwargs):
        raise MuxdanticSubprocessError(program="tmux", args=["list-windows"], returncode=1, stderr="boom")

    monkeypatch.setattr("muxdantic.cli.kill", raise_subprocess)
    rc = cli.main(["kill", "workspace/.tmuxp.yaml", "--all-jobs"])
    assert rc == 1
    assert "tmux failed with exit code 1" in capsys.readouterr().err
