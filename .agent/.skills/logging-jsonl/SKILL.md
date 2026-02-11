# .agent/.skills/logging-jsonl/SKILL.md — pipe-pane + Python sink

## Goal
When enabled, capture pane output into a durable JSONL file keyed by `job_id`.

## CLI surface
- `--log-dir DIR` → default file: `<DIR>/<job_id>.jsonl`
- `--log-file PATH` → exact path
(mutually exclusive)

## tmux wiring
Call before starting the command:
- `tmux pipe-pane -o -t <pane_id> "python -m muxdantic.logging_sink --job-id <id> --file <path>"`

`-o` means “only if no existing pipe” (safer if re-run).

## Sink behavior (`python -m muxdantic.logging_sink`)
- Read from stdin line-by-line.
- Write JSON Lines objects:
  - `ts` (UTC ISO 8601 with `Z`)
  - `job_id`
  - `line` (rstrip the newline, preserve other whitespace)
- Flush frequently (line-buffered) for tailing.
- Ensure parent directories exist.

## Testing
- Unit: feed sample lines into sink (use `io.StringIO`) and assert JSONL output.
- No need to test tmux pipe-pane in unit tests; keep it integration-only if desired.
