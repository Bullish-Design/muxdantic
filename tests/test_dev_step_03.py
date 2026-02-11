from __future__ import annotations

import subprocess

import pytest

from muxdantic.models import TmuxServerArgs
from muxdantic.tmux import list_windows


def test_dev_step_03_tmux_wrapper_parsing(monkeypatch: pytest.MonkeyPatch) -> None:
    called: dict[str, list[str]] = {}

    def fake_run(cmd: list[str], *, capture_output: bool, text: bool) -> subprocess.CompletedProcess[str]:
        called["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="@7\tjob:build\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    windows = list_windows("dev", TmuxServerArgs(socket_name="mx"))

    assert called["cmd"] == ["tmux", "-L", "mx", "list-windows", "-t", "dev", "-F", "#{window_id}\t#{window_name}"]
    assert windows == [("@7", "job:build")]
