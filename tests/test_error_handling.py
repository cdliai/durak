"""
Unit tests for error handling and input validation in Rust core functions.

Tests that empty input, invalid parameters, and edge cases are handled gracefully
with Python-friendly error messages instead of panics.
"""

import pytest
from durak._durak_core import (
    fast_normalize,
    tokenize_with_offsets,
    lookup_lemma,
    strip_suffixes,
    strip_suffixes_validated,
)


class TestFastNormalizeErrorHandling:
    """Test error handling in fast_normalize."""

    def test_empty_string_raises_value_error(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="Input text cannot be empty"):
            fast_normalize("")

    def test_valid_input_works(self):
        """Valid input should work normally."""
        assert fast_normalize("Merhaba") == "merhaba"
        assert fast_normalize("İSTANBUL") == "istanbul"


class TestTokenizeWithOffsetsErrorHandling:
    """Test error handling in tokenize_with_offsets."""

    def test_empty_string_returns_empty_list(self):
        """Empty string should return empty list (graceful handling)."""
        result = tokenize_with_offsets("")
        assert result == []

    def test_valid_input_works(self):
        """Valid input should work normally."""
        result = tokenize_with_offsets("Merhaba dünya!")
        assert len(result) == 3
        assert result[0][0] == "Merhaba"


class TestLookupLemmaErrorHandling:
    """Test error handling in lookup_lemma."""

    def test_empty_string_raises_value_error(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="Input word cannot be empty"):
            lookup_lemma("")

    def test_valid_input_works(self):
        """Valid input should work normally."""
        # Known word
        result = lookup_lemma("kitaplar")
        assert result == "kitap"
        
        # Unknown word
        result = lookup_lemma("nonexistent")
        assert result is None


class TestStripSuffixesErrorHandling:
    """Test error handling in strip_suffixes."""

    def test_empty_string_raises_value_error(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="Input word cannot be empty"):
            strip_suffixes("")

    def test_valid_input_works(self):
        """Valid input should work normally."""
        assert strip_suffixes("kitaplar") == "kitap"


class TestStripSuffixesValidatedErrorHandling:
    """Test error handling in strip_suffixes_validated."""

    def test_empty_string_raises_value_error(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError, match="Input word cannot be empty"):
            strip_suffixes_validated("")

    def test_zero_min_root_length_raises_value_error(self):
        """min_root_length=0 should raise ValueError."""
        with pytest.raises(ValueError, match="min_root_length must be greater than 0"):
            strip_suffixes_validated("kitap", min_root_length=0)

    def test_valid_input_works(self):
        """Valid input should work normally."""
        result = strip_suffixes_validated("kitaplar", strict=False, min_root_length=2)
        assert result == "kitap"


class TestErrorMessagesQuality:
    """Test that error messages are helpful and Pythonic."""

    def test_error_messages_are_descriptive(self):
        """Error messages should be clear and helpful."""
        try:
            fast_normalize("")
        except ValueError as e:
            assert "empty" in str(e).lower()
            assert "input" in str(e).lower()

    def test_errors_are_python_exceptions(self):
        """Errors should be Python exceptions, not Rust panics."""
        # This test passes if no panic occurs
        try:
            fast_normalize("")
        except Exception as e:
            assert isinstance(e, ValueError)
            # Should NOT be a generic "Rust panic" message


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_whitespace_only_is_valid(self):
        """Whitespace-only input should be treated as valid (not empty)."""
        # fast_normalize should work
        result = fast_normalize(" ")
        assert result == " "
        
        # tokenize_with_offsets should return empty (no tokens)
        result = tokenize_with_offsets("   ")
        assert result == []

    def test_single_character_input(self):
        """Single character input should work."""
        assert fast_normalize("A") == "a"
        assert lookup_lemma("a") is None  # Not in dict, but valid call

    def test_very_long_input(self):
        """Very long input should work without errors."""
        long_text = "Merhaba " * 10000
        result = fast_normalize(long_text)
        assert len(result) == len(long_text)
        
        result = tokenize_with_offsets(long_text)
        assert len(result) > 0
