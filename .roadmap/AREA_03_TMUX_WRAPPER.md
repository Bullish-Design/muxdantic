# Area 03 — tmux/tmuxp subprocess wrappers + format parsing helpers

## Goal
Provide a consistent subprocess wrapper for `tmux` and `tmuxp`, including server targeting (`-L`, `-S`) and safe parsing of tab-separated format output.

## Owned files (exclusive)
- `muxdantic/tmux.py`
- `tests/test_tmux_format_parsing.py`

## Depends on
- Area 00 scaffold
- Area 01 (models + `MuxdanticSubprocessError`)

## Provides to other areas
- `tmux(args: list[str], server: TmuxServerArgs) -> str` (stdout)
- `tmuxp(args: list[str], server: TmuxServerArgs) -> str`
- helper operations:
  - `has_session(session_name)`
  - `new_window(session_name, window_name)`
  - `set_window_option(window_id, option, value)`
  - `list_windows(session_name) -> list[(window_id, window_name)]`
  - `list_panes(target) -> list[pane tuple]`
  - `pipe_pane(pane_id, cmd)`
  - `send_keys(pane_id, string)`
  - `kill_window(window_id)`

## Implementation notes (to reduce later merge conflicts)
- Provide “thin” functions; higher-level logic lives in `ensure.py` and `jobs.py`.
- Parse `\t` separated output only; no scraping pane content.
- Keep format strings centrally defined in this module.

## Tests
- Provide fixtures for parsing (strings containing tabs) to structured fields.
- Avoid requiring a live tmux server in unit tests.

## Acceptance criteria
- Non-zero return codes raise `MuxdanticSubprocessError` capturing stderr.
- Server args are consistently applied to every tmux/tmuxp invocation.
