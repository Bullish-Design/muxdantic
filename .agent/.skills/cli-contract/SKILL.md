# .agent/.skills/cli-contract/SKILL.md — CLI design & JSON output

## Goals
- Clear, scriptable CLI with **JSON stdout** and **stderr diagnostics**.
- Provide `--` passthrough for command execution.
- Stable exit codes: 0/1/2.

## Commands
### `muxdantic ensure <workspace> [-L NAME|-S PATH]`
JSON stdout:
```json
{"workspace":"...","session_name":"...","created":false}
```

### `muxdantic run <workspace> --tag TAG [--keep|--rm] [--keep-on-fail|--no-keep-on-fail] [--log-dir DIR|--log-file FILE] [-L/-S] -- <cmd...>`
JSON stdout (JobRef):
```json
{"job_id":"...","tag":"...","ts_utc":"...","session_name":"...","window_id":"...","window_name":"...","pane_id":"...","log_file":"..."}
```

### `muxdantic ls-jobs <workspace> [-L/-S]`
JSON stdout:
```json
[{"job_id":"...","tag":"...","ts_utc":"...","session_name":"...","window_id":"...","window_name":"...","pane_id":"...","pane_dead":0,"pane_dead_status":null,"pane_dead_time":null,"state":"running"}]
```

### `muxdantic kill <workspace> (--job-id ID | --tag TAG | --all-jobs) [-L/-S]`
JSON stdout:
```json
{"killed":["<window_id>", "..."]}
```

## Diagnostics
- Any validation failure prints a short message to stderr and exits 2.
- Any subprocess failure prints: which command failed, return code, and captured stderr; exits 1.

## Implementation notes
- Keep dependencies minimal; `argparse` is fine for v0.
- Always support `-L` and `-S` passthrough and include server selector in lock keys.
