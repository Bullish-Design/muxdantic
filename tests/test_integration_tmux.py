from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path
from uuid import uuid4

import pytest

from muxdantic.ensure import ensure
from muxdantic.errors import MuxdanticSubprocessError
from muxdantic.jobs import kill, list_jobs, run
from muxdantic.models import EnsureRequest, RunRequest, TmuxServerArgs

pytestmark = pytest.mark.skipif(
    os.environ.get("MUXDANTIC_INTEGRATION") != "1",
    reason="set MUXDANTIC_INTEGRATION=1 to run tmux integration tests",
)


def _require_tmux_tools() -> None:
    if shutil.which("tmux") is None:
        pytest.skip("tmux is not available on PATH")
    if shutil.which("tmuxp") is None:
        pytest.skip("tmuxp is not available on PATH")


def _wait_for(predicate: callable, *, timeout_s: float = 8.0, interval_s: float = 0.25) -> None:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(interval_s)
    raise AssertionError("condition not met before timeout")


def test_tmux_flow_uses_isolated_socket_and_library_api(tmp_path: Path) -> None:
    _require_tmux_tools()

    socket_name = f"muxdantic-test-{uuid4().hex[:12]}"
    session_name = f"muxdantic-session-{uuid4().hex[:8]}"
    server = TmuxServerArgs(socket_name=socket_name)

    workspace = tmp_path / ".tmuxp.json"
    workspace.write_text(
        json.dumps(
            {
                "session_name": session_name,
                "windows": [{"window_name": "base"}],
            }
        ),
        encoding="utf-8",
    )

    try:
        ensured = ensure(EnsureRequest(workspace=workspace, server=server))
        assert ensured.session_name == session_name

        default_has_session = subprocess.run(
            ["tmux", "has-session", "-t", session_name],
            capture_output=True,
            text=True,
            check=False,
        )
        assert default_has_session.returncode != 0

        success_ref = run(
            RunRequest(
                workspace=workspace,
                server=server,
                tag="integration-success",
                cmd=["sh", "-lc", "exit 0"],
            )
        )
        failure_ref = run(
            RunRequest(
                workspace=workspace,
                server=server,
                tag="integration-failure",
                cmd=["sh", "-lc", "exit 9"],
            )
        )

        def _failed_job_exited_and_success_disappeared() -> bool:
            jobs = list_jobs(workspace, server)
            by_id = {job.job_id: job for job in jobs}
            failed = by_id.get(failure_ref.job_id)
            success = by_id.get(success_ref.job_id)
            return failed is not None and failed.state == "exited" and success is None

        _wait_for(_failed_job_exited_and_success_disappeared)

        jobs = list_jobs(workspace, server)
        by_id = {job.job_id: job for job in jobs}
        assert success_ref.job_id not in by_id
        assert failure_ref.job_id in by_id
        assert by_id[failure_ref.job_id].state == "exited"

        killed = kill(workspace, server, job_id=None, tag=None, all_jobs=True)
        assert failure_ref.window_id in killed.killed
    finally:
        # Cleanup is best-effort because setup can fail before the isolated server exists.
        try:
            kill(workspace, server, job_id=None, tag=None, all_jobs=True)
        except MuxdanticSubprocessError:
            pass
        subprocess.run(
            ["tmux", "-L", socket_name, "kill-session", "-t", session_name],
            capture_output=True,
            text=True,
            check=False,
        )
