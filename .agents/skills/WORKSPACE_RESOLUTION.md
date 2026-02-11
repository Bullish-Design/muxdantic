# SKILLS/WORKSPACE_RESOLUTION.md — deterministic workspace resolution

## Inputs accepted
- A direct tmuxp config file path, OR
- A directory containing exactly one of:
  - `.tmuxp.yaml`
  - `.tmuxp.yml`
  - `.tmuxp.json`

## Rules
1. If input is a file: accept only the above suffixes; return the file path.
2. If input is a directory: look for the three filenames; error if none or more than one.
3. Error messages:
   - None found: mention the directory and expected filenames.
   - More than one: list candidate paths.

## Session name extraction
- Load YAML via `yaml.safe_load`.
- Load JSON via `json.load`.
- Extract `session_name` as:
  - `cfg.get("session_name")` OR `cfg.get("session")` (be tolerant if you want).
- If missing, error (usage/validation) because ensure/run depend on it.

## Tests
- Directory with 0 configs → usage error.
- Directory with 2 configs → usage error listing both.
- File path with wrong name → usage error.
- YAML/JSON both supported.
