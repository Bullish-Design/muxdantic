from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pytest

from muxdantic.models import EnsureRequest, TmuxServerArgs
from muxdantic.ensure import ensure


def test_ensure_existing_session_does_not_load(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = tmp_path / ".tmuxp.yaml"
    req = EnsureRequest(workspace=workspace, server=TmuxServerArgs(socket_name="dev"))
    events: list[str] = []

    monkeypatch.setattr("muxdantic.ensure.resolve_workspace", lambda p: workspace)
    monkeypatch.setattr("muxdantic.ensure.load_tmuxp_config", lambda p: {"session_name": "app"})
    monkeypatch.setattr("muxdantic.ensure.extract_session_name", lambda cfg: "app")

    @contextmanager
    def fake_lock(server: TmuxServerArgs, session_name: str):
        events.append(f"lock-enter:{session_name}")
        try:
            yield
        finally:
            events.append(f"lock-exit:{session_name}")

    def fake_has_session(session_name: str, server: TmuxServerArgs) -> bool:
        events.append(f"has:{session_name}")
        return True

    def fake_tmuxp(args: list[str], server: TmuxServerArgs) -> str:
        events.append("tmuxp-load")
        return ""

    monkeypatch.setattr("muxdantic.ensure.session_lock", fake_lock)
    monkeypatch.setattr("muxdantic.ensure.has_session", fake_has_session)
    monkeypatch.setattr("muxdantic.ensure.tmuxp", fake_tmuxp)

    result = ensure(req)

    assert result.workspace == workspace
    assert result.session_name == "app"
    assert result.created is False
    assert events == ["lock-enter:app", "has:app", "lock-exit:app"]


def test_ensure_missing_session_loads_tmuxp(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = tmp_path / ".tmuxp.json"
    req = EnsureRequest(workspace=workspace, server=TmuxServerArgs(socket_path="/tmp/tmux.sock"))
    calls: dict[str, list[object]] = {"tmuxp": []}

    monkeypatch.setattr("muxdantic.ensure.resolve_workspace", lambda p: workspace)
    monkeypatch.setattr("muxdantic.ensure.load_tmuxp_config", lambda p: {"session_name": "backend"})
    monkeypatch.setattr("muxdantic.ensure.extract_session_name", lambda cfg: "backend")

    @contextmanager
    def fake_lock(server: TmuxServerArgs, session_name: str):
        yield

    monkeypatch.setattr("muxdantic.ensure.session_lock", fake_lock)
    monkeypatch.setattr("muxdantic.ensure.has_session", lambda n, s: False)

    def fake_tmuxp(args: list[str], server: TmuxServerArgs) -> str:
        calls["tmuxp"].append((args, server))
        return ""

    monkeypatch.setattr("muxdantic.ensure.tmuxp", fake_tmuxp)

    result = ensure(req)

    assert result.session_name == "backend"
    assert result.created is True
    assert calls["tmuxp"] == [(["load", "-d", "--yes", str(workspace)], req.server)]
