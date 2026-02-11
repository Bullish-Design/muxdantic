"""File-locking helpers for concurrency-safe session creation."""

from __future__ import annotations

import hashlib
from contextlib import contextmanager
from pathlib import Path

import fcntl

from muxdantic.models import TmuxServerArgs

_LOCK_ROOT = Path("~/.cache/muxdantic/lock").expanduser()


def _server_selector(server: TmuxServerArgs) -> str:
    return f"L={server.socket_name or ''};S={server.socket_path or ''}"


def lock_key(server: TmuxServerArgs, session_name: str) -> str:
    """Build the stable lock key from tmux server selector + session name."""

    return f"{_server_selector(server)};session={session_name}"


def lock_filename(server: TmuxServerArgs, session_name: str) -> str:
    """Return a SHA1 filename derived from the lock key."""

    key = lock_key(server, session_name)
    return hashlib.sha1(key.encode("utf-8")).hexdigest()


def lock_path_for(
    server: TmuxServerArgs,
    session_name: str,
    *,
    lock_root: Path | None = None,
) -> Path:
    """Return the full lock file path for a session/server pair."""

    root = (lock_root or _LOCK_ROOT).expanduser()
    return root / lock_filename(server, session_name)


@contextmanager
def session_lock(
    server: TmuxServerArgs,
    session_name: str,
    *,
    lock_root: Path | None = None,
):
    """Acquire an exclusive advisory lock for the session/server key."""

    path = lock_path_for(server, session_name, lock_root=lock_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield path
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
