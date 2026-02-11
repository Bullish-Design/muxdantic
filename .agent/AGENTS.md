# AGENTS.md — muxdantic build guide (LLM agent playbook)

This repo builds **muxdantic**: ensure a tmuxp-defined tmux session exists, then spawn **tagged tmux job windows** that are fire-and-forget (auto-remove on success, remain visible on failure) with optional JSONL logging. Source of truth is **tmux**. fileciteturn0file0

## North-star constraints
- **No daemon, no DB**; tmux is the runtime/state/observability surface.
- **Devenv-only**: assume `tmux` + `tmuxp` on `PATH` (declared in `devenv.nix`), plus a tiny pytest smoke check.
- **JSON in/out**: machine-readable stdout, human diagnostics to stderr.
- **Tolerant tmuxp parsing**: only what we need (session name), allow unknown keys.
- **Predictable defaults**: success auto-cleans; failure remains visible by default.

## What to build (MVP scope)
CLI commands:
- `ensure <workspace> [tmux-server-args]`
- `run <workspace> --tag TAG [opts] -- <cmd...>`
- `ls-jobs <workspace>`
- `kill <workspace> (--job-id ID | --tag TAG | --all-jobs)`

Key behaviors:
- Workspace resolution: config path OR directory containing exactly one of `.tmuxp.yaml/.yml/.json`.
- Job == **one tmux window** named: `job:<tag>:<utc_ts>:<job_id>`.
- Tag sanitization: lowercase; allow `[a-z0-9._-]`; invalid runs → `-`; trim edges; error if empty.
- Default lifecycle: `remain-on-exit=failed` (success removes window; failure stays).
- Optional JSONL logs via `tmux pipe-pane -o` → tiny Python sink, file keyed by `job_id`.

Exit codes:
- `0` success
- `1` operational failure (tmux/tmuxp subprocess errors)
- `2` usage/validation error

## Repository layout (recommended)
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
tests/
  test_smoke_env.py
  test_workspace.py
  test_tag_sanitize.py
  test_models.py
  test_tmux_format_parsing.py
  test_integration_tmux.py   # optional, guarded
pyproject.toml
README.md
```

## Agent roles and handoffs

### Agent A — Architect & contracts
**Owns:** public API shapes, models, CLI contract, file layout, exit codes, and invariants.

Deliverables:
- `models.py` with Pydantic v2 models: `TmuxServerArgs`, `EnsureRequest/Result`, `RunRequest`, `JobRef`, `JobInfo`.
- `errors.py` defining typed exceptions mapping to exit codes.
- CLI contract doc (see `SKILLS/CLI_CONTRACT.md`).

Acceptance:
- All command outputs are valid JSON (stdout).
- Validation errors are consistent and exit `2`.

Read first:
- `SKILLS/CORE_MODELS.md`
- `SKILLS/CLI_CONTRACT.md`

---

### Agent B — Workspace resolver & tmuxp parsing
**Owns:** deterministic workspace discovery + extracting `session_name` from tmuxp config (YAML/JSON).

Deliverables:
- `workspace.py` with:
  - `resolve_workspace(path: Path) -> Path`
  - `load_tmuxp_config(path: Path) -> dict`
  - `extract_session_name(cfg: dict) -> str` (tolerant)
- Unit tests for resolution and parsing.

Acceptance:
- Errors match concept: “none found” vs “more than one found” listing candidates.
- Handles `.tmuxp.yaml`, `.tmuxp.yml`, `.tmuxp.json`.

Read first:
- `SKILLS/WORKSPACE_RESOLUTION.md`

---

### Agent C — tmux integration primitives
**Owns:** subprocess wrapper for `tmux`/`tmuxp`, server targeting (`-L/-S`), and parsing `tmux` format output.

Deliverables:
- `tmux.py` with:
  - `tmux(args, server: TmuxServerArgs) -> CompletedProcess`
  - `tmuxp(args, server: TmuxServerArgs) -> CompletedProcess`
  - helpers for `has_session`, `new_window`, `list_windows`, `list_panes`, `kill_window`, `set_window_option`, `pipe_pane`, `send_keys`
- Parsing helpers used by `ls-jobs`.

Acceptance:
- Server args are passed through consistently.
- No pane-content scraping; only format variables.

Read first:
- `SKILLS/TMUX_COMMANDS.md`

---

### Agent D — Ensure + locking
**Owns:** locking and `ensure` implementation (race-safe tmuxp load).

Deliverables:
- `locking.py` with an `flock`-based context manager and lock-key hashing.
- `jobs.py` / `ensure` function: lock only around `has-session` + `tmuxp load -d --yes`.

Acceptance:
- Concurrency-safe: two processes racing won’t double-load.
- Lock filename includes server selector + session_name (via stable hash).

Read first:
- `SKILLS/LOCKING.md`

---

### Agent E — Job run lifecycle + discovery + kill
**Owns:** `run`, `ls-jobs`, `kill` logic and job naming / parsing.

Deliverables:
- `jobs.py` implementing:
  - `run_job(...) -> JobRef`
  - `list_jobs(...) -> list[JobInfo]`
  - `kill_jobs(...) -> ...`
- Tag sanitize and job-name parsing helpers with tests.

Acceptance:
- Default: window disappears on success, remains on failure.
- `ls-jobs` returns required fields (including pane dead status/time) using tmux variables.
- `kill` targets window(s) precisely by job_id/tag/all.

Read first:
- `SKILLS/JOB_LIFECYCLE.md`
- `SKILLS/SECURITY_SAFETY.md`

---

### Agent F — Logging sink
**Owns:** `--log-dir/--log-file` behavior and JSONL sink invoked via `tmux pipe-pane`.

Deliverables:
- `logging_sink.py` module runnable via `python -m muxdantic.logging_sink ...`
- Tests for sink formatting (pure unit tests).
- Integration hook in `run_job` to attach pipe-pane before starting command.

Acceptance:
- Produces JSON Lines records: `{ts, job_id, line}` with UTC timestamps.
- Log filename default: `<log_dir>/<job_id>.jsonl`.

Read first:
- `SKILLS/LOGGING_JSONL.md`

---

### Agent G — Tests & packaging glue
**Owns:** pytest setup, smoke tests, optional integration tests, and packaging/entrypoints.

Deliverables:
- `test_smoke_env.py` verifying `tmux -V` and `tmuxp --version` run.
- Guarded integration tests that skip if `TMUX` env requirements aren’t met.
- `pyproject.toml` console script entrypoint.

Acceptance:
- Unit tests run fast and deterministic.
- Integration tests are opt-in (skip by default if no tmux server).

Read first:
- `SKILLS/TEST_STRATEGY.md`

## Milestones (order of implementation)
1. **Scaffold & contracts:** models, errors, CLI skeleton (no tmux yet).
2. **Workspace + session parsing:** resolution and session_name extraction.
3. **tmux wrappers:** server targeting + `has-session`.
4. **ensure:** locking + `tmuxp load -d --yes`.
5. **run:** window create + remain-on-exit + send-keys; print `JobRef` JSON.
6. **ls-jobs:** list job windows + parse into `JobInfo` JSON array.
7. **kill:** sugar over `tmux kill-window` by job id/tag/all.
8. **logging:** pipe-pane + JSONL sink.
9. **Docs/README:** examples, troubleshooting, JSON schemas.

## Definition of done
- All commands implemented with stated defaults and exit codes.
- All JSON schemas stable and covered by tests.
- No background process, no data store, no custom scheduler.
- Works in devenv-managed environments with assumed tmux/tmuxp availability.
