# .agent/.skills/security-safety/SKILL.md — sanitization, quoting, and sharp edges

## Threat model (lightweight)
muxdantic is for local dev orchestration, but still avoid obvious foot-guns:
- unsafe filenames from tags
- accidental tmux target injection
- command quoting surprises

## Tag sanitization is mandatory
- Only sanitized tags are used in window names and (optionally) filenames.
- Never allow empty tags.

## Lock filenames
- Use a hash of (server selector + session name) to avoid path injection and length issues.

## Command execution
- Prefer receiving the command as argv (`-- <cmd...>`), not a single shell string.
- When sending into tmux with `send-keys`, convert argv to a shell-safe string using `shlex.join(cmd)`.
- Avoid embedding raw user strings into a `pipe-pane` command; pass file paths and job_id as arguments.

## tmux targets
- Always pass `-t` targets as their own argv elements (no concatenation).
- Treat `window_id` and `pane_id` as opaque strings returned by tmux.
