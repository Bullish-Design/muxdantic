from importlib.util import find_spec


def test_step_00_scaffold_exists() -> None:
    assert find_spec("muxdantic") is not None
