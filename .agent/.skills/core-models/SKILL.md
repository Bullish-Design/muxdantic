# .agent/.skills/core-models/SKILL.md — Pydantic models & validation

## Goal
Keep the library API and CLI output stable by defining explicit **Pydantic v2** models for all requests/results.

## Models (recommended)
- `TmuxServerArgs`
  - `socket_name: str | None`  (for `-L`)
  - `socket_path: str | None`  (for `-S`)
  - method: `to_tmux_args() -> list[str]` returning `["-L", name]` and/or `["-S", path]` in a consistent order.
- `EnsureRequest`: `workspace: Path`, `server: TmuxServerArgs`
- `EnsureResult`: `workspace: Path`, `session_name: str`, `created: bool`
- `RunRequest`:
  - `workspace: Path`, `server: TmuxServerArgs`, `tag: str`, `cmd: list[str]`
  - lifecycle flags: `keep: bool`, `rm: bool`, `keep_on_fail: bool` (default True)
  - logging: `log_dir: Path | None`, `log_file: Path | None`
- `JobRef` (printed by `run`):
  - `job_id: str`, `tag: str`, `ts_utc: str`
  - `session_name: str`, `window_id: str`, `window_name: str`, `pane_id: str`
  - `log_file: Path | None`
- `JobInfo` (returned by `ls-jobs`):
  - all fields from concept: `job_id`, `tag`, `ts_utc`, `session_name`, `window_id`, `window_name`, `pane_id`,
    `pane_dead`, `pane_dead_status`, `pane_dead_time`
  - optional derived: `state: Literal["running","exited"]`

## Validation rules
- Tag sanitization returns a **validated** tag; error if empty after sanitize.
- `--keep` and `--rm` mutually exclusive (usage error).
- `--log-dir` and `--log-file` mutually exclusive (usage error).

## Parsing external configs
For tmuxp config models, prefer not to fully model the schema. Keep it as `dict` and extract `session_name` in a tolerant way.
If you do define a model, set `model_config = ConfigDict(extra="allow")`.

## JSON output
For CLI output:
- Use `model.model_dump(mode="json")` (Pydantic v2) and `json.dumps(..., separators=(",",":"))`.
- Ensure paths serialize to strings (use `json_encoders` or pre-coerce to `str`).
