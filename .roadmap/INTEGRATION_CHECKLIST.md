# Integration checklist (merge order + conflict-avoidance)

## Merge order (recommended)
1. Area 00 — Baseline scaffold
2. Area 01 — Contracts (models + errors)
3. Area 02 — Workspace
4. Area 03 — tmux wrapper
5. Area 04 — Locking + ensure
6. Area 05 — Jobs
7. Area 06 — Logging
8. Area 08 — Tests & quality (smoke + integration)
9. Area 07 — CLI wiring (late, to avoid conflicts)
10. Area 09 — Docs

## One-time “shared file” edits (do centrally)
These files are common conflict hotspots; keep changes centralized:
- `muxdantic/__init__.py`
  - final exports: `ensure`, `run`, `list_jobs`, `kill`
- `pyproject.toml`
  - console script entrypoint: `muxdantic = muxdantic.cli:main`
  - dependencies list consolidation

## Final review checks
- `pytest` passes (including smoke test)
- `muxdantic ensure ...` prints JSON object with `created`
- `muxdantic run ... -- <cmd>` prints JobRef JSON and creates a tmux window
- `muxdantic ls-jobs ...` prints JSON array of JobInfo
- `muxdantic kill ...` prints killed window IDs
- Logging (when enabled) writes JSONL lines with UTC timestamps
