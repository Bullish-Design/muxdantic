# File ownership map (MVP)

The purpose of this map is to keep each parallel area mostly editing different files.

> Rule of thumb: if a file is “owned” by one area, other areas should avoid editing it unless absolutely necessary.

## Owned files by area

### Area 00 — Baseline scaffold
- `pyproject.toml`
- `muxdantic/__init__.py` (initial minimal exports only; later changes via Integration checklist)
- `muxdantic/py.typed`
- `.gitignore` (if needed)
- `tests/conftest.py` (if needed)

### Area 01 — Contracts (models, errors, shared utils)
- `muxdantic/models.py`
- `muxdantic/errors.py`
- `muxdantic/jsonio.py` (JSON stdout helpers; optional but recommended)

### Area 02 — Workspace resolution + tmuxp parsing
- `muxdantic/workspace.py`
- `tests/test_workspace_resolution.py`

### Area 03 — tmux/tmuxp wrapper + format parsing helpers
- `muxdantic/tmux.py`
- `tests/test_tmux_format_parsing.py`

### Area 04 — Locking + ensure
- `muxdantic/locking.py`
- `muxdantic/ensure.py`
- `tests/test_locking.py`
- `tests/test_ensure_unit.py` (pure unit tests; integration optional)

### Area 05 — Jobs (run / list-jobs / kill)
- `muxdantic/jobs.py`
- `muxdantic/tags.py` (tag sanitize + parsing helpers; can also live in models validators)
- `tests/test_tag_sanitize.py`
- `tests/test_jobs_naming_parsing.py`

### Area 06 — Logging (JSONL sink + pipe-pane wiring)
- `muxdantic/logging_sink.py`
- `muxdantic/logging.py` (pipe-pane command builder + helpers)
- `tests/test_logging_sink.py`

### Area 07 — CLI wiring
- `muxdantic/cli.py`
- `tests/test_cli_smoke.py` (argparse help / basic exit code behavior; optional)

### Area 08 — Tests & quality (suite glue, smoke + integration)
- `tests/test_smoke_env.py` (required smoke test)
- `tests/test_integration_tmux.py` (opt-in, guarded)
- `tests/test_models_validation.py` (if Area 01 prefers to keep tests separate, this file can be owned here)

### Area 09 — Docs
- `README.md`
- `CHANGELOG.md` (optional)
- `docs/*` (optional)

## Shared files (edit only in Integration)
- `muxdantic/__init__.py` (final API exports)
- `pyproject.toml` (console script entrypoint)
