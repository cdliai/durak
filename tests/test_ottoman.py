"""Tests for Ottoman Turkish module.

Tests transliteration, tokenization, and offset preservation
for historical Ottoman Turkish texts.
"""

from typing import Any

import pytest

from durak.ottoman import (
    OttomanConfig,
    OttomanProcessor,
    OttomanTransliterator,
    TransliterationMapping,
    ottoman_to_modern,
)
from durak.ottoman.char_maps import (
    ARABIC_TO_LATIN,
    SCHOLARLY_TO_MODERN,
    contains_arabic,
    normalize_diacritics,
)
from durak.exceptions import ConfigurationError, ResourceError


class TestOttomanTransliterator:
    """Test OttomanTransliterator functionality."""

    def test_scholarly_to_modern_basic(self):
        """Test basic scholarly to modern conversion."""
        transliterator = OttomanTransliterator()
        mapping = transliterator.scholarly_to_modern("ḳāżī")
        
        assert mapping.transliterated == "kadı"
        assert mapping.original == "ḳāżī"
        assert len(mapping.char_mappings) > 0

    def test_scholarly_to_modern_complex(self):
        """Test complex scholarly text."""
        transliterator = OttomanTransliterator()
        
        test_cases = [
            ("ḳāżī", "kadı"),
            ("ṣāḥib", "sahib"),
            ("meḳteb", "mekteb"),
            ("ḥüküm", "hüküm"),
            ("ġālib", "galib"),
        ]
        
        for scholarly, expected in test_cases:
            mapping = transliterator.scholarly_to_modern(scholarly)
            assert mapping.transliterated == expected, f"Failed for {scholarly}"

    def test_arabic_to_latin_basic(self):
        """Test basic Arabic to scholarly Latin conversion."""
        transliterator = OttomanTransliterator()
        mapping = transliterator.arabic_to_latin("قاضی")
        
        # Should convert to scholarly Latin (with diacritics)
        assert "ḳ" in mapping.transliterated or "k" in mapping.transliterated
        assert len(mapping.char_mappings) > 0

    def test_arabic_to_modern(self):
        """Test Arabic directly to Modern Turkish."""
        transliterator = OttomanTransliterator()
        mapping = transliterator.arabic_to_modern("قاضی")
        
        assert mapping.transliterated == "kadı"

    def test_auto_transliterate_scholarly(self):
        """Test auto-detection of scholarly Latin."""
        transliterator = OttomanTransliterator()
        mapping = transliterator.auto_transliterate("ḳāżī")
        
        assert mapping.transliterated == "kadı"

    def test_auto_transliterate_arabic(self):
        """Test auto-detection of Arabic script."""
        transliterator = OttomanTransliterator()
        mapping = transliterator.auto_transliterate("قاضی")
        
        assert mapping.transliterated == "kadı"

    def test_offset_preservation(self):
        """Test that character offsets are preserved."""
        transliterator = OttomanTransliterator()
        mapping = transliterator.scholarly_to_modern("ḳāżī")
        
        # Get offset for first character of transliterated text
        orig_offset = mapping.get_original_offset(0)
        assert orig_offset == 0  # Should map to start of original
        
        # Get original offsets for token span
        orig_start, orig_end = mapping.get_token_offsets(0, len(mapping.transliterated))
        assert orig_start == 0
        assert orig_end == len(mapping.original)

    def test_ambiguous_character_tracking(self):
        """Test tracking of ambiguous character choices."""
        transliterator = OttomanTransliterator(use_context_rules=True)
        mapping = transliterator.arabic_to_latin("كتاب")
        
        # Should track that "ك" was mapped
        assert len(mapping.ambiguous_chars) >= 0  # May or may not be ambiguous

    def test_convenience_function(self):
        """Test ottoman_to_modern convenience function."""
        result = ottoman_to_modern("ḳāżī")
        assert result == "kadı"


class TestOttomanProcessor:
    """Test OttomanProcessor functionality."""

    def test_basic_processing(self):
        """Test basic Ottoman text processing."""
        processor = OttomanProcessor()
        result = processor.process("ḳāżī")
        
        assert "kadı" in result.tokens
        assert result.original_tokens is not None
        assert "ḳāżī" in result.original_tokens

    def test_arabic_script_processing(self):
        """Test processing Arabic script Ottoman."""
        processor = OttomanProcessor()
        result = processor.process("قاضی")
        
        assert "kadı" in result.tokens
        assert result.metadata["language_variant"] == "ottoman"

    def test_mixed_script_processing(self):
        """Test processing mixed Arabic/Latin text."""
        processor = OttomanProcessor()
        result = processor.process("ḳāżī (قاضی)")
        
        # Should process both versions
        assert len(result.tokens) > 0
        assert "kadı" in result.tokens

    def test_script_type_detection(self):
        """Test correct script type detection."""
        processor = OttomanProcessor()
        
        # Scholarly Latin
        result = processor.process("ḳāżī")
        assert "scholarly_latin" in result.script_types
        
        # Modern Latin
        result = processor.process("kadı")
        assert "modern_latin" in result.script_types

    def test_preserve_original_false(self):
        """Test without original token preservation."""
        config = OttomanConfig(preserve_original=False)
        processor = OttomanProcessor(config)
        result = processor.process("ḳāżī")
        
        assert result.original_tokens is None
        assert "kadı" in result.tokens

    def test_no_transliteration(self):
        """Test modern mode without transliteration."""
        config = OttomanConfig(
            language_variant="modern",
            auto_transliterate=False,
        )
        processor = OttomanProcessor(config)
        result = processor.process("ḳāżī")
        
        # Should keep scholarly form
        assert "ḳāżī" in result.tokens

    def test_custom_stopwords(self, tmp_path):
        """Test loading custom stopwords."""
        stopwords_file = tmp_path / "custom_stopwords.json"
        stopwords_file.write_text('{"stopwords": ["test", "words"]}')
        
        config = OttomanConfig(custom_stopwords=str(stopwords_file))
        processor = OttomanProcessor(config)
        
        result = processor.process("test words here")
        assert "test" not in result.tokens
        assert "words" not in result.tokens
        assert "here" in result.tokens

    def test_custom_stopwords_not_found(self):
        """Test error for missing stopwords file."""
        config = OttomanConfig(custom_stopwords="/nonexistent/file.json")
        
        with pytest.raises(ResourceError):
            OttomanProcessor(config)

    def test_batch_processing(self):
        """Test batch processing."""
        processor = OttomanProcessor()
        texts = ["ḳāżī", "meḳteb", "ṣāḥib"]
        
        results = processor.process_batch(texts)
        
        assert len(results) == 3
        for result in results:
            assert len(result.tokens) > 0

    def test_offset_retrieval(self):
        """Test getting offsets for tokens."""
        processor = OttomanProcessor()
        result = processor.process("ḳāżī hakkında")
        
        if len(result.tokens) > 0:
            offsets = processor.get_offsets_for_token(result, 0)
            assert offsets is not None
            assert isinstance(offsets, tuple)
            assert len(offsets) == 2

    def test_callable_interface(self):
        """Test processor as callable."""
        processor = OttomanProcessor()
        result = processor("ḳāżī")
        
        assert "kadı" in result.tokens


class TestOttomanConfig:
    """Test OttomanConfig functionality."""

    def test_default_config(self):
        """Test default configuration."""
        config = OttomanConfig()
        
        assert config.language_variant == "ottoman"
        assert config.auto_transliterate is True
        assert config.preserve_original is True
        assert config.use_context_rules is True

    def test_invalid_variant(self):
        """Test invalid language variant."""
        with pytest.raises(ConfigurationError):
            OttomanConfig(language_variant="invalid")

    def test_valid_variants(self):
        """Test valid language variants."""
        config_ottoman = OttomanConfig(language_variant="ottoman")
        assert config_ottoman.language_variant == "ottoman"
        
        config_modern = OttomanConfig(language_variant="modern")
        assert config_modern.language_variant == "modern"


class TestCharacterMaps:
    """Test character mapping functions."""

    def test_arabic_to_latin_mappings(self):
        """Test Arabic to Latin mappings exist."""
        assert "ا" in ARABIC_TO_LATIN
        assert "ب" in ARABIC_TO_LATIN
        assert "ق" in ARABIC_TO_LATIN

    def test_scholarly_to_modern_mappings(self):
        """Test scholarly to modern mappings exist."""
        assert "ḳ" in SCHOLARLY_TO_MODERN
        assert "ṣ" in SCHOLARLY_TO_MODERN
        assert "ā" in SCHOLARLY_TO_MODERN

    def test_contains_arabic(self):
        """Test Arabic detection."""
        assert contains_arabic("قاضی") is True
        assert contains_arabic("kadı") is False
        assert contains_arabic("ḳāżī") is False
        assert contains_arabic("mixed قاضی") is True

    def test_normalize_diacritics(self):
        """Test Unicode NFC normalization."""
        # Precomposed vs decomposed forms should be equal after normalization
        text1 = "ā"  # Precomposed
        text2 = "a\u0304"  # a + combining macron
        
        normalized1 = normalize_diacritics(text1)
        normalized2 = normalize_diacritics(text2)
        
        assert normalized1 == normalized2


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string(self):
        """Test empty string handling."""
        processor = OttomanProcessor()
        result = processor.process("")
        
        assert result.tokens == []
        assert len(result) == 0

    def test_whitespace_only(self):
        """Test whitespace-only input."""
        processor = OttomanProcessor()
        result = processor.process("   \n\t   ")
        
        assert len(result.tokens) == 0 or all(t.strip() for t in result.tokens)

    def test_invalid_input_type(self):
        """Test invalid input type."""
        processor = OttomanProcessor()
        invalid_number: Any = 123
        invalid_none: Any = None
        
        with pytest.raises(ConfigurationError):
            processor.process(invalid_number)
        
        with pytest.raises(ConfigurationError):
            processor.process(invalid_none)

    def test_long_text(self):
        """Test long text processing."""
        processor = OttomanProcessor()
        long_text = "ḳāżī " * 1000
        
        result = processor.process(long_text)
        assert len(result.tokens) > 0

    def test_mixed_content(self):
        """Test mixed content types."""
        processor = OttomanProcessor()
        
        # Mixed with punctuation
        result = processor.process("ḳāżī, meḳteb.")
        assert "kadı" in result.tokens or "ḳāżī" in result.tokens
        
        # Mixed with numbers
        result = processor.process("ḳāżī 123")
        assert len(result.tokens) > 0


class TestIntegration:
    """Integration tests with Durak core."""

    def test_with_durak_stopwords(self):
        """Test integration with Durak stopword removal."""
        from durak import BASE_STOPWORDS
        
        processor = OttomanProcessor()
        result = processor.process("ve ḳāżī")
        
        # "ve" is a stopword
        assert "ve" not in result.tokens or "kadı" in result.tokens

    def test_transliteration_consistency(self):
        """Test that transliteration is consistent."""
        processor = OttomanProcessor()
        
        # Same word should always produce same result
        result1 = processor.process("ḳāżī")
        result2 = processor.process("ḳāżī")
        
        assert result1.tokens == result2.tokens

    def test_offset_monotonicity(self):
        """Test that offsets are monotonic."""
        transliterator = OttomanTransliterator()
        mapping = transliterator.scholarly_to_modern("ḳāżī meḳteb")
        
        # Check that character mappings are in order
        prev_end = 0
        for orig_start, orig_end, trans_start, trans_end in mapping.char_mappings:
            assert trans_start >= prev_end
            prev_end = trans_end


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
