# SKILLS/TEST_STRATEGY.md — unit + (optional) integration tests

## Unit tests (default)
- Tag sanitization: edge cases, invalid-only tags, trimming.
- Workspace resolution: dir/file cases, multiple config errors.
- tmux format parsing: parsing of `\t`-separated fields into `JobInfo`.
- Model validation: mutually exclusive flags, log path rules.

## Smoke test (required)
A single test that verifies the devenv assumptions:
- `tmux -V` runs
- `tmuxp --version` runs

This test should not require a running tmux server.

## Integration tests (opt-in)
If you add them, make them skip by default unless an env var is set, e.g. `MUXDANTIC_INTEGRATION=1`.
Suggested flow:
1) Create a temp tmux server via `-L` with a random socket name.
2) Use a tiny tmuxp workspace pointing to a session name.
3) `ensure` then `run` a command that exits 0 and one that exits non-zero.
4) Verify window presence/absence using `ls-jobs`.

Keep integration tests isolated from the user’s real tmux server by always using `-L`.
