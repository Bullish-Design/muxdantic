# SKILLS/JOB_LIFECYCLE.md — job naming, lifecycle, and discovery

## Job identity
A job is exactly **one tmux window**.

Window name format:
`job:<tag>:<utc_ts>:<job_id>`
- `<utc_ts>`: UTC `YYYYMMDDThhmmssZ`
- `<job_id>`: shortuuid (also used for log filename)

## Tag sanitization
- lowercase
- allow `[a-z0-9._-]`
- invalid runs → `-`
- trim `-` and `_` edges
- error if empty after sanitization

## Lifecycle defaults
Use `remain-on-exit` (window option):
- default: `failed` (success removes, failure remains)
- `--keep`: `on`
- `--rm`: `off`
- `--keep-on-fail` / `--no-keep-on-fail` control whether default is `failed` vs `off` (unless `--keep`).

## Creating the window deterministically
Prefer:
1) `tmux new-window -d -t <session> -n <window_name>`
2) capture `window_id` + `pane_id`
3) set `remain-on-exit`
4) attach logging (pipe-pane) if requested
5) `tmux send-keys` to start the command

This ensures options/log piping are attached before execution begins.

## Discovery (`ls-jobs`)
- List windows, filter `window_name.startswith("job:")`
- Parse `tag/ts/job_id` from window_name
- For each job window, query the first pane for `pane_dead`, `pane_dead_status`, `pane_dead_time`.
- Derive `state`:
  - `running` if `pane_dead == 0`
  - `exited` if `pane_dead == 1`
