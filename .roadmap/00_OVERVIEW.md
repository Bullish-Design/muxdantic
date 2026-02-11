# Parallel Development Areas for muxdantic (MVP)

This document set splits the SPEC-defined MVP into **development areas** that can be implemented in parallel with **minimal file overlap**, to reduce git merge conflicts.

## How to use this plan
- Create one branch per area (e.g., `area-02-workspace`).
- Each area **owns** a set of files; avoid editing files owned by other areas.
- If you must change an interface in another area’s owned files, open a small PR and let that area’s owner apply it.

## Directory + file ownership strategy (conflict minimizer)
- Each area owns **distinct Python modules** under `muxdantic/`.
- Tests are split by feature into **separate test files** so parallel work doesn’t collide.
- Only the **Integration area** edits `muxdantic/cli.py` once submodules are ready.

## Dependency graph (high level)
Area 00 (Baseline scaffold)
  ├─ Area 01 (Contracts: models + errors + JSON helpers)
  ├─ Area 02 (Workspace resolution + tmuxp parsing)
  ├─ Area 03 (tmux/tmuxp subprocess wrapper + format parsing)
  ├─ Area 04 (Locking + ensure implementation)
  ├─ Area 05 (Jobs: run/list/kill, naming, lifecycle)
  ├─ Area 06 (Logging: JSONL sink + pipe-pane wiring)
  ├─ Area 08 (Tests suite glue + optional integration tests)
  └─ Area 07 (CLI wiring)  ← should land late to avoid conflicts
        └─ Area 09 (Docs/README)

## Area index
- [AREA_00_BASELINE_SCAFFOLD.md](./AREA_00_BASELINE_SCAFFOLD.md)
- [AREA_01_CONTRACTS_MODELS_ERRORS.md](./AREA_01_CONTRACTS_MODELS_ERRORS.md)
- [AREA_02_WORKSPACE_RESOLUTION.md](./AREA_02_WORKSPACE_RESOLUTION.md)
- [AREA_03_TMUX_WRAPPER.md](./AREA_03_TMUX_WRAPPER.md)
- [AREA_04_LOCKING_AND_ENSURE.md](./AREA_04_LOCKING_AND_ENSURE.md)
- [AREA_05_JOBS_RUN_LIST_KILL.md](./AREA_05_JOBS_RUN_LIST_KILL.md)
- [AREA_06_LOGGING_JSONL.md](./AREA_06_LOGGING_JSONL.md)
- [AREA_07_CLI_WIRING.md](./AREA_07_CLI_WIRING.md)
- [AREA_08_TESTS_AND_QUALITY.md](./AREA_08_TESTS_AND_QUALITY.md)
- [AREA_09_DOCS_README.md](./AREA_09_DOCS_README.md)

## Integration checklist
See: [INTEGRATION_CHECKLIST.md](./INTEGRATION_CHECKLIST.md)
