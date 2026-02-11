from pathlib import Path

import pytest
from pydantic import ValidationError

from muxdantic.models import RunRequest, TmuxServerArgs, sanitize_tag


def test_tmux_server_args_order() -> None:
    args = TmuxServerArgs(socket_name="name", socket_path="/tmp/tmux.sock").to_tmux_args()
    assert args == ["-L", "name", "-S", "/tmp/tmux.sock"]


def test_run_request_validates_mutual_exclusions() -> None:
    with pytest.raises(ValidationError, match="mutually exclusive"):
        RunRequest(workspace=Path("w"), tag="x", cmd=["echo"], keep=True, rm=True)

    with pytest.raises(ValidationError, match="mutually exclusive"):
        RunRequest(
            workspace=Path("w"),
            tag="x",
            cmd=["echo"],
            log_dir=Path("logs"),
            log_file=Path("logs/out.log"),
        )


def test_run_request_sanitizes_tag() -> None:
    req = RunRequest(workspace=Path("w"), tag=" Build::Release ", cmd=["echo", "ok"])
    assert req.tag == "build-release"


def test_sanitize_tag_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one alphanumeric"):
        sanitize_tag("---")
