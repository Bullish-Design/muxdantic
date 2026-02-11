"""JSONL sink process used by tmux pipe-pane."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import TextIO


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def stream_jsonl(*, job_id: str, output_file: Path, stdin: TextIO) -> None:
    """Read lines from stdin and write JSONL records to output_file."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open("a", encoding="utf-8", buffering=1) as fh:
        for raw_line in stdin:
            line = raw_line.rstrip("\n")
            record = {"ts": _ts_utc(), "job_id": job_id, "line": line}
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
            fh.flush()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="muxdantic JSONL logging sink")
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--file", required=True)
    args = parser.parse_args(argv)

    stream_jsonl(job_id=args.job_id, output_file=Path(args.file), stdin=sys.stdin)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
