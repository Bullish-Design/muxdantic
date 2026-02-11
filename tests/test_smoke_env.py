import subprocess

import pytest


@pytest.mark.parametrize(
    ("command", "tool_name"),
    [(["tmux", "-V"], "tmux"), (["tmuxp", "--version"], "tmuxp")],
)
def test_tool_version_command_succeeds(command: list[str], tool_name: str) -> None:
    try:
        result = subprocess.run(command, capture_output=True, text=True)
    except FileNotFoundError as exc:
        pytest.fail(f"{tool_name} binary is missing from PATH: {exc}")

    assert result.returncode == 0, (
        f"{tool_name} command failed: {' '.join(command)!r} exited with {result.returncode}; "
        f"stdout={result.stdout!r}; stderr={result.stderr!r}"
    )
