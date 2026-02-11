# Area 09 — Documentation (README + examples)

## Goal
Document the CLI and library API with practical examples and troubleshooting tips.

## Owned files (exclusive)
- `README.md`
- `CHANGELOG.md` (optional)

## Depends on
- All functional areas (01–07)

## README outline (suggested)
- What muxdantic does (ensure + run job windows)
- Installation (brief)
- CLI examples:
  - ensure
  - run with tag
  - ls-jobs
  - kill
  - logging examples (`--log-dir`)
- JSON schemas and exit codes
- Troubleshooting:
  - wrong session name
  - tmux server targeting (-L/-S)
  - where logs go

## Acceptance criteria
- README examples match actual output JSON shapes.
- Includes a small tmuxp workspace example snippet.
