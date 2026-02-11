# muxdantic

`muxdantic` is a small Python library + CLI for tmux/tmuxp workflows:

- **ensure** a tmux session exists from a tmuxp workspace file
- **run** fire-and-forget commands as tagged tmux job windows
- **list** and **kill** job windows created by muxdantic
- optionally stream pane output into **JSONL logs**

tmux remains the runtime and source of truth. muxdantic is the glue layer.

## Installation

```bash
pip install muxdantic
```

## Workspace file conventions

You can pass either:

- a direct workspace file path (`.tmuxp.yaml`, `.tmuxp.yml`, or `.tmuxp.json`), or
- a directory containing exactly one of those filenames.

Minimal example (`.tmuxp.yaml`):

```yaml
session_name: dev
windows:
  - window_name: shell
    panes:
      - echo "ready"
```

## CLI quickstart

### Ensure a session exists

```bash
muxdantic ensure .
```

Success JSON shape:

```json
{"workspace":"/path/to/.tmuxp.yaml","session_name":"dev","created":false}
```

### Run a tagged job

`--` is required to separate muxdantic arguments from the command argv.

```bash
muxdantic run . --tag build -- python -m pytest -q
```

Success JSON shape (`JobRef`):

```json
{
  "job_id":"a1b2c3d4e5f6",
  "tag":"build",
  "ts_utc":"20260211T143012Z",
  "session_name":"dev",
  "window_id":"@9",
  "window_name":"job:build:20260211T143012Z:a1b2c3d4e5f6",
  "pane_id":"%11",
  "log_file":null
}
```

Lifecycle flags:

- `--keep`: keep window after command exits
- `--rm`: always remove window on exit
- `--keep-on-fail` / `--no-keep-on-fail`: control failure visibility (default keeps failures)

### List jobs

```bash
muxdantic ls-jobs .
```

Success JSON shape (`list[JobInfo]`):

```json
[
  {
    "job_id":"a1b2c3d4e5f6",
    "tag":"build",
    "ts_utc":"20260211T143012Z",
    "session_name":"dev",
    "window_id":"@9",
    "window_name":"job:build:20260211T143012Z:a1b2c3d4e5f6",
    "pane_id":"%11",
    "pane_dead":0,
    "pane_dead_status":null,
    "pane_dead_time":null,
    "state":"running"
  }
]
```

### Kill jobs

Choose one selector:

- `--job-id <id>`
- `--tag <tag>`
- `--all-jobs`

```bash
muxdantic kill . --tag build
```

Success JSON shape:

```json
{"killed":["@9"]}
```

### Logging output (`--log-dir` and `--log-file`)

```bash
muxdantic run . --tag lint --log-dir ./logs -- ruff check .
```

or:

```bash
muxdantic run . --tag lint --log-file ./logs/lint.jsonl -- ruff check .
```

Each line in the JSONL sink is structured as:

```json
{"ts":"2026-02-11T14:30:12.123456Z","job_id":"a1b2c3d4e5f6","line":"stdout/stderr line"}
```

## tmux server targeting

All commands support tmux server routing flags:

- `-L NAME` / `--socket-name NAME`
- `-S PATH` / `--socket-path PATH`

Example:

```bash
muxdantic ensure . -L myserver
```

## Python API

Core functions:

- `ensure(req: EnsureRequest) -> EnsureResult`
- `run(req: RunRequest) -> JobRef`
- `list_jobs(workspace: Path, server: TmuxServerArgs) -> list[JobInfo]`
- `kill(workspace: Path, server: TmuxServerArgs, *, job_id: str | None, tag: str | None, all_jobs: bool) -> KillResult`

Example:

```python
from pathlib import Path

from muxdantic.jobs import list_jobs, run
from muxdantic.models import RunRequest, TmuxServerArgs

server = TmuxServerArgs(socket_name="mx")
job = run(
    RunRequest(
        workspace=Path(".tmuxp.yaml"),
        server=server,
        tag="build",
        cmd=["python", "-m", "pytest", "-q"],
    )
)

jobs = list_jobs(Path(".tmuxp.yaml"), server)
print(job.model_dump(mode="json"))
print([entry.model_dump(mode="json") for entry in jobs])
```

## Exit codes

- `0`: success
- `1`: operational subprocess errors (`tmux`, `tmuxp`)
- `2`: usage or validation errors

## Troubleshooting

### Wrong session name or missing `session_name`

Ensure your tmuxp config includes `session_name` (or `session`) with a non-empty string.

### tmux server mismatch (`-L` / `-S`)

If jobs appear in a different server than expected, make sure all commands use the same `-L`/`-S` values.

### Logs not where expected

- `--log-file` writes to exactly that path
- `--log-dir` writes `<job_id>.jsonl` inside that directory
- if neither flag is set, no pane logging is attached
