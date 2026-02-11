from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

import pytest

from muxdantic.ensure import ensure
from muxdantic.models import EnsureRequest, TmuxServerArgs


def test_dev_step_04_ensure_contract(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    workspace = tmp_path / ".tmuxp.yaml"
    req = EnsureRequest(workspace=workspace, server=TmuxServerArgs(socket_name="mx"))

    monkeypatch.setattr("muxdantic.ensure.resolve_workspace", lambda p: workspace)
    monkeypatch.setattr("muxdantic.ensure.load_tmuxp_config", lambda p: {"session_name": "roadmap-04"})
    monkeypatch.setattr("muxdantic.ensure.extract_session_name", lambda cfg: "roadmap-04")

    @contextmanager
    def fake_lock(server: TmuxServerArgs, session_name: str):
        yield

    monkeypatch.setattr("muxdantic.ensure.session_lock", fake_lock)
    monkeypatch.setattr("muxdantic.ensure.has_session", lambda n, s: False)
    monkeypatch.setattr("muxdantic.ensure.tmuxp", lambda args, server: "")

    result = ensure(req)

    assert result.model_dump() == {
        "workspace": workspace,
        "session_name": "roadmap-04",
        "created": True,
    }
