from __future__ import annotations

import io
import json
import re
from pathlib import Path

from muxdantic.logging_sink import stream_jsonl


ISO_UTC_Z_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z$")


def test_stream_jsonl_writes_line_records(tmp_path: Path) -> None:
    log_path = tmp_path / "logs" / "job.jsonl"
    stdin = io.StringIO("first line\n  keep spaces  \nlast-no-newline")

    stream_jsonl(job_id="abc123", output_file=log_path, stdin=stdin)

    rows = [json.loads(line) for line in log_path.read_text(encoding="utf-8").splitlines()]
    assert [row["line"] for row in rows] == ["first line", "  keep spaces  ", "last-no-newline"]
    assert all(row["job_id"] == "abc123" for row in rows)
    assert all(ISO_UTC_Z_RE.match(row["ts"]) for row in rows)
