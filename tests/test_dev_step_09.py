from __future__ import annotations

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent
README = REPO_ROOT / "README.md"


def _extract_fenced_blocks(readme_text: str, language: str) -> list[str]:
    blocks: list[str] = []
    start = f"```{language}"
    cursor = 0
    while True:
        begin = readme_text.find(start, cursor)
        if begin == -1:
            return blocks
        begin += len(start)
        end = readme_text.find("```", begin)
        if end == -1:
            return blocks
        blocks.append(readme_text[begin:end].strip())
        cursor = end + 3


def test_dev_step_09_readme_exists_and_covers_required_sections() -> None:
    assert README.exists(), "README.md must exist"

    text = README.read_text(encoding="utf-8")

    required_markers = [
        "# muxdantic",
        "## CLI quickstart",
        "### Ensure a session exists",
        "### Run a tagged job",
        "### List jobs",
        "### Kill jobs",
        "### Logging output (`--log-dir` and `--log-file`)",
        "## Exit codes",
        "## Troubleshooting",
        "tmux server routing flags",
    ]
    for marker in required_markers:
        assert marker in text, f"README missing expected section marker: {marker}"


def test_dev_step_09_readme_json_examples_match_contract_shapes() -> None:
    text = README.read_text(encoding="utf-8")
    json_blocks = _extract_fenced_blocks(text, "json")
    assert json_blocks, "README should include JSON examples"

    parsed: list[dict | list] = []
    for block in json_blocks:
        parsed.append(json.loads(block))

    ensure_payload = next((p for p in parsed if isinstance(p, dict) and "created" in p), None)
    assert ensure_payload is not None, "README must include ensure success JSON"
    assert {"workspace", "session_name", "created"}.issubset(ensure_payload.keys())

    run_payload = next((p for p in parsed if isinstance(p, dict) and "job_id" in p and "pane_id" in p), None)
    assert run_payload is not None, "README must include run success JSON"
    assert {
        "job_id",
        "tag",
        "ts_utc",
        "session_name",
        "window_id",
        "window_name",
        "pane_id",
        "log_file",
    }.issubset(run_payload.keys())

    ls_payload = next((p for p in parsed if isinstance(p, list) and p and isinstance(p[0], dict) and "state" in p[0]), None)
    assert ls_payload is not None, "README must include ls-jobs success JSON"
    job_info = ls_payload[0]
    assert {
        "job_id",
        "tag",
        "ts_utc",
        "session_name",
        "window_id",
        "window_name",
        "pane_id",
        "pane_dead",
        "pane_dead_status",
        "pane_dead_time",
        "state",
    }.issubset(job_info.keys())

    kill_payload = next((p for p in parsed if isinstance(p, dict) and set(p.keys()) == {"killed"}), None)
    assert kill_payload is not None, "README must include kill success JSON"

    sink_payload = next((p for p in parsed if isinstance(p, dict) and {"ts", "job_id", "line"}.issubset(p.keys())), None)
    assert sink_payload is not None, "README must include logging sink JSONL line example"


def test_dev_step_09_readme_includes_tmuxp_workspace_example() -> None:
    text = README.read_text(encoding="utf-8")
    yaml_blocks = _extract_fenced_blocks(text, "yaml")
    assert yaml_blocks, "README must include a tmuxp workspace YAML snippet"

    assert any("session_name:" in block for block in yaml_blocks), "tmuxp snippet must include session_name"
