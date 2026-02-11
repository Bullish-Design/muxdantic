# Area 02 — Workspace resolution + tmuxp config parsing

## Goal
Implement deterministic workspace resolution and session name extraction, tolerant to real-world tmuxp configs.

## Owned files (exclusive)
- `muxdantic/workspace.py`
- `tests/test_workspace_resolution.py`

## Depends on
- Area 00 scaffold
- Area 01 (for `MuxdanticUsageError` preferred; otherwise raise ValueError and let CLI map later)

## Provides to other areas
- `resolve_workspace(path: Path) -> Path`
- `load_tmuxp_config(path: Path) -> dict`
- `extract_session_name(cfg: dict) -> str`

## Steps
1. Implement file-or-directory resolution rules:
   - file path must be one of `.tmuxp.yaml/.yml/.json`
   - directory must contain exactly one of those standard filenames
2. Implement YAML/JSON load:
   - YAML via `yaml.safe_load`
   - JSON via `json.load`
3. Extract `session_name`:
   - required key `session_name`
   - optional tolerance for `session` (if desired)
4. Tests:
   - dir with none found → usage error
   - dir with more than one → usage error listing candidates
   - file with wrong suffix → usage error
   - yaml + json supported

## Acceptance criteria
- All workspace rules match SPEC.
- Error messages are actionable (mention directory + expected filenames; list candidates).

## Merge notes
- Keep all workspace logic in this one module to avoid collision.
