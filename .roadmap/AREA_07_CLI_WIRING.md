# Area 07 — CLI wiring (argparse) and exit code mapping

## Goal
Implement the CLI contract with JSON stdout on success, diagnostics on stderr on error, and stable exit codes (0/1/2).

## Owned files (exclusive)
- `muxdantic/cli.py`
- (optional) `tests/test_cli_smoke.py`

## Depends on
- Area 00 scaffold
- Area 01 (models + errors + json helpers)
- Area 02/03/04/05/06 (feature implementations)

## Strategy to avoid merge conflicts
- This area is the **only** one that edits `cli.py`.
- Keep `cli.py` as a thin dispatcher:
  - parse args
  - create Pydantic request models
  - call `ensure/run/list_jobs/kill`
  - print JSON
  - map exceptions to exit codes

## Steps
1. Argparse subcommands: `ensure`, `run`, `ls-jobs`, `kill`
2. Support server args `-L` / `-S` on each command
3. Enforce `--` separator for `run` command (required)
4. Map exceptions:
   - `MuxdanticUsageError` -> print message -> exit 2
   - `MuxdanticSubprocessError` -> print program + rc + stderr -> exit 1
5. JSON stdout:
   - single objects for ensure/run/kill
   - JSON array for ls-jobs

## Acceptance criteria
- Matches SPEC CLI JSON shapes exactly.
- Never prints stack traces by default.
