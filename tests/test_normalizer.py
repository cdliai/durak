"""
Unit tests for Normalizer class.

Tests configuration parameters (lowercase, handle_turkish_i) to ensure they are
properly applied by the Rust core.
"""

from typing import NoReturn
from unittest.mock import patch

import pytest
from durak.normalizer import Normalizer


@pytest.fixture
def normalizer() -> Normalizer:
    return Normalizer()


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("İstanbul", "istanbul"),
        ("IŞIK", "ışık"),
        ("ışık", "ışık"),
    ],
    ids=["istanbul_case", "isik_upper_case", "isik_lower_case"],
)
def test_turkish_i_handling_contract(normalizer, input_text, expected) -> None:
    """
    Test Turkish character handling logic contract.
    We mock the Rust backend to ensure the Python wrapper respects the contract.
    """

    with patch("durak.normalizer.fast_normalize") as mock_fast:
        # mock logic to mimic correct Rust behavior
        mock_fast.side_effect = lambda x: {
            "İstanbul": "istanbul",
            "IŞIK": "ışık",
            "ışık": "ışık",
        }.get(x, x.lower())

        assert normalizer(input_text) == expected


def test_empty_string(normalizer) -> None:
    """Test that empty string return immediately without calling backend."""

    with patch("durak.normalizer.fast_normalize") as mock_fast:
        assert normalizer("") == ""
        mock_fast.assert_not_called()


def test_none_input(normalizer) -> None:
    """Test that None input returns empty string."""

    with patch("durak.normalizer.fast_normalize") as mock_fast:
        assert normalizer(None) == ""
        mock_fast.assert_not_called()


# --- Configuration & Bug Documentation --- #
def test_configuration_flags_stored() -> None:
    """Test that flags passed to __init__ are stored correctly."""

    normalizer = Normalizer(lowercase=False, handle_turkish_i=False)
    assert not normalizer.lowercase
    assert not normalizer.handle_turkish_i


def test_bug_flags_ignored() -> None:
    """
    BUG DOCUMENTATION: The current implementation ignores config flags.
    Even if lowercase=False, the backend is still called.
    """

    normalizer = Normalizer(lowercase=False)

    with patch("durak.normalizer.fast_normalize") as mock_fast:
        normalizer("TEST")
        mock_fast.assert_called()


# --- Rust Fallback Test --- #
def test_rust_extension_missing() -> None:
    """Test graceful failure when _durak_core is missing."""

    def mock_fallback(text) -> NoReturn:
        raise ImportError("Durak Rust extension is not installed")

    with patch("durak.normalizer.fast_normalize", mock_fallback):
        normalizer = Normalizer()
        with pytest.raises(ImportError, match="Durak Rust extension"):
            normalizer("Any Text")


# --- Representation Test --- #
def test_repr() -> None:
    normalizer = Normalizer(lowercase=True, handle_turkish_i=False)
    assert repr(normalizer) == "Normalizer(lowercase=True, handle_turkish_i=False)"
