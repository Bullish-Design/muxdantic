# Area 04 — Locking + ensure() implementation

## Goal
Implement concurrency-safe session creation:
- lock around `tmux has-session` + `tmuxp load -d --yes`
- no other operations are lock-protected

## Owned files (exclusive)
- `muxdantic/locking.py`
- `muxdantic/ensure.py`
- `tests/test_locking.py`
- `tests/test_ensure_unit.py` (unit-level; integration belongs to Area 08)

## Depends on
- Area 00 scaffold
- Area 01 (models + errors)
- Area 02 (`resolve_workspace`, `extract_session_name`)
- Area 03 (`has_session`, `tmuxp load` wrapper)

## Provides to other areas
- `ensure(req: EnsureRequest) -> EnsureResult`

## Steps
1. Implement lock key:
   - stable key = (server selector + session_name)
   - filename = sha1(key).hexdigest()
   - lock dir: `~/.cache/muxdantic/lock/`
2. Implement flock context manager using `fcntl.flock(fd, LOCK_EX)`.
3. Implement `ensure()` per SPEC algorithm:
   - resolve workspace
   - parse session name
   - lock
   - check `has-session`
   - if missing: `tmuxp load -d --yes`
   - unlock
4. Unit tests:
   - hash determinism
   - lock path safety
   - ensure algorithm behavior with mocked tmux/tmuxp calls

## Acceptance criteria
- Lock is held only around has-session + optional tmuxp load.
- Returned JSON fields match `EnsureResult` contract.

## Merge notes
- Avoid editing `jobs.py` or `cli.py` here; keep logic in `ensure.py`.
