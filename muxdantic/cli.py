"""Command-line interface for muxdantic operations."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from muxdantic.ensure import ensure
from muxdantic.errors import MuxdanticSubprocessError, MuxdanticUsageError
from muxdantic.jobs import kill, list_jobs, run
from muxdantic.jsonio import print_error, print_json
from muxdantic.models import EnsureRequest, RunRequest, TmuxServerArgs


def _add_server_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("-L", "--socket-name", dest="socket_name")
    parser.add_argument("-S", "--socket-path", dest="socket_path")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="muxdantic")
    subparsers = parser.add_subparsers(dest="command", required=True)

    ensure_parser = subparsers.add_parser("ensure")
    _add_server_args(ensure_parser)
    ensure_parser.add_argument("workspace")

    run_parser = subparsers.add_parser("run")
    _add_server_args(run_parser)
    run_parser.add_argument("workspace")
    run_parser.add_argument("--tag", required=True)

    lifecycle_group = run_parser.add_mutually_exclusive_group()
    lifecycle_group.add_argument("--keep", action="store_true")
    lifecycle_group.add_argument("--rm", action="store_true")

    keep_on_fail_group = run_parser.add_mutually_exclusive_group()
    keep_on_fail_group.add_argument("--keep-on-fail", dest="keep_on_fail", action="store_true", default=True)
    keep_on_fail_group.add_argument("--no-keep-on-fail", dest="keep_on_fail", action="store_false")

    log_group = run_parser.add_mutually_exclusive_group()
    log_group.add_argument("--log-dir")
    log_group.add_argument("--log-file")


    ls_jobs_parser = subparsers.add_parser("ls-jobs")
    _add_server_args(ls_jobs_parser)
    ls_jobs_parser.add_argument("workspace")

    kill_parser = subparsers.add_parser("kill")
    _add_server_args(kill_parser)
    kill_parser.add_argument("workspace")
    selectors = kill_parser.add_mutually_exclusive_group(required=True)
    selectors.add_argument("--job-id")
    selectors.add_argument("--tag")
    selectors.add_argument("--all-jobs", action="store_true")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    raw_argv = list(argv) if argv is not None else sys.argv[1:]
    try:
        args, extras = parser.parse_known_args(raw_argv)
    except SystemExit as exc:
        return int(exc.code)

    server = TmuxServerArgs(socket_name=args.socket_name, socket_path=args.socket_path)

    try:
        if args.command == "ensure":
            req = EnsureRequest(workspace=Path(args.workspace), server=server)
            print_json(ensure(req))
            return 0

        if args.command == "run":
            if not extras or extras[0] != "--" or len(extras) == 1:
                raise MuxdanticUsageError("run requires '--' followed by command arguments")

            req = RunRequest(
                workspace=Path(args.workspace),
                server=server,
                tag=args.tag,
                keep=args.keep,
                rm=args.rm,
                keep_on_fail=args.keep_on_fail,
                log_dir=Path(args.log_dir) if args.log_dir else None,
                log_file=Path(args.log_file) if args.log_file else None,
                cmd=extras[1:],
            )
            print_json(run(req))
            return 0

        if args.command != "run" and extras:
            raise MuxdanticUsageError(f"Unexpected extra arguments: {' '.join(extras)}")

        if args.command == "ls-jobs":
            jobs = list_jobs(Path(args.workspace), server)
            print_json([job.model_dump(mode="json") for job in jobs])
            return 0

        if args.command == "kill":
            result = kill(
                Path(args.workspace),
                server,
                job_id=args.job_id,
                tag=args.tag,
                all_jobs=args.all_jobs,
            )
            print_json(result)
            return 0

        raise MuxdanticUsageError(f"Unknown command: {args.command}")
    except MuxdanticUsageError as exc:
        print_error(str(exc))
        return 2
    except MuxdanticSubprocessError as exc:
        print_error(str(exc))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
