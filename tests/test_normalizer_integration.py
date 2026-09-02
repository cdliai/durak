import importlib.util

import pytest
from durak.normalizer import Normalizer

RUST_AVAILABLE = importlib.util.find_spec("durak._durak_core") is not None


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust extension not installed")
def test_end_to_end_integration() -> None:
    """Real integration test."""

    normalizer = Normalizer()
    result = normalizer("İSTANBUL")

    assert result == "istanbul"
