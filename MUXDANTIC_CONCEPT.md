# MUXDANTIC_CONCEPT.md — muxdantic

## What muxdantic is

**muxdantic** is a tiny Python library + CLI that does two things:

1. **Ensure** a tmux session exists from a given **tmuxp** workspace file (load detached).
2. **Run fire-and-forget commands** inside that session as **tagged tmux “job windows”**.

tmux is the runtime, the state store, and the observability surface. muxdantic is just glue.

---

## Core idea

A “job” is **one tmux window** created in the session derived from a tmuxp workspace.

- Tagging = window naming (`job:<tag>:<timestamp>`)
- Listing jobs = `tmux list-windows` filtered by `job:` prefix
- Cleanup = tmux options + a tiny shell wrapper
- Logs = optional `tmux pipe-pane` to a file

No daemon. No DB. No custom scheduler.

---

## Design principles

- **Unix-first**: use tmux features and small shell wrappers instead of Python orchestration.
- **Minimal schema**: parse only what’s needed from tmuxp YAML; tolerate everything else.
- **Predictable defaults**:
  - Success → auto-cleanup (no litter)
  - Failure → stays visible (easy debugging)
- **Composable output**: machine-readable job references (JSON) for scripting.

---

## Responsibilities split

### tmuxp (declarative loader)
- Reads workspace config and creates the base session/windows/panes.
- muxdantic uses it only to load the session **detached** when missing.

### tmux (imperative runner)
- muxdantic uses `tmux` directly to spawn job windows, stream logs, list jobs, and kill jobs.

This separation keeps muxdantic stable even with “rich” tmuxp configs.

---

## Default job lifecycle

muxdantic starts jobs in a dedicated window with these policies:

### Keep failures visible
- Enable `remain-on-exit` for the job window so a failing process doesn’t vanish.
- Print exit status to the pane on failure for quick inspection.

### Auto-cleanup on success
- On success, the wrapper kills its own pane using `$TMUX_PANE`.
- With a single-pane window, that removes the job window entirely.

### User-controllable lifecycle knobs
- `--keep` : keep the window even on success
- `--rm` : remove the window even on failure
- `--keep-on-fail / --no-keep-on-fail` : control “failure stays visible” (default on)

The default is tuned for “fire-and-forget but debuggable”.

---

## Tagging and naming

Job window name is the primary tag:

```
job:<tag>:<timestamp>
```

Examples:
- `job:migrate:20260211-143012`
- `job:lint:20260211-143055`

muxdantic treats any window starting with `job:` as a managed job.

---

## Optional logging

When `--log-file PATH` is provided:

- muxdantic enables `tmux pipe-pane -o` for the job pane
- output is appended to the file (no logger subsystem)

This keeps the library small while producing durable logs for detached workflows.

---

## Concurrency and locking

muxdantic assumes multiple processes might try to “ensure” the same workspace at once.

Solution:
- Wrap the *ensure/load* section with `flock` on a lock file such as:

```
~/.cache/muxdantic/lock/<session_name>.lock
```

Lock scope:
- Held only around `tmux has-session` + `tmuxp load -d --yes ...`
- Released before job spawning to allow high-throughput job creation

Goal: avoid session-creation races without adding any persistent service.

---

## Targeting an existing window (advanced)

In addition to “new job window per run”, muxdantic can optionally support:

- `run --window <name-or-id> -- <cmd...>`

Use cases:
- send one-off commands into a long-lived “dev” or “ssh” window
- share a single context while still using muxdantic’s CLI

This is an ergonomic feature, not required for the core job model.

---

## Job discovery and listing

Because tmux is the source of truth, listing is a query:

- `ls-jobs <workspace>`:
  - read session name from tmuxp YAML
  - `tmux list-windows -t <session> -F <format>`
  - filter windows whose names begin with `job:`

Suggested fields:
- `window_name` (tag + timestamp)
- `window_id`, `pane_id`
- `active`/flags (best-effort)
- “dead” indicator (pane exited)
- exit status (best-effort: print to pane; optionally scrape last line)

muxdantic doesn’t invent a state machine; it reflects tmux.

---

## Minimal Pydantic models

muxdantic only needs to parse enough of tmuxp YAML to find `session_name`
(and optionally validate “shape”):

### Workspace parsing layer (tolerant)
- `WorkspaceSpec`
  - `session_name: str` (required)
  - `windows: list[WindowSpec] = []` (optional)
- `WindowSpec`
  - `window_name: str | None`
  - `panes: list[Any] = []`
- `PaneSpec`
  - accepts tmuxp pane variants (string, dict with `shell_command`, blank)
  - can normalize to `list[str]` if needed

All parsing models should allow unknown keys (`extra="allow"`) so real-world tmuxp configs don’t break muxdantic.

### Execution request/response layer
- `LoadRequest`: workspace path + tmux socket args
- `RunRequest`: workspace + cmd argv + tag + lifecycle/log options
- `JobRef`: session + window_id + pane_id + window_name

CLI prints `JobRef` as JSON for shell pipelines.

---

## CLI surface (kept intentionally small)

- `muxdantic ensure <workspace>`
  - resolve workspace file
  - parse `session_name`
  - if missing: `tmuxp load -d --yes <workspace>`

- `muxdantic run <workspace> [opts] -- <cmd...>`
  - ensure session exists
  - create job window (or target existing window, if supported)
  - apply lifecycle policy
  - optionally attach `pipe-pane` for logging
  - print JobRef JSON

- `muxdantic ls-jobs <workspace>`
  - list job windows in that session

- `muxdantic kill <workspace> (--tag TAG | --window-id ID | --all-jobs)`
  - thin sugar over `tmux kill-window`

Everything else is “use tmux directly.”

---

## Workspace path resolution

muxdantic accepts:
- a direct tmuxp config file path
- or a directory containing a conventional workspace file (`.tmuxp.yaml`, `.tmuxp.yml`, `.tmuxp.json`)

Resolution is deterministic and only within the provided path.

---

## Safety and quoting

- Accept commands as argv (`-- <cmd...>`), not a single shell string.
- Only use shell quoting at the final boundary (e.g., `<shell> -lc '<wrapped>'`).
- Prefer `subprocess.run([...])` with argv lists everywhere else.
- Never splice untrusted strings into tmux format strings.

---

## Non-goals

- Not a tmux config manager
- Not a tmuxp replacement
- Not a background scheduler/daemon
- Not a remote execution system (SSH is fine as a command, but muxdantic doesn’t manage it)

---

## Essence

**muxdantic ensures a tmuxp-defined session exists, then uses plain tmux to spawn tagged job windows that clean up on success, stay visible on failure, and optionally stream logs—using tmux itself as the system of record.**
