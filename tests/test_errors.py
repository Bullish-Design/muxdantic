from muxdantic.errors import MuxdanticSubprocessError


def test_subprocess_error_str_deduplicates_base_prefix_from_stderr() -> None:
    err = MuxdanticSubprocessError(
        program="tmux",
        args=["new-window", "-n", "job:test"],
        returncode=1,
        stderr=(
            "tmux failed with exit code 1: new-window -n job:test\n"
            "usage: tmux new-window [-abdkPS] [-c start-directory] [-e environment] [-F format] "
            "[-n window-name] [-t target-window] [shell-command]\n"
            "bad target: foo"
        ),
    )

    assert str(err) == (
        "tmux failed with exit code 1: new-window -n job:test\n"
        "usage: tmux new-window [-abdkPS] [-c start-directory] [-e environment] [-F format] "
        "[-n window-name] [-t target-window] [shell-command]\n"
        "bad target: foo"
    )
