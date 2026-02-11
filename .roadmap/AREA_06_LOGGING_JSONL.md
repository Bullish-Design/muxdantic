# Area 06 — Logging: JSONL sink + pipe-pane wiring

## Goal
Provide optional durable job logs as JSONL using `tmux pipe-pane` piping pane output to a Python sink.

## Owned files (exclusive)
- `muxdantic/logging.py` (pipe-pane helpers, log file resolution)
- `muxdantic/logging_sink.py` (module runnable via `python -m muxdantic.logging_sink`)
- `tests/test_logging_sink.py`

## Depends on
- Area 00 scaffold
- Area 01 (errors/models)
- Area 03 (`pipe_pane` primitive)

## Provides to Area 05 (jobs)
- `resolve_log_file(log_dir, log_file, job_id) -> Path|None`
- `pipe_pane_to_jsonl(server, pane_id, job_id, path) -> None`
- `build_sink_command(job_id, path) -> str` (shell-safe quoting)

## Implementation requirements
1. CLI surface (enforced in RunRequest):
   - `--log-dir DIR` → `<DIR>/<job_id>.jsonl`
   - `--log-file PATH` → exact path
2. tmux wiring (must be called *before* command starts):
   - `tmux pipe-pane -o -t <pane_id> "<python -m muxdantic.logging_sink --job-id ... --file ...>"`
3. Sink behavior:
   - read stdin line-by-line
   - write JSONL `{ts, job_id, line}`
   - `ts` in UTC with `Z`
   - strip only the trailing newline from line
   - ensure parent directories exist
   - flush frequently

## Tests
- Pure unit test: feed known lines; assert JSON objects per line and UTC ts format.
- No need to test tmux pipe-pane in unit tests (integration belongs to Area 08).

## Merge notes
- Do not modify `jobs.py`. It should already call into helpers in `muxdantic/logging.py`.
