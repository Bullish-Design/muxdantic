# SKILLS/LOCKING.md — concurrency-safe ensure with file locks

## Goal
Prevent races where multiple processes try to `tmuxp load` the same session at once.

## Scope
Lock only around:
1) `tmux has-session -t <session>`
2) if missing: `tmuxp load -d --yes <workspace>`

Everything else can be lock-free.

## Implementation (Unix)
- Lock directory: `~/.cache/muxdantic/lock/`
- Create lock file name from a stable key:
  - include server selector + session_name
  - to keep filenames safe: `sha1(key).hexdigest()`
- Use `fcntl.flock(fd, LOCK_EX)` in a context manager.
- Ensure the lock dir exists (`mkdir(parents=True, exist_ok=True)`).

## Tests
- Unit test: lock key hashing deterministic.
- Optional integration: run two processes racing ensure; verify only one load occurs (harder; can be skipped by default).
