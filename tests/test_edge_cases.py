"""Edge case tests for Durak Turkish NLP toolkit.

Tests boundary conditions, malformed inputs, and unusual text patterns
to ensure robustness and graceful error handling.
"""

import pytest

from durak import (
    ProcessorConfig,
    TextProcessor,
    attach_detached_suffixes,
    clean_text,
    normalize_case,
    remove_stopwords,
    tokenize,
)
from durak.exceptions import ConfigurationError


class TestEmptyAndNoneInputs:
    """Test handling of empty and None inputs."""

    def test_text_processor_empty_string(self):
        """Processor should handle empty string."""
        processor = TextProcessor()
        result = processor.process("")
        assert result.tokens == []
        assert len(result) == 0

    def test_text_processor_whitespace_only(self):
        """Processor should handle whitespace-only strings."""
        processor = TextProcessor()
        result = processor.process("   \n\t   ")
        assert result.tokens == []

    def test_tokenize_empty_string(self):
        """Tokenize should return empty list for empty string."""
        assert tokenize("") == []

    def test_tokenize_none(self):
        """Tokenize should return empty list for None."""
        assert tokenize(None) == []

    def test_clean_text_empty(self):
        """Clean text should handle empty string."""
        assert clean_text("") == ""

    def test_normalize_case_empty(self):
        """Normalize case should handle empty string."""
        assert normalize_case("") == ""

    def test_attach_suffixes_empty(self):
        """Attach suffixes should handle empty list."""
        assert attach_detached_suffixes([]) == []

    def test_remove_stopwords_empty(self):
        """Remove stopwords should handle empty list."""
        assert remove_stopwords([]) == []


class TestInvalidInputs:
    """Test handling of invalid inputs."""

    def test_processor_non_string_input(self):
        """Processor should raise ConfigurationError for non-string input."""
        processor = TextProcessor()
        
        with pytest.raises(ConfigurationError):
            processor.process(123)
        
        with pytest.raises(ConfigurationError):
            processor.process(None)
        
        with pytest.raises(ConfigurationError):
            processor.process(["list", "not", "string"])

    def test_processor_bytes_input(self):
        """Processor should handle bytes appropriately."""
        processor = TextProcessor()
        
        with pytest.raises(ConfigurationError):
            processor.process(b"bytes not string")


class TestVeryLongTexts:
    """Test handling of very long texts."""

    def test_long_text_processing(self):
        """Processor should handle 100KB text."""
        long_text = "Bu bir test cümlesidir. " * 5000  # ~100KB
        processor = TextProcessor()
        
        result = processor.process(long_text)
        assert len(result.tokens) > 0
        assert result.metadata["token_count"] > 0

    def test_repeated_pattern(self):
        """Processor should handle repetitive patterns."""
        text = "abc " * 10000
        processor = TextProcessor()
        
        result = processor.process(text)
        assert len(result.tokens) == 10000

    def test_single_word_repeated(self):
        """Processor should handle single word repeated."""
        text = "test" * 1000
        processor = TextProcessor()
        
        result = processor.process(text)
        assert len(result.tokens) >= 1


class TestSpecialCharacters:
    """Test handling of special characters."""

    def test_various_apostrophes(self):
        """Test different apostrophe characters."""
        texts = [
            "Türkiye'de",   # Straight apostrophe
            "Türkiye'de",   # Curly apostrophe U+2019
            "Türkiye'de",   # Backtick
        ]
        processor = TextProcessor()
        
        for text in texts:
            result = processor.process(text)
            assert len(result.tokens) > 0

    def test_unicode_punctuation(self):
        """Test various Unicode punctuation."""
        text = "Merhaba… nasılsın? Güzel! Harika."
        processor = TextProcessor()
        
        result = processor.process(text)
        assert len(result.tokens) > 0

    def test_zero_width_chars(self):
        """Test zero-width characters."""
        text = "Merhaba\u200Bdünya"  # Zero-width space
        processor = TextProcessor()
        
        result = processor.process(text)
        # Should handle gracefully, either join or separate
        assert len(result.tokens) >= 1

    def test_control_characters(self):
        """Test control characters in text."""
        text = "Merhaba\x00dünya\x01"  # Null and start-of-header
        processor = TextProcessor()
        
        result = processor.process(text)
        # Should not crash
        assert isinstance(result.tokens, list)

    def test_bidirectional_text(self):
        """Test bidirectional text markers."""
        text = "\u2022Türkiye'de\u2022"  # Bullet and RTL marks
        processor = TextProcessor()
        
        result = processor.process(text)
        assert len(result.tokens) > 0


class TestTurkishSpecificEdgeCases:
    """Test Turkish language edge cases."""

    def test_turkish_i_variations(self):
        """Test various Turkish I combinations."""
        test_cases = [
            ("I", "ı"),      # Capital I (Turkish dotless)
            ("İ", "i"),      # Capital dotted I
            ("i", "i"),      # Small i
            ("ı", "ı"),      # Small dotless i
            ("II", "ıı"),    # Double I
            ("İİ", "ii"),    # Double dotted I
            ("Iİ", "ıi"),    # Mixed
        ]
        
        for input_text, expected in test_cases:
            result = normalize_case(input_text, mode="lower")
            assert result == expected, f"Failed for {input_text}: got {result}, expected {expected}"

    def test_turkish_capitalization_edge_cases(self):
        """Test edge cases in Turkish capitalization."""
        # Word with multiple I's
        assert normalize_case("İSTANBUL", mode="lower") == "istanbul"
        assert normalize_case("IĞDIR", mode="lower") == "ığdır"
        
        # Mixed case
        result = normalize_case("İsTaNbUl", mode="lower")
        assert result == "istanbul"

    def test_apostrophe_edge_cases(self):
        """Test apostrophe handling in various positions."""
        texts = [
            "'Türkiye",      # Leading apostrophe
            "Türkiye'",      # Trailing apostrophe
            "Tür'ki'ye",     # Multiple apostrophes
            "'",             # Just apostrophe
            "''",            # Double apostrophe
        ]
        processor = TextProcessor()
        
        for text in texts:
            result = processor.process(text)
            # Should not crash
            assert isinstance(result.tokens, list)

    def test_detached_suffixes_edge_cases(self):
        """Test edge cases in detached suffix attachment."""
        # Multiple spaces
        tokens = attach_detached_suffixes(["Ankara", " ", " ", "'", " ", "da"])
        assert isinstance(tokens, list)
        
        # Suffix at start
        tokens = attach_detached_suffixes(["da", "Ankara"])
        assert "da" in tokens  # Should not attach incorrectly
        
        # Empty tokens between
        tokens = attach_detached_suffixes(["Ankara", "", "'", "da"])
        assert isinstance(tokens, list)


class TestMixedContent:
    """Test handling of mixed content types."""

    def test_mixed_scripts(self):
        """Test text with multiple scripts."""
        text = "Türkiye'de NLP Türkçe 日本語 العربية"
        processor = TextProcessor()
        
        result = processor.process(text)
        assert len(result.tokens) > 0

    def test_mixed_directionality(self):
        """Test mixed LTR and RTL text."""
        text = "Türkçe محتوى عربي Türkçe"
        processor = TextProcessor()
        
        result = processor.process(text)
        assert len(result.tokens) > 0

    def test_numbers_and_text(self):
        """Test various number formats."""
        texts = [
            "2024 yılında",
            "1.250,50 TL",
            "Saat 14:30'da",
            "+90 532 123 45 67",
            "3.14",
            "1-2-3",
        ]
        processor = TextProcessor()
        
        for text in texts:
            result = processor.process(text)
            assert len(result.tokens) > 0

    def test_urls_and_emails(self):
        """Test text with URLs and emails."""
        text = "Visit https://example.com or email test@example.com"
        processor = TextProcessor()
        
        result = processor.process(text)
        assert len(result.tokens) > 0

    def test_hashtags_and_mentions(self):
        """Test social media content."""
        text = "Hey @user check #hashtag and #TürkçeTag"
        processor = TextProcessor(ProcessorConfig(remove_stopwords=True))
        
        result = processor.process(text)
        assert len(result.tokens) > 0


class TestEmojiEdgeCases:
    """Test emoji handling edge cases."""

    def test_single_emoji(self):
        """Test text with single emoji."""
        processor = TextProcessor(ProcessorConfig(emoji_mode="extract"))
        result = processor.process("🎉")
        
        assert result.emojis is not None
        assert "🎉" in result.emojis

    def test_multiple_emojis(self):
        """Test text with multiple emojis."""
        processor = TextProcessor(ProcessorConfig(emoji_mode="extract"))
        result = processor.process("🎉🎊🎁")
        
        assert len(result.emojis) == 3

    def test_emoji_sequences(self):
        """Test emoji sequences (skin tones, families)."""
        text = "👨‍👩‍👧‍👦 👋🏽"  # Family and wave with skin tone
        processor = TextProcessor(ProcessorConfig(emoji_mode="extract"))
        
        result = processor.process(text)
        # Should handle gracefully
        assert isinstance(result.tokens, list)
        assert result.emojis is not None

    def test_emoji_with_variation_selector(self):
        """Test emojis with variation selectors."""
        text = "❤️"  # Heart with variation selector
        processor = TextProcessor(ProcessorConfig(emoji_mode="extract"))
        
        result = processor.process(text)
        assert result.emojis is not None


class TestHTMLAndMarkup:
    """Test HTML and markup handling."""

    def test_empty_html(self):
        """Test empty HTML tags."""
        text = "<p></p><div></div>"
        result = clean_text(text)
        assert result == ""

    def test_nested_html(self):
        """Test deeply nested HTML."""
        text = "<div><div><div><p>Text</p></div></div></div>"
        result = clean_text(text)
        assert "text" in result

    def test_broken_html(self):
        """Test malformed HTML."""
        text = "<p>Unclosed div <span>nested"
        result = clean_text(text)
        # Should handle gracefully
        assert isinstance(result, str)

    def test_html_entities(self):
        """Test HTML entities."""
        text = "T&amp;M&quot; &lt;test&gt;"
        result = clean_text(text)
        assert "T&M" in result or "test" in result

    def test_script_and_style(self):
        """Test that script and style content is removed."""
        text = "<script>alert('test')</script>Content<style>.red{color:red}</style>"
        result = clean_text(text)
        assert "alert" not in result
        assert "color" not in result
        assert "content" in result


class TestWhitespaceEdgeCases:
    """Test various whitespace patterns."""

    def test_multiple_spaces(self):
        """Test multiple consecutive spaces."""
        text = "Word1    Word2     Word3"
        processor = TextProcessor()
        
        result = processor.process(text)
        assert len(result.tokens) >= 3

    def test_newlines_and_tabs(self):
        """Test various whitespace characters."""
        text = "Line1\nLine2\tTabbed\r\nWindows"
        processor = TextProcessor()
        
        result = processor.process(text)
        assert len(result.tokens) >= 3

    def test_leading_trailing_whitespace(self):
        """Test leading and trailing whitespace."""
        text = "   \n\t  Content  \t\n   "
        processor = TextProcessor()
        
        result = processor.process(text)
        assert "content" in result.tokens

    def test_unicode_whitespace(self):
        """Test Unicode whitespace characters."""
        text = "Word1\u00A0Word2\u2003Word3"  # NBSP and em-space
        processor = TextProcessor()
        
        result = processor.process(text)
        assert len(result.tokens) >= 3


class TestPunctuationEdgeCases:
    """Test punctuation handling."""

    def test_repeated_punctuation(self):
        """Test repeated punctuation marks."""
        text = "Wow!!! Really??? Amazing..."
        processor = TextProcessor()
        
        result = processor.process(text)
        assert len(result.tokens) > 0

    def test_unusual_punctuation(self):
        """Test unusual punctuation combinations."""
        text = "(Parentheses) [Brackets] {Braces} "
        processor = TextProcessor()
        
        result = processor.process(text)
        assert len(result.tokens) > 0

    def test_punctuation_only(self):
        """Test text with only punctuation."""
        text = "...!?.,;:'\""
        processor = TextProcessor()
        
        result = processor.process(text)
        # Should return punctuation as tokens or empty
        assert isinstance(result.tokens, list)


class TestConfigurationEdgeCases:
    """Test configuration edge cases."""

    def test_all_false_config(self):
        """Test configuration with all options False."""
        config = ProcessorConfig(
            lowercase=False,
            remove_stopwords=False,
            attach_suffixes=False,
            remove_punctuation=False,
        )
        processor = TextProcessor(config)
        result = processor.process("Türkiye'de NLP!")
        
        assert len(result.tokens) > 0

    def test_all_true_config(self):
        """Test configuration with all options True."""
        config = ProcessorConfig(
            lowercase=True,
            remove_stopwords=True,
            attach_suffixes=True,
            remove_punctuation=True,
        )
        processor = TextProcessor(config)
        result = processor.process("Türkiye'de NLP!")
        
        assert len(result.tokens) >= 0  # May be empty after filtering

    def test_invalid_emoji_mode(self):
        """Test invalid emoji mode."""
        config = ProcessorConfig(emoji_mode="invalid")
        processor = TextProcessor(config)
        
        with pytest.raises(ValueError):
            processor.process("Test text")


class TestResultObjectEdgeCases:
    """Test ProcessingResult edge cases."""

    def test_empty_result_iteration(self):
        """Test iterating over empty result."""
        processor = TextProcessor()
        result = processor.process("")
        
        tokens = list(result)
        assert tokens == []

    def test_empty_result_indexing(self):
        """Test indexing empty result."""
        processor = TextProcessor()
        result = processor.process("")
        
        with pytest.raises(IndexError):
            _ = result[0]

    def test_result_length_consistency(self):
        """Test that len(result) matches len(tokens)."""
        processor = TextProcessor()
        result = processor.process("Bir iki üç dört.")
        
        assert len(result) == len(result.tokens)
        assert result.metadata["token_count"] == len(result.tokens)
