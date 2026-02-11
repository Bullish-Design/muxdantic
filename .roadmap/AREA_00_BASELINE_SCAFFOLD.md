# Area 00 — Baseline scaffold (package + minimal skeleton)

## Goal
Create a stable repo skeleton that other areas can build on **without touching the same files**.

## Owned files (exclusive)
- `pyproject.toml`
- `muxdantic/__init__.py`
- `muxdantic/py.typed`
- `tests/` directory scaffolding (empty files ok)

## Upstream dependencies
None.

## Steps
1. Create package layout:
   - `muxdantic/` package directory
   - `tests/` directory
2. Add `pyproject.toml` with:
   - dependencies: `pydantic>=2`, `pyyaml` (and stdlib `json`, etc.)
   - dev deps: `pytest`
   - console script entrypoint placeholder (wire later in Area 07 / Integration)
3. Create `muxdantic/__init__.py`:
   - keep minimal: version + (optionally) re-export models only
4. Add `muxdantic/py.typed` (empty file) to signal typing.
5. Add placeholder module files (empty or minimal) so imports resolve early:
   - `muxdantic/models.py`, `errors.py`, `workspace.py`, `tmux.py`,
     `locking.py`, `ensure.py`, `jobs.py`, `logging.py`, `logging_sink.py`, `cli.py`
   > These placeholders reduce “missing module” noise during parallel work.

## Acceptance criteria
- `pytest` runs (even if it runs 0 tests at this point).
- Importing `import muxdantic` works.
- No area is forced to edit `pyproject.toml` except via Integration.

## Merge notes
- Land this branch first (or merge early), so other branches can rebase onto it and avoid repeated scaffold edits.
