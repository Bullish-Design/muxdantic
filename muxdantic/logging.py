"""Logging helpers for JSONL pane capture via tmux pipe-pane."""

from __future__ import annotations

import shlex
import sys
from pathlib import Path

from muxdantic.models import RunRequest, TmuxServerArgs
from muxdantic.tmux import pipe_pane


def resolve_log_file(req: RunRequest, job_id: str) -> Path | None:
    """Resolve the effective JSONL log path for a run request."""
    if req.log_file is not None:
        return req.log_file
    if req.log_dir is not None:
        return req.log_dir / f"{job_id}.jsonl"
    return None


def build_sink_command(job_id: str, path: Path) -> str:
    """Build a shell-safe command for the JSONL logging sink."""
    python_exe = shlex.quote(sys.executable)
    quoted_job_id = shlex.quote(job_id)
    quoted_path = shlex.quote(str(path))
    return (
        f"{python_exe} -m muxdantic.logging_sink "
        f"--job-id {quoted_job_id} --file {quoted_path}"
    )


def pipe_pane_to_jsonl(server: TmuxServerArgs, pane_id: str, job_id: str, path: Path) -> None:
    """Attach tmux pipe-pane for JSONL capture."""
    cmd = build_sink_command(job_id, path)
    pipe_pane(pane_id, cmd, server)


def attach_pipe_pane(server: TmuxServerArgs, pane_id: str, job_id: str, log_file: Path | None) -> None:
    """Compatibility wrapper used by jobs.run to conditionally attach logging."""
    if log_file is None:
        return
    pipe_pane_to_jsonl(server, pane_id, job_id, log_file)
