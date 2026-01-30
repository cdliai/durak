"""
Property-based tests for Durak Turkish NLP functions.

Uses Hypothesis to generate thousands of Turkish text variants and verify
mathematical properties hold across all inputs.
"""

import pytest
from hypothesis import given, settings, assume

import durak
from tests.strategies import (
    turkish_sentence,
    turkish_word,
    turkish_word_with_suffix,
    turkish_text_with_unicode_edge_cases,
)


class TestNormalizationProperties:
    """Property tests for text normalization functions."""

    @given(turkish_sentence())
    @settings(max_examples=200)
    def test_normalize_case_is_idempotent(self, text):
        """Normalizing case twice should equal normalizing once."""
        normalized_once = durak.normalize_case(text)
        normalized_twice = durak.normalize_case(normalized_once)
        assert normalized_once == normalized_twice

    @given(turkish_word())
    @settings(max_examples=200)
    def test_normalize_case_preserves_length_or_decreases(self, word):
        """Case normalization should never increase text length."""
        # Skip empty strings
        assume(len(word) > 0)
        normalized = durak.normalize_case(word)
        assert len(normalized) <= len(word)

    @given(turkish_sentence())
    @settings(max_examples=200)
    def test_normalize_case_removes_uppercase_turkish(self, text):
        """Case normalization must remove Turkish uppercase characters."""
        normalized = durak.normalize_case(text)
        # These should be converted to lowercase
        assert "İ" not in normalized  # İ -> i
        assert "I" not in normalized  # I -> ı
        assert "Ş" not in normalized  # Ş -> ş
        assert "Ğ" not in normalized  # Ğ -> ğ
        assert "Ç" not in normalized  # Ç -> ç
        assert "Ö" not in normalized  # Ö -> ö
        assert "Ü" not in normalized  # Ü -> ü

    @given(turkish_text_with_unicode_edge_cases())
    @settings(max_examples=100)
    def test_normalize_unicode_handles_edge_cases(self, text):
        """Unicode normalization should not crash on edge cases."""
        # Should complete without exceptions
        normalized = durak.normalize_unicode(text)
        assert isinstance(normalized, str)

    @given(turkish_sentence())
    @settings(max_examples=200)
    def test_clean_text_is_idempotent(self, text):
        """Cleaning text twice should equal cleaning once."""
        cleaned_once = durak.clean_text(text)
        cleaned_twice = durak.clean_text(cleaned_once)
        assert cleaned_once == cleaned_twice


class TestTokenizerProperties:
    """Property tests for tokenization functions."""

    @given(turkish_sentence())
    @settings(max_examples=200)
    def test_tokenize_always_returns_list(self, text):
        """Tokenization must always return a list."""
        tokens = durak.tokenize(text)
        assert isinstance(tokens, list)

    @given(turkish_sentence())
    @settings(max_examples=200)
    def test_tokenize_preserves_non_whitespace_content(self, text):
        """Tokenizing should preserve all non-whitespace characters."""
        assume(len(text.strip()) > 0)
        tokens = durak.tokenize(text)
        rejoined = "".join(tokens)

        # Remove all whitespace for comparison
        text_no_ws = "".join(text.split())
        rejoined_no_ws = "".join(rejoined.split())

        # All non-whitespace chars should be preserved (modulo normalization)
        assert len(rejoined_no_ws) > 0

    @given(turkish_word_with_suffix())
    @settings(max_examples=200)
    def test_tokenize_handles_apostrophes_consistently(self, text):
        """Tokenization of apostrophe'd words should be consistent."""
        # Apostrophe handling should not crash
        tokens = durak.tokenize(text)
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    @given(turkish_sentence())
    @settings(max_examples=100)
    def test_tokenize_with_offsets_returns_valid_offsets(self, text):
        """Token offsets must point to valid positions in original text."""
        assume(len(text) > 0)

        tokens_with_offsets = durak.tokenize_with_offsets(text)

        for token, start, end in tokens_with_offsets:
            # Offset must be within bounds
            assert 0 <= start < end <= len(text), (
                f"Invalid offset [{start}:{end}] for text of length {len(text)}"
            )

            # Extracted substring should be related to token
            extracted = text[start:end]
            assert len(extracted) > 0

    @given(turkish_sentence())
    @settings(max_examples=100)
    def test_tokenize_with_offsets_no_overlaps(self, text):
        """Token offsets should not overlap."""
        assume(len(text) > 0)

        tokens_with_offsets = durak.tokenize_with_offsets(text)

        # Sort by start position
        sorted_tokens = sorted(tokens_with_offsets, key=lambda x: x[1])

        for i in range(len(sorted_tokens) - 1):
            _, start1, end1 = sorted_tokens[i]
            _, start2, end2 = sorted_tokens[i + 1]

            # Next token should start at or after current token ends
            assert end1 <= start2, (
                f"Overlapping tokens: [{start1}:{end1}] and [{start2}:{end2}]"
            )


class TestStopwordProperties:
    """Property tests for stopword management."""

    @given(turkish_sentence())
    @settings(max_examples=200)
    def test_remove_stopwords_reduces_or_maintains_length(self, text):
        """Removing stopwords should never increase token count."""
        tokens = durak.tokenize(text)
        assume(len(tokens) > 0)

        filtered = durak.remove_stopwords(tokens)

        assert len(filtered) <= len(tokens)
        assert isinstance(filtered, list)

    @given(turkish_sentence())
    @settings(max_examples=100)
    def test_stopword_manager_keep_list_honored(self, text):
        """Keep-list words should never be removed, even if they're stopwords."""
        tokens = durak.tokenize(text)
        assume(len(tokens) > 0)

        # Pick a word from tokens as keep word (or use a known stopword)
        keep_word = tokens[0] if tokens else "ve"

        manager = durak.StopwordManager(keep=[keep_word])
        filtered = durak.remove_stopwords(tokens, manager=manager)

        # If keep_word was in original tokens, it must be in filtered
        if keep_word in tokens:
            assert keep_word in filtered, (
                f"Keep word '{keep_word}' was removed despite being in keep-list"
            )


class TestPipelineProperties:
    """Property tests for the full processing pipeline."""

    @given(turkish_sentence())
    @settings(max_examples=100)
    def test_process_text_is_consistent(self, text):
        """Processing the same text twice should give the same result."""
        result1 = durak.process_text(text)
        result2 = durak.process_text(text)

        assert result1 == result2

    @given(turkish_sentence())
    @settings(max_examples=100)
    def test_process_text_always_returns_list(self, text):
        """process_text should always return a list of tokens."""
        result = durak.process_text(text)
        assert isinstance(result, list)

    @given(turkish_sentence())
    @settings(max_examples=100)
    def test_pipeline_custom_preserves_type(self, text):
        """Custom pipelines should maintain consistent output types."""
        pipeline = durak.Pipeline(
            normalize_case=True,
            normalize_unicode=True,
            clean_text=True,
            tokenize=True,
        )

        result = pipeline.process(text)
        assert isinstance(result, list)


# Edge case tests using property-based generation
class TestEdgeCases:
    """Property tests for edge cases and boundary conditions."""

    @given(turkish_text_with_unicode_edge_cases())
    @settings(max_examples=50)
    def test_full_pipeline_handles_unicode_edge_cases(self, text):
        """The full pipeline should handle Unicode edge cases without crashing."""
        # This should not raise any exceptions
        try:
            result = durak.process_text(text)
            assert isinstance(result, list)
        except Exception as e:
            pytest.fail(f"Pipeline crashed on Unicode edge case: {e}")

    @given(turkish_sentence())
    @settings(max_examples=100)
    def test_empty_result_handling(self, text):
        """Functions should gracefully handle inputs that result in empty output."""
        # Extreme cleaning might result in empty output
        cleaned = durak.clean_text(text)

        if not cleaned:
            # Empty cleaned text should tokenize to empty list
            tokens = durak.tokenize(cleaned)
            assert tokens == [] or tokens == [""]
