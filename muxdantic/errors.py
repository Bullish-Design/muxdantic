"""Exception contracts for muxdantic."""

from __future__ import annotations


class MuxdanticError(Exception):
    """Base exception for muxdantic failures."""


class MuxdanticUsageError(MuxdanticError):
    """Represents user or validation errors (CLI exit code 2)."""

    exit_code: int = 2


class MuxdanticSubprocessError(MuxdanticError):
    """Represents operational subprocess failures (CLI exit code 1)."""

    exit_code: int = 1

    def __init__(
        self,
        *,
        program: str,
        args: list[str],
        returncode: int,
        stderr: str | None = None,
    ) -> None:
        self.program = program
        self.args = args
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(self.__str__())

    def __str__(self) -> str:
        base = f"{self.program} failed with exit code {self.returncode}"
        if self.args:
            base = f"{base}: {' '.join(self.args)}"
        if self.stderr:
            return f"{base}\n{self.stderr.rstrip()}"
        return base
