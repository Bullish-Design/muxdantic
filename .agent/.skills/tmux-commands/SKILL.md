# .agent/.skills/tmux-commands/SKILL.md — tmux/tmuxp subprocess patterns

## Goals
- One tiny wrapper for running `tmux` and `tmuxp` with consistent server targeting.
- Avoid scraping pane content; use tmux **format variables**.

## Server targeting
- Support `-L <socket-name>` and/or `-S <socket-path>` pass-through.
- Include selector in any lock key / cache key.

## Subprocess wrapper
- Use `subprocess.run([...], text=True, capture_output=True)`.
- Raise a typed error when returncode != 0 including:
  - program name (`tmux`/`tmuxp`), args, return code, stderr.

## Key tmux operations
- `has-session -t <session>`
- `new-window -d -t <session> -n <name>`
- `set-window-option -t <window_id> remain-on-exit <failed|on|off>`
- `list-windows -t <session> -F <fmt>`
- `list-panes -t <window_id> -F <fmt>`
- `pipe-pane -o -t <pane_id> <command>`
- `send-keys -t <pane_id> -- <string> C-m`
- `kill-window -t <window_id>`

## Format strings (suggested)
For windows:
- `#{window_id}\t#{window_name}`

For panes (first pane per job window):
- `#{pane_id}\t#{pane_dead}\t#{pane_dead_status}\t#{pane_dead_time}`

## Parsing tips
- Split on `\t`, not spaces.
- tmux may output empty strings; normalize empty → None for numeric fields where appropriate.
