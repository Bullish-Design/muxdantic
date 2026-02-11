# SPEC.md — muxdantic MVP specification

## 1. Summary

muxdantic is a tiny Python library + CLI that:

1) Ensures a tmux session exists from a tmuxp workspace file (loaded detached).
2) Runs “fire-and-forget” commands inside that session as **tagged tmux job windows**.

tmux is the runtime, state store, and observability surface. muxdantic is glue.

---

## 2. Goals and non-goals

### Goals (MVP)
- Deterministic workspace resolution (file or directory convention).
- Concurrency-safe `ensure` (no session-creation races).
- Run jobs as one tmux window each, with deterministic naming and discovery.
- Defaults: auto-cleanup on success; keep visible on failure.
- Scriptable CLI: **JSON on stdout**, diagnostics on stderr.
- Optional log capture via `tmux pipe-pane` to a **JSONL** file.
- Minimal, tolerant tmuxp parsing (extract only `session_name`).

### Non-goals
- No daemon / background scheduler.
- No database / custom job state machine.
- No remote execution management (SSH is “just a command”).
- Not a tmux/tmuxp configuration manager.

---

## 3. Definitions

- **Workspace**: a tmuxp config file (`.tmuxp.yaml/.yml/.json`).
- **Session**: tmux session named by `session_name` in the workspace.
- **Job**: exactly **one tmux window** created by muxdantic.
- **Job window**: a window whose name begins with `job:`.

---

## 4. CLI contract (MVP)

All commands:
- Write **valid JSON** to stdout on success.
- Write human diagnostics to stderr on error.
- Exit codes:
  - `0`: success
  - `1`: operational failure (tmux/tmuxp subprocess errors)
  - `2`: usage/validation error (bad args, missing workspace, invalid tag, etc.)

### 4.1 `muxdantic ensure <workspace> [-L NAME] [-S PATH]`
Purpose: ensure the session exists (load detached if missing).

Success JSON:
```json
{"workspace":"...","session_name":"...","created":false}
```

### 4.2 `muxdantic run <workspace> --tag TAG [--keep|--rm] [--keep-on-fail|--no-keep-on-fail] [--log-dir DIR|--log-file FILE] [-L/-S] -- <cmd...>`
Purpose: spawn a job window and start the command.

Success JSON (JobRef):
```json
{"job_id":"...","tag":"...","ts_utc":"...","session_name":"...","window_id":"...","window_name":"...","pane_id":"...","log_file":"..."}
```

Rules:
- `--` is required to separate muxdantic flags from the command.
- `--keep` and `--rm` are mutually exclusive.
- `--log-dir` and `--log-file` are mutually exclusive.

### 4.3 `muxdantic ls-jobs <workspace> [-L/-S]`
Purpose: list current job windows in the session and their pane status.

Success JSON:
```json
[
  {"job_id":"...","tag":"...","ts_utc":"...","session_name":"...","window_id":"...","window_name":"...","pane_id":"...","pane_dead":0,"pane_dead_status":null,"pane_dead_time":null,"state":"running"}
]
```

### 4.4 `muxdantic kill <workspace> (--job-id ID | --tag TAG | --all-jobs) [-L/-S]`
Purpose: kill job windows.

Success JSON:
```json
{"killed":["<window_id>","..."]}
```

---

## 5. Python library API (MVP)

The library must expose the same behaviors as the CLI, via typed request/result models.

### 5.1 Module layout (recommended)
```
muxdantic/
  __init__.py
  cli.py
  errors.py
  models.py
  workspace.py
  tmux.py
  locking.py
  jobs.py
  logging_sink.py
```

### 5.2 Public functions (minimum)
- `ensure(req: EnsureRequest) -> EnsureResult`
- `run(req: RunRequest) -> JobRef`
- `list_jobs(workspace: Path, server: TmuxServerArgs) -> list[JobInfo]`
- `kill(workspace: Path, server: TmuxServerArgs, *, job_id: str | None, tag: str | None, all_jobs: bool) -> KillResult`

> Implementation may keep the public API minimal (even CLI-first), but models and behavior must remain stable.

---

## 6. Data models and validation

Use Pydantic v2 models for all inputs/outputs.

### 6.1 `TmuxServerArgs`
Fields:
- `socket_name: str | None`  (maps to `tmux -L`)
- `socket_path: str | None`  (maps to `tmux -S`)

Methods:
- `to_tmux_args() -> list[str]` (stable ordering: `-L` then `-S` if present)

### 6.2 `EnsureRequest`
- `workspace: Path`
- `server: TmuxServerArgs`

### 6.3 `EnsureResult`
- `workspace: Path`
- `session_name: str`
- `created: bool`

### 6.4 `RunRequest`
- `workspace: Path`
- `server: TmuxServerArgs`
- `tag: str`
- `cmd: list[str]`
- lifecycle flags:
  - `keep: bool = False`
  - `rm: bool = False`
  - `keep_on_fail: bool = True`
- logging:
  - `log_dir: Path | None = None`
  - `log_file: Path | None = None`

Validation:
- Tag must be valid after sanitization (see §7.2).
- `keep` XOR `rm` (cannot both be true).
- `log_dir` XOR `log_file`.

### 6.5 `JobRef`
- `job_id: str` (shortuuid)
- `tag: str` (sanitized)
- `ts_utc: str` (UTC ISO 8601 `YYYYMMDDThhmmssZ` or full ISO8601; must include `Z`)
- `session_name: str`
- `window_id: str`
- `window_name: str`
- `pane_id: str`
- `log_file: Path | None`

### 6.6 `JobInfo`
- all `JobRef` identity fields:
  - `job_id`, `tag`, `ts_utc`, `session_name`, `window_id`, `window_name`, `pane_id`
- pane status:
  - `pane_dead: int` (0/1)
  - `pane_dead_status: int | None`
  - `pane_dead_time: int | None` (epoch seconds from tmux, if available)
- derived:
  - `state: Literal["running","exited"]`

### 6.7 `KillResult`
- `killed: list[str]` (window_ids killed)

---

## 7. Core behaviors

### 7.1 Workspace resolution
Inputs accepted:
- A direct file path, OR
- A directory containing exactly one of:
  - `.tmuxp.yaml`
  - `.tmuxp.yml`
  - `.tmuxp.json`

Rules:
1) If input is a file: accept only the above suffixes; return it.
2) If input is a directory: search for the three filenames; error if none or more than one.
3) Error messages:
   - None found: mention the directory and expected filenames.
   - More than one: list candidate paths.

### 7.2 Session name extraction (tolerant)
- Load YAML via `yaml.safe_load`, JSON via `json.load`.
- Extract:
  - `cfg["session_name"]` (required), optionally tolerate `cfg["session"]` if present.
- If missing: usage/validation error (exit 2 in CLI).

### 7.3 Tag sanitization (mandatory)
Rules:
- Convert to lowercase.
- Allow characters: `[a-z0-9._-]`
- Replace any run of invalid chars with `-`.
- Trim leading/trailing `-` and `_`.
- If empty after sanitization: error.

The sanitized tag is the only value used in window naming and any file naming.

### 7.4 Job identity and window naming
A job window name MUST be:
```
job:<tag>:<utc_ts>:<job_id>
```

- `<utc_ts>` format: `YYYYMMDDThhmmssZ` (UTC).
- `<job_id>`: shortuuid (also used for default log filename).

### 7.5 Ensure behavior (`ensure`)
Algorithm:
1) Resolve workspace file.
2) Extract `session_name`.
3) Acquire a file lock scoped to `(server selector, session_name)` (see §8).
4) Run `tmux has-session -t <session_name>`; if exists → `created=false`.
5) If missing: run `tmuxp load -d --yes <workspace>`; then `created=true`.
6) Release lock.

Only steps 4–5 are lock-protected.

### 7.6 Run behavior (`run`)
Required ordering (to ensure options/logging attach before execution begins):

1) `ensure` (as above).
2) Generate:
   - `job_id` (shortuuid)
   - `ts_utc` (UTC)
   - `window_name` per §7.4
3) Create detached window in the session:
   - `tmux new-window -d -t <session> -n <window_name>`
4) Capture identifiers:
   - Obtain `window_id` for the new window.
   - Obtain `pane_id` for the first pane of that window.
   > Implementation may:
   > - parse `tmux list-windows` and match by `window_name`, OR
   > - use `tmux display-message -p` targeting the most recently created window.
   > The result must be deterministic and reliable.
5) Set lifecycle policy using `remain-on-exit` (see §7.7).
6) If logging enabled (see §9), call `tmux pipe-pane -o -t <pane_id> "<sink command>"`
7) Start command by sending keys:
   - Convert argv to a safe shell string with `shlex.join(cmd)`
   - Send: `exec <joined-cmd>` and Enter
     - `tmux send-keys -t <pane_id> -- "exec <...>" C-m`

Output: `JobRef` JSON.

### 7.7 Lifecycle policy
Use tmux window option `remain-on-exit`:

- Default: keep failures visible, auto-remove on success:
  - if `keep_on_fail == True` and neither `keep` nor `rm`: `remain-on-exit=failed`
- `--keep`:
  - `remain-on-exit=on` (always remain, even on success)
- `--rm`:
  - `remain-on-exit=off` (never remain; failure is not kept)
- If `keep_on_fail == False` (and not `--keep`):
  - `remain-on-exit=off`

### 7.8 Listing jobs (`ls-jobs`)
Algorithm:
1) Resolve workspace and extract session name.
2) `tmux list-windows -t <session> -F "#{window_id}\t#{window_name}"`
3) Filter windows where `window_name.startswith("job:")`.
4) Parse `tag`, `ts_utc`, `job_id` from the window name.
5) For each job window:
   - `tmux list-panes -t <window_id> -F "#{pane_id}\t#{pane_dead}\t#{pane_dead_status}\t#{pane_dead_time}"`
   - Take the first pane record (single-pane is the standard).
6) Derive `state`:
   - `running` if `pane_dead == 0`
   - `exited` if `pane_dead == 1`
7) Return list of `JobInfo`.

Parsing rules:
- Split tmux format output on tabs (`\t`), never spaces.
- Normalize empty strings to `None` for optional numeric fields.

### 7.9 Killing jobs (`kill`)
Supported selectors:
- by `job_id` (preferred; exact match)
- by `tag` (sanitized tag; kill all windows with that tag)
- `--all-jobs` (kill all windows with `job:` prefix)

Algorithm:
1) List job windows as in `ls-jobs`.
2) Select matching windows by requested selector.
3) For each selected window:
   - `tmux kill-window -t <window_id>`
4) Return `KillResult`.

---

## 8. Concurrency and locking

Purpose: prevent multiple processes from racing `tmuxp load`.

### Requirements
- Lock directory: `~/.cache/muxdantic/lock/`
- Lock filename is a safe hash (sha1) of:
  - server selector (`-L`/`-S` values) + session_name
- Use `fcntl.flock(fd, LOCK_EX)`.

Lock scope:
- Held only during:
  - `tmux has-session ...`
  - optional `tmuxp load ...`

---

## 9. Logging (optional JSONL)

### 9.1 CLI flags
- `--log-dir DIR` → default file `<DIR>/<job_id>.jsonl`
- `--log-file PATH` → exact path
(mutually exclusive)

### 9.2 tmux wiring
Before starting the command, attach:
- `tmux pipe-pane -o -t <pane_id> "<python -m muxdantic.logging_sink ...>"`

The sink command must be shell-quoted safely (job_id and path).

### 9.3 Sink module: `python -m muxdantic.logging_sink`
Behavior:
- Read stdin line-by-line.
- Write JSON Lines records to the target file:
  - `ts` (UTC ISO 8601 with `Z`)
  - `job_id`
  - `line` (rstrip newline only)
- Flush frequently (line-buffered).
- Ensure parent directories exist.

Example record:
```json
{"ts":"2026-02-11T16:30:12.123Z","job_id":"XyZ...","line":"hello"}
```

---

## 10. tmux/tmuxp subprocess wrapper requirements

### 10.1 Invocation rules
- Use `subprocess.run([...], text=True, capture_output=True)`.
- Raise a typed error on non-zero return code capturing:
  - program, args, return code, stderr.

### 10.2 Server targeting
All tmux calls must include server args from `TmuxServerArgs.to_tmux_args()`.

### 10.3 tmux targets safety
- Always pass `-t` targets as separate argv elements.
- Treat `window_id` / `pane_id` as opaque strings returned by tmux.
- Never splice untrusted user strings into tmux format strings.

---

## 11. Error handling and diagnostics

### 11.1 Typed exceptions (minimum)
- `MuxdanticUsageError` → exit 2
- `MuxdanticSubprocessError` → exit 1
  - includes: program, args, returncode, stderr

### 11.2 CLI error format
- Print a short, actionable message to stderr.
- Do not print stack traces by default.

---

## 12. Testing requirements

### 12.1 Unit tests (default)
- Tag sanitization edge cases.
- Workspace resolution (dir/file, none found, multiple found).
- Model validation (mutually exclusive flags; log-dir/log-file rules).
- tmux format parsing into `JobInfo` using tab-separated fixtures.

### 12.2 Smoke test (required)
A single test that verifies devenv assumptions without requiring a tmux server:
- `tmux -V` runs
- `tmuxp --version` runs

### 12.3 Integration tests (optional, opt-in)
- Guarded by env var, e.g. `MUXDANTIC_INTEGRATION=1`.
- Use an isolated tmux server via `-L <random-socket>` to avoid touching user’s server.
- Flow:
  1) Create temp workspace pointing to a session name.
  2) `ensure`
  3) `run` success + failure commands
  4) verify via `ls-jobs` and `kill`

---

## 13. Packaging requirements

- Provide a console script entrypoint:
  - `muxdantic = muxdantic.cli:main`
- Keep dependencies minimal (argparse acceptable for MVP).
- Include `py.typed` if shipping typed public APIs.

---

## 14. Security and safety requirements (MVP)

- Tag sanitization is mandatory and enforced centrally.
- Lock filenames must be safe (hashed key).
- Commands accepted as argv (`-- <cmd...>`), not a single shell string.
- When converting argv for tmux `send-keys`, use `shlex.join`.
- Avoid embedding raw user strings into the `pipe-pane` command; quote arguments safely.
