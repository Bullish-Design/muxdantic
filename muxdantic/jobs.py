"""Job operations: run, list, and kill tmux job windows."""

from __future__ import annotations

import shlex
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from muxdantic.ensure import ensure
from muxdantic.errors import MuxdanticUsageError
from muxdantic.models import EnsureRequest, JobInfo, JobRef, KillResult, RunRequest, TmuxServerArgs
from muxdantic.tags import build_job_window_name, parse_job_window_name, sanitize_tag
from muxdantic.tmux import kill_window, list_panes, list_windows, new_window, send_keys, set_window_option
from muxdantic.workspace import extract_session_name, load_tmuxp_config, resolve_workspace


def _generate_job_id() -> str:
    return uuid4().hex[:12]


def _now_utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _remain_on_exit_value(req: RunRequest) -> str:
    if req.keep:
        return "on"
    if req.rm:
        return "off"
    if not req.keep_on_fail:
        return "off"
    return "failed"


def run(req: RunRequest) -> JobRef:
    ensured = ensure(EnsureRequest(workspace=req.workspace, server=req.server))

    job_id = _generate_job_id()
    ts_utc = _now_utc_ts()
    window_name = build_job_window_name(req.tag, ts_utc, job_id)

    window_id, resolved_window_name, pane_id = new_window(ensured.session_name, window_name, req.server)

    set_window_option(window_id, "remain-on-exit", _remain_on_exit_value(req), req.server)

    from muxdantic import logging as mux_logging

    resolve_log_file = getattr(mux_logging, "resolve_log_file", None)
    attach_pipe_pane = getattr(mux_logging, "attach_pipe_pane", None)

    log_file: Path | None
    if callable(resolve_log_file):
        log_file = resolve_log_file(req, job_id)
    elif req.log_file is not None:
        log_file = req.log_file
    elif req.log_dir is not None:
        log_file = req.log_dir / f"{job_id}.log"
    else:
        log_file = None

    if callable(attach_pipe_pane):
        attach_pipe_pane(req.server, pane_id, job_id, log_file)

    send_keys(pane_id, f"exec {shlex.join(req.cmd)}", req.server)

    return JobRef(
        job_id=job_id,
        tag=req.tag,
        ts_utc=ts_utc,
        session_name=ensured.session_name,
        window_id=window_id,
        window_name=resolved_window_name,
        pane_id=pane_id,
        log_file=log_file,
    )


def list_jobs(workspace: Path, server: TmuxServerArgs) -> list[JobInfo]:
    resolved_workspace = resolve_workspace(workspace)
    cfg = load_tmuxp_config(resolved_workspace)
    session_name = extract_session_name(cfg)

    jobs: list[JobInfo] = []
    for window_id, window_name in list_windows(session_name, server):
        if not window_name.startswith("job:"):
            continue
        try:
            tag, ts_utc, job_id = parse_job_window_name(window_name)
        except ValueError:
            continue

        panes = list_panes(window_id, server)
        if not panes:
            continue

        pane_id, pane_dead, pane_dead_status, pane_dead_time = panes[0]
        state = "running" if pane_dead == 0 else "exited"
        jobs.append(
            JobInfo(
                job_id=job_id,
                tag=tag,
                ts_utc=ts_utc,
                session_name=session_name,
                window_id=window_id,
                window_name=window_name,
                pane_id=pane_id,
                pane_dead=pane_dead,
                pane_dead_status=pane_dead_status,
                pane_dead_time=pane_dead_time,
                state=state,
            )
        )

    return jobs


def kill(
    workspace: Path,
    server: TmuxServerArgs,
    *,
    job_id: str | None,
    tag: str | None,
    all_jobs: bool,
) -> KillResult:
    jobs = list_jobs(workspace, server)

    selected: list[JobInfo]
    if job_id:
        selected = [job for job in jobs if job.job_id == job_id]
    elif tag:
        selected = [job for job in jobs if job.tag == sanitize_tag(tag)]
    elif all_jobs:
        selected = jobs
    else:
        raise MuxdanticUsageError("Select one of: job_id, tag, or all_jobs")

    killed: list[str] = []
    for job in selected:
        kill_window(job.window_id, server)
        killed.append(job.window_id)

    return KillResult(killed=killed)
