from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from muxdantic.errors import MuxdanticSubprocessError, MuxdanticUsageError
from muxdantic.models import EnsureResult, JobInfo, JobRef, KillResult, RunRequest


@pytest.fixture
def cli_module():
    import muxdantic.cli as cli

    return cli


def _invoke_cli(cli_module, argv: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        try:
            result = cli_module.main(argv)
            exit_code = int(result) if isinstance(result, int) else 0
        except SystemExit as exc:
            code = exc.code
            exit_code = int(code) if isinstance(code, int) else 1
    return exit_code, out.getvalue(), err.getvalue()


def test_dev_step_07_ensure_parses_args_and_emits_ensure_result_json(
    cli_module,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    workspace = tmp_path / ".tmuxp.yaml"
    calls: dict[str, object] = {}

    def fake_ensure(req):
        calls["req"] = req
        return EnsureResult(workspace=workspace, session_name="dev", created=True)

    monkeypatch.setattr("muxdantic.ensure.ensure", fake_ensure)
    monkeypatch.setattr(cli_module, "ensure", fake_ensure, raising=False)

    exit_code, stdout, stderr = _invoke_cli(cli_module, ["ensure", str(workspace), "-L", "mx"])

    assert exit_code == 0
    payload = json.loads(stdout)
    EnsureResult.model_validate(payload)
    req = calls["req"]
    assert req.workspace == workspace
    assert req.server.socket_name == "mx"
    assert "Traceback" not in stderr


def test_dev_step_07_run_requires_separator_and_command(cli_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = tmp_path / ".tmuxp.yaml"

    exit_code, stdout, stderr = _invoke_cli(cli_module, ["run", str(workspace), "--tag", "build"])
    assert exit_code == 2
    assert stdout == ""
    assert "Traceback" not in stderr

    calls: dict[str, object] = {}

    def fake_run(req: RunRequest) -> JobRef:
        calls["req"] = req
        return JobRef(
            job_id="abc123",
            tag=req.tag,
            ts_utc="20260211T143012Z",
            session_name="dev",
            window_id="@9",
            window_name="job:build:20260211T143012Z:abc123",
            pane_id="%11",
        )

    monkeypatch.setattr("muxdantic.jobs.run", fake_run)
    monkeypatch.setattr(cli_module, "run", fake_run, raising=False)

    exit_code, stdout, stderr = _invoke_cli(
        cli_module,
        ["run", str(workspace), "--tag", "build", "--", "python", "-V"],
    )

    assert exit_code == 0
    payload = json.loads(stdout)
    JobRef.model_validate(payload)
    req = calls["req"]
    assert req.workspace == workspace
    assert req.tag == "build"
    assert req.cmd == ["python", "-V"]
    assert "Traceback" not in stderr


def test_dev_step_07_ls_jobs_emits_json_array(cli_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = tmp_path / ".tmuxp.yaml"

    def fake_list_jobs(workspace_arg, server_arg):
        assert workspace_arg == workspace
        return [
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
        ]

    monkeypatch.setattr("muxdantic.jobs.list_jobs", fake_list_jobs)
    monkeypatch.setattr(cli_module, "list_jobs", fake_list_jobs, raising=False)

    exit_code, stdout, stderr = _invoke_cli(cli_module, ["ls-jobs", str(workspace)])

    assert exit_code == 0
    payload = json.loads(stdout)
    assert isinstance(payload, list)
    assert len(payload) == 1
    JobInfo.model_validate(payload[0])
    assert "Traceback" not in stderr


def test_dev_step_07_kill_selector_validation_and_json(cli_module, monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = tmp_path / ".tmuxp.yaml"

    exit_code, stdout, stderr = _invoke_cli(
        cli_module,
        ["kill", str(workspace), "--job-id", "abc123", "--tag", "build"],
    )
    assert exit_code == 2
    assert stdout == ""
    assert "Traceback" not in stderr

    def fake_kill(workspace_arg, server_arg, *, job_id, tag, all_jobs):
        assert workspace_arg == workspace
        assert job_id == "abc123"
        assert tag is None
        assert all_jobs is False
        return KillResult(killed=["@9"])

    monkeypatch.setattr("muxdantic.jobs.kill", fake_kill)
    monkeypatch.setattr(cli_module, "kill", fake_kill, raising=False)

    exit_code, stdout, stderr = _invoke_cli(cli_module, ["kill", str(workspace), "--job-id", "abc123"])

    assert exit_code == 0
    payload = json.loads(stdout)
    KillResult.model_validate(payload)
    assert "Traceback" not in stderr


@pytest.mark.parametrize(
    ("exc", "expected_code", "expected_message"),
    [
        (MuxdanticUsageError("bad input"), 2, "bad input"),
        (
            MuxdanticSubprocessError(
                program="tmux",
                args=["list-windows"],
                returncode=1,
                stderr="permission denied",
            ),
            1,
            "tmux failed with exit code 1",
        ),
    ],
)
def test_dev_step_07_exception_mapping_no_traceback(
    cli_module,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    exc: Exception,
    expected_code: int,
    expected_message: str,
) -> None:
    workspace = tmp_path / ".tmuxp.yaml"

    def raising(_req):
        raise exc

    monkeypatch.setattr("muxdantic.ensure.ensure", raising)
    monkeypatch.setattr(cli_module, "ensure", raising, raising=False)

    exit_code, stdout, stderr = _invoke_cli(cli_module, ["ensure", str(workspace)])

    assert exit_code == expected_code
    assert stdout == ""
    assert expected_message in stderr
    assert "Traceback" not in stderr
