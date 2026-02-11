from __future__ import annotations

import subprocess
import pytest

from muxdantic.errors import MuxdanticSubprocessError
from muxdantic.models import TmuxServerArgs
from muxdantic.tmux import list_panes, list_windows, tmux, tmuxp


def test_tmux_applies_server_args(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, list[str]] = {}

    def fake_run(cmd: list[str], *, capture_output: bool, text: bool) -> subprocess.CompletedProcess[str]:
        seen["cmd"] = cmd
        assert capture_output is True
        assert text is True
        return subprocess.CompletedProcess(cmd, 0, stdout="ok\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    out = tmux(["list-sessions"], TmuxServerArgs(socket_name="sock", socket_path="/tmp/t.sock"))
    assert out == "ok\n"
    assert seen["cmd"] == ["tmux", "-L", "sock", "-S", "/tmp/t.sock", "list-sessions"]


def test_tmuxp_nonzero_raises_subprocess_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd: list[str], *, capture_output: bool, text: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="bad things")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(MuxdanticSubprocessError, match="bad things"):
        tmuxp(["load"], TmuxServerArgs())


def test_list_windows_parses_tab_output(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd: list[str], *, capture_output: bool, text: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 0, stdout="@1\tdev\n@2\tjob:build\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    windows = list_windows("dev", TmuxServerArgs())
    assert windows == [("@1", "dev"), ("@2", "job:build")]


def test_list_panes_parses_optional_int_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(cmd: list[str], *, capture_output: bool, text: bool) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(cmd, 0, stdout="%9\t0\t\t\n%10\t1\t23\t1700000000\n", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    panes = list_panes("@2", TmuxServerArgs())
    assert panes == [("%9", 0, None, None), ("%10", 1, 23, 1700000000)]
