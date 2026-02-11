from __future__ import annotations

import re
from pathlib import Path

from muxdantic.locking import lock_filename, lock_key, lock_path_for, session_lock
from muxdantic.models import TmuxServerArgs


def test_lock_key_and_filename_are_deterministic() -> None:
    server = TmuxServerArgs(socket_name="dev", socket_path="/tmp/tmux.sock")

    assert lock_key(server, "api") == lock_key(server, "api")
    assert lock_filename(server, "api") == lock_filename(server, "api")
    assert lock_filename(server, "api") != lock_filename(server, "worker")


def test_lock_path_is_scoped_to_cache_and_uses_sha1_name() -> None:
    server = TmuxServerArgs(socket_name="dev")
    path = lock_path_for(server, "my/session:name")

    assert str(path.parent).endswith(".cache/muxdantic/lock")
    assert re.fullmatch(r"[0-9a-f]{40}", path.name)


def test_session_lock_creates_lock_file(tmp_path: Path) -> None:
    server = TmuxServerArgs(socket_name="dev")

    with session_lock(server, "api", lock_root=tmp_path) as lock_file:
        assert lock_file.exists()
        assert lock_file.parent == tmp_path
