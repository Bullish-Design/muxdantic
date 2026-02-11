from __future__ import annotations

import ast
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parent.parent
SMOKE_TEST = REPO_ROOT / "tests" / "test_smoke_env.py"


class _CommandVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.commands: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            cmd = node.args[0].value.strip()
            if cmd:
                self.commands.add(cmd)
        elif node.args and isinstance(node.args[0], (ast.List, ast.Tuple)):
            first = node.args[0].elts[0] if node.args[0].elts else None
            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                self.commands.add(first.value)
        self.generic_visit(node)


class _ImportedNameVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.imported: set[str] = set()

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        for alias in node.names:
            self.imported.add(alias.asname or alias.name)


class _HelperCallVisitor(ast.NodeVisitor):
    def __init__(self, helper_names: set[str]) -> None:
        self.helper_names = helper_names
        self.used_helpers: set[str] = set()

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name) and node.func.id in self.helper_names:
            self.used_helpers.add(node.func.id)
        self.generic_visit(node)


def _module_ast(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _extract_commands(path: Path) -> set[str]:
    visitor = _CommandVisitor()
    visitor.visit(_module_ast(path))
    return visitor.commands


def test_dev_step_08_smoke_module_exists_and_is_importable() -> None:
    assert SMOKE_TEST.exists(), "tests/test_smoke_env.py must exist"

    source = SMOKE_TEST.read_text(encoding="utf-8")
    ast.parse(source, filename=str(SMOKE_TEST))


def test_dev_step_08_smoke_checks_cover_tmux_and_tmuxp() -> None:
    assert SMOKE_TEST.exists(), "tests/test_smoke_env.py must exist"

    smoke_commands = _extract_commands(SMOKE_TEST)
    required_fragments = {"tmux -V", "tmuxp --version"}

    if all(any(fragment in cmd for cmd in smoke_commands) for fragment in required_fragments):
        return

    smoke_ast = _module_ast(SMOKE_TEST)
    imported_visitor = _ImportedNameVisitor()
    imported_visitor.visit(smoke_ast)

    helper_calls = _HelperCallVisitor(imported_visitor.imported)
    helper_calls.visit(smoke_ast)

    helper_paths = [
        p
        for p in (REPO_ROOT / "tests").glob("*.py")
        if p.name not in {"__init__.py", "test_smoke_env.py"}
    ]

    helper_commands: set[str] = set()
    for helper_path in helper_paths:
        helper_ast = _module_ast(helper_path)
        defined_helpers = {
            node.name
            for node in helper_ast.body
            if isinstance(node, ast.FunctionDef) and node.name in helper_calls.used_helpers
        }
        if defined_helpers:
            helper_commands |= _extract_commands(helper_path)

    combined = smoke_commands | helper_commands
    missing = [fragment for fragment in required_fragments if not any(fragment in cmd for cmd in combined)]
    assert not missing, f"Smoke checks must cover required binaries; missing checks for: {', '.join(sorted(missing))}"


def test_dev_step_08_integration_tests_are_opt_in() -> None:
    integration_tests = sorted((REPO_ROOT / "tests").glob("test_integration*.py"))
    if not integration_tests:
        pytest.skip("No integration tests present yet.")

    for path in integration_tests:
        source = path.read_text(encoding="utf-8")
        assert "MUXDANTIC_INTEGRATION" in source, f"{path.name} must guard execution using MUXDANTIC_INTEGRATION"
        assert (
            "pytest.mark.skipif" in source or "pytest.skip" in source
        ), f"{path.name} must skip by default unless MUXDANTIC_INTEGRATION=1"
