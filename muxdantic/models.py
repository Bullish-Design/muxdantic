"""Core pydantic contracts for muxdantic."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_TAG_ALLOWED = re.compile(r"[^a-zA-Z0-9._-]+")


def sanitize_tag(tag: str) -> str:
    """Normalize tags used in job identifiers/window names."""
    normalized = _TAG_ALLOWED.sub("-", tag.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-._")
    if not normalized:
        raise ValueError("tag must contain at least one alphanumeric character")
    return normalized


class TmuxServerArgs(BaseModel):
    """Arguments that target a tmux server."""

    socket_name: str | None = None
    socket_path: str | None = None

    model_config = ConfigDict(extra="forbid")

    def to_tmux_args(self) -> list[str]:
        args: list[str] = []
        if self.socket_name:
            args.extend(["-L", self.socket_name])
        if self.socket_path:
            args.extend(["-S", self.socket_path])
        return args


class EnsureRequest(BaseModel):
    workspace: Path
    server: TmuxServerArgs = Field(default_factory=TmuxServerArgs)

    model_config = ConfigDict(extra="forbid")


class EnsureResult(BaseModel):
    workspace: Path
    session_name: str
    created: bool

    model_config = ConfigDict(extra="forbid")


class RunRequest(BaseModel):
    workspace: Path
    server: TmuxServerArgs = Field(default_factory=TmuxServerArgs)
    tag: str
    cmd: list[str]

    keep: bool = False
    rm: bool = False
    keep_on_fail: bool = True

    log_dir: Path | None = None
    log_file: Path | None = None

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def _validate_combinations(self) -> "RunRequest":
        if self.keep and self.rm:
            raise ValueError("keep and rm are mutually exclusive")
        if self.log_dir is not None and self.log_file is not None:
            raise ValueError("log_dir and log_file are mutually exclusive")
        self.tag = sanitize_tag(self.tag)
        if not self.cmd:
            raise ValueError("cmd must contain at least one argument")
        return self


class JobRef(BaseModel):
    job_id: str
    tag: str
    ts_utc: str
    session_name: str
    window_id: str
    window_name: str
    pane_id: str
    log_file: Path | None = None

    model_config = ConfigDict(extra="forbid")


class JobInfo(BaseModel):
    job_id: str
    tag: str
    ts_utc: str
    session_name: str
    window_id: str
    window_name: str
    pane_id: str

    pane_dead: int
    pane_dead_status: int | None = None
    pane_dead_time: int | None = None
    state: Literal["running", "exited"]

    model_config = ConfigDict(extra="forbid")


class KillResult(BaseModel):
    killed: list[str]

    model_config = ConfigDict(extra="forbid")
