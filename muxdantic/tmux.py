"""Thin tmux/tmuxp subprocess wrappers and format parsing helpers."""

from __future__ import annotations

import subprocess
from typing import Any

from muxdantic.errors import MuxdanticSubprocessError
from muxdantic.models import TmuxServerArgs

WINDOW_FORMAT = "#{window_id}\t#{window_name}"
PANE_FORMAT = "#{pane_id}\t#{pane_dead}\t#{pane_dead_status}\t#{pane_dead_time}"


def _run_program(program: str, args: list[str], server: TmuxServerArgs) -> str:
    cmd = [program, *server.to_tmux_args(), *args]
    return _run_command(program, cmd, [*server.to_tmux_args(), *args])


def _run_command(program: str, cmd: list[str], error_args: list[str]) -> str:
    completed = subprocess.run(cmd, capture_output=True, text=True)
    if completed.returncode != 0:
        raise MuxdanticSubprocessError(
            program=program,
            args=error_args,
            returncode=completed.returncode,
            stderr=completed.stderr,
        )
    return completed.stdout


def tmux(args: list[str], server: TmuxServerArgs) -> str:
    return _run_program("tmux", args, server)


def tmuxp(args: list[str], server: TmuxServerArgs) -> str:
    if not args:
        raise ValueError("tmuxp args must include a subcommand")

    subcommand, *rest = args
    if subcommand == "load":
        cmd = ["tmuxp", "load", *server.to_tmux_args(), *rest]
        return _run_command("tmuxp", cmd, ["load", *server.to_tmux_args(), *rest])

    cmd = ["tmuxp", subcommand, *rest]
    return _run_command("tmuxp", cmd, [subcommand, *rest])


def has_session(session_name: str, server: TmuxServerArgs) -> bool:
    try:
        tmux(["has-session", "-t", session_name], server)
        return True
    except MuxdanticSubprocessError:
        return False


def new_window(session_name: str, window_name: str, server: TmuxServerArgs) -> tuple[str, str, str]:
    out = tmux(
        [
            "new-window",
            "-d",
            "-P",
            "-F",
            "#{window_id}\t#{window_name}\t#{pane_id}",
            "-t",
            session_name,
            "-n",
            window_name,
        ],
        server,
    )
    rows = _parse_tabular_output(out, expected_columns=3, label="new-window output")
    window_id, resolved_window_name, pane_id = rows[0]
    return window_id, resolved_window_name, pane_id


def list_windows(session_name: str, server: TmuxServerArgs) -> list[tuple[str, str]]:
    out = tmux(["list-windows", "-t", session_name, "-F", WINDOW_FORMAT], server)
    rows = _parse_tabular_output(out, expected_columns=2, label="list-windows output")
    return [(window_id, window_name) for window_id, window_name in rows]


def list_panes(target: str, server: TmuxServerArgs) -> list[tuple[str, int, int | None, int | None]]:
    out = tmux(["list-panes", "-t", target, "-F", PANE_FORMAT], server)
    rows = _parse_tabular_output(out, expected_columns=4, label="list-panes output")
    parsed: list[tuple[str, int, int | None, int | None]] = []
    for pane_id, pane_dead, pane_dead_status, pane_dead_time in rows:
        parsed.append(
            (
                pane_id,
                _parse_int(pane_dead, field="pane_dead"),
                _parse_optional_int(pane_dead_status, field="pane_dead_status"),
                _parse_optional_int(pane_dead_time, field="pane_dead_time"),
            )
        )
    return parsed


def set_window_option(window_id: str, option: str, value: str, server: TmuxServerArgs) -> None:
    tmux(["set-window-option", "-t", window_id, option, value], server)


def pipe_pane(pane_id: str, cmd: str, server: TmuxServerArgs) -> None:
    tmux(["pipe-pane", "-o", "-t", pane_id, cmd], server)


def send_keys(pane_id: str, string: str, server: TmuxServerArgs) -> None:
    tmux(["send-keys", "-t", pane_id, string, "C-m"], server)


def kill_window(window_id: str, server: TmuxServerArgs) -> None:
    tmux(["kill-window", "-t", window_id], server)


def _parse_int(value: str, *, field: str) -> int:
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"Invalid integer for {field}: {value!r}") from exc


def _parse_optional_int(value: str, *, field: str) -> int | None:
    if value in {"", "-", "none", "None"}:
        return None
    return _parse_int(value, field=field)


def _parse_tabular_output(output: str, *, expected_columns: int, label: str) -> list[list[str]]:
    rows: list[list[str]] = []
    for line in output.splitlines():
        if not line.strip():
            continue
        columns = line.split("\t")
        if len(columns) != expected_columns:
            raise ValueError(
                f"Malformed {label}: expected {expected_columns} tab-separated columns, got {len(columns)} in line {line!r}"
            )
        rows.append(columns)
    if not rows:
        return []
    return rows
