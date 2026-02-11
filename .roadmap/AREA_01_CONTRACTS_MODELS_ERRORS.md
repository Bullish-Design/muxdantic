# Area 01 — Contracts: models, errors, and JSON stdout helpers

## Goal
Define stable Pydantic v2 models and typed exceptions so all other areas can implement behavior behind these contracts.

## Owned files (exclusive)
- `muxdantic/models.py`
- `muxdantic/errors.py`
- `muxdantic/jsonio.py` (optional helper module)

## Depends on
- Area 00 scaffold

## Provides to other areas
- `TmuxServerArgs.to_tmux_args()`
- `EnsureRequest/EnsureResult`
- `RunRequest/JobRef/JobInfo`
- `KillResult`
- `MuxdanticUsageError` (exit 2)
- `MuxdanticSubprocessError` (exit 1; captures program/args/returncode/stderr)

## Steps
1. Implement models per SPEC:
   - Stable JSON serialization (`model_dump(mode="json")`)
   - Validation:
     - `keep` XOR `rm`
     - `log_dir` XOR `log_file`
     - tag sanitization enforced (either validator or `tags.py` helper)
2. Implement exceptions:
   - Usage/validation error type
   - Subprocess error type capturing stderr
3. (Recommended) Add `jsonio.py`:
   - `print_json(obj)` helper (writes to stdout)
   - `print_error(msg)` helper (writes to stderr)
   - keep CLI thin and consistent

## Acceptance criteria
- Model validation matches SPEC rules.
- Paths serialize as strings in JSON mode.
- Exceptions are ergonomic for CLI mapping to exit codes.

## Merge notes
- Other areas should not edit these files; if they need a field change, they request it here.
