from pathlib import Path

from muxdantic.errors import MuxdanticSubprocessError, MuxdanticUsageError
from muxdantic.models import EnsureRequest, EnsureResult, RunRequest


def test_step_01_contracts_end_to_end() -> None:
    req = EnsureRequest(workspace=Path("workspace/.tmuxp.yaml"))
    result = EnsureResult(workspace=req.workspace, session_name="dev", created=False)
    assert result.model_dump(mode="json") == {
        "workspace": "workspace/.tmuxp.yaml",
        "session_name": "dev",
        "created": False,
    }

    run = RunRequest(workspace=Path("workspace/.tmuxp.yaml"), tag="CI Build", cmd=["make", "test"])
    assert run.tag == "ci-build"

    usage = MuxdanticUsageError("bad arguments")
    assert usage.exit_code == 2

    sub = MuxdanticSubprocessError(program="tmux", args=["new-window"], returncode=1, stderr="boom")
    assert sub.exit_code == 1
    assert "boom" in str(sub)
