import pytest

from durak.normalizer import Normalizer

try:
    from durak._durak_core import fast_normalize

    RUST_AVAILABLE = True
except ImportError:
    RUST_AVAILABLE = False


@pytest.mark.skipif(not RUST_AVAILABLE, reason="Rust extension not installed")
def test_end_to_end_integration() -> None:
    """Real integration test."""

    normalizer = Normalizer()
    result = normalizer("İSTANBUL")

    assert result == "istanbul"
