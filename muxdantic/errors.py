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
        self.command_args = args
        self.returncode = returncode
        self.stderr = stderr
        super().__init__(self.__str__())

    def __str__(self) -> str:
        base = f"{self.program} failed with exit code {self.returncode}"
        if self.command_args:
            base = f"{base}: {' '.join(self.command_args)}"
        if self.stderr:
            stderr = self.stderr.rstrip()
            if stderr:
                exit_line = f"{self.program} failed with exit code {self.returncode}"
                for duplicate_prefix in (base, exit_line):
                    if stderr.startswith(duplicate_prefix):
                        stderr = stderr[len(duplicate_prefix) :]
                        if duplicate_prefix == exit_line and self.command_args:
                            args_suffix = f": {' '.join(self.command_args)}"
                            if stderr.startswith(args_suffix):
                                stderr = stderr[len(args_suffix) :]
                        stderr = stderr.lstrip("\r\n")
                        break

                if stderr:
                    return f"{base}\n{stderr}"
        return base
