"""Ensure a tmux session exists for a tmuxp workspace."""

from __future__ import annotations

from muxdantic.locking import session_lock
from muxdantic.models import EnsureRequest, EnsureResult
from muxdantic.tmux import has_session, tmuxp
from muxdantic.workspace import extract_session_name, load_tmuxp_config, resolve_workspace


def ensure(req: EnsureRequest) -> EnsureResult:
    workspace = resolve_workspace(req.workspace)
    cfg = load_tmuxp_config(workspace)
    session_name = extract_session_name(cfg)

    created = False
    with session_lock(req.server, session_name):
        if not has_session(session_name, req.server):
            tmuxp(["load", "-d", "--yes", str(workspace)], req.server)
            created = True

    return EnsureResult(workspace=workspace, session_name=session_name, created=created)
