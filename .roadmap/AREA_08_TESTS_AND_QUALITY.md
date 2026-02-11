# Area 08 — Tests & quality gates (smoke + optional integration)

## Goal
Ensure the project meets the SPEC testing requirements and stays deterministic.

## Owned files (exclusive)
- `tests/test_smoke_env.py` (required)
- `tests/test_integration_tmux.py` (optional, guarded)
- `tests/test_models_validation.py` (optional split if Area 01 prefers not to own tests)

## Depends on
- Area 00 scaffold
- Area 01+ (for full suite)

## Required smoke test
A single pytest that verifies devenv assumptions without needing a running tmux server:
- `tmux -V` runs
- `tmuxp --version` runs

## Optional integration tests (guarded)
- Skip by default unless `MUXDANTIC_INTEGRATION=1`
- Use isolated tmux server: `-L <random-socket>`
- Flow:
  1) temp tmuxp workspace with session name
  2) `ensure`
  3) `run` success command + failure command
  4) verify via `ls-jobs`
  5) `kill --all-jobs`

## Acceptance criteria
- Unit tests are fast and deterministic.
- Integration tests do not touch the user’s real tmux server.
