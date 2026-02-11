from __future__ import annotations

import pytest

from muxdantic.tags import sanitize_tag


def test_sanitize_tag_collapses_invalid_sequences() -> None:
    assert sanitize_tag(" Build::Release -- main ") == "build-release-main"


def test_sanitize_tag_rejects_empty() -> None:
    with pytest.raises(ValueError, match="at least one alphanumeric"):
        sanitize_tag("---")
