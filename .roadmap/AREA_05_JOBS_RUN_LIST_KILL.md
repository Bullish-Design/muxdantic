# Area 05 — Jobs: run / ls-jobs / kill (naming + lifecycle)

## Goal
Implement job execution and discovery as tmux windows with deterministic naming and lifecycle defaults.

## Owned files (exclusive)
- `muxdantic/jobs.py`
- `muxdantic/tags.py` (recommended: sanitize + parse helpers)
- `tests/test_tag_sanitize.py`
- `tests/test_jobs_naming_parsing.py`

## Depends on
- Area 00 scaffold
- Area 01 (models + errors)
- Area 02 (session extraction)
- Area 03 (tmux primitives)
- Area 04 (`ensure()`)

## Provides
- `run(req: RunRequest) -> JobRef`
- `list_jobs(workspace: Path, server: TmuxServerArgs) -> list[JobInfo]`
- `kill(workspace: Path, server: TmuxServerArgs, *, job_id: str|None, tag: str|None, all_jobs: bool) -> KillResult`

## Key behaviors to implement
### Job window naming (required)
`job:<tag>:<utc_ts>:<job_id>`
- `<utc_ts>`: `YYYYMMDDThhmmssZ` (UTC)
- `<job_id>`: shortuuid

### Required ordering (run)
1) ensure session exists
2) generate job_id + ts_utc + window_name
3) create detached window
4) capture window_id + pane_id deterministically
5) set `remain-on-exit` per lifecycle policy
6) (optional logging hook) attach pipe-pane before execution (see Area 06)
7) send keys: `exec <shlex.join(cmd)>` + Enter

### Lifecycle policy
- default: `remain-on-exit=failed` (success removed, failure remains)
- `--keep`: `on`
- `--rm`: `off`
- if `keep_on_fail=False` and not keep: `off`

### Listing jobs
- list windows: `#{window_id}\t#{window_name}`
- filter `job:` prefix
- parse tag/ts/job_id from window_name
- list panes first pane: `#{pane_id}\t#{pane_dead}\t#{pane_dead_status}\t#{pane_dead_time}`
- derive state: `running` vs `exited`

### Killing jobs
- list jobs first
- selector precedence: `job_id` exact > `tag` > `all_jobs`
- `tmux kill-window -t <window_id>`

## Tests
- Tag sanitize: invalid chars collapse to `-`, trim, empty -> error
- Job window name parse roundtrip
- tmux output parse fixtures for ls-jobs (tab-separated)

## Merge notes (important)
- Keep logging integration as a **call into `muxdantic/logging.py`** (owned by Area 06) to avoid touching `jobs.py` later:
  - in `jobs.py`, call a helper like `resolve_log_file(req, job_id)` + `attach_pipe_pane(server, pane_id, job_id, log_file)`
  - Area 06 implements those helpers without requiring edits to jobs.py.
