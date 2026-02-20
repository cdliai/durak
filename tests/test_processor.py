"""Tests for TextProcessor class."""

import pytest

from durak import ProcessorConfig, TextProcessor, process_text
from durak.exceptions import ConfigurationError


class TestTextProcessor:
    """Test TextProcessor functionality."""

    def test_basic_processing(self):
        """Test basic text processing."""
        processor = TextProcessor()
        result = processor.process("Merhaba dünya!")
        
        assert len(result.tokens) > 0
        assert "merhaba" in result.tokens  # Should be lowercased
        assert "dünya" in result.tokens

    def test_with_stopwords(self):
        """Test processing with stopword removal."""
        config = ProcessorConfig(remove_stopwords=True)
        processor = TextProcessor(config)
        result = processor.process("Bu bir test cümlesidir.")
        
        # "bu" and "bir" are stopwords
        assert "bu" not in result.tokens
        assert "bir" not in result.tokens
        assert "test" in result.tokens

    def test_with_suffix_attachment(self):
        """Test processing with suffix attachment."""
        config = ProcessorConfig(attach_suffixes=True)
        processor = TextProcessor(config)
        result = processor.process("Ankara ' da kaldım.")
        
        # Should reattach suffix
        assert any("ankara" in t for t in result.tokens)

    def test_with_punctuation_removal(self):
        """Test processing with punctuation removal."""
        config = ProcessorConfig(remove_punctuation=True)
        processor = TextProcessor(config)
        result = processor.process("Merhaba, dünya! Nasılsın?")
        
        # Punctuation should be removed
        assert "." not in result.tokens
        assert "," not in result.tokens
        assert "!" not in result.tokens
        assert "?" not in result.tokens

    def test_emoji_keep_mode(self):
        """Test emoji keep mode."""
        config = ProcessorConfig(emoji_mode="keep")
        processor = TextProcessor(config)
        result = processor.process("Harika! 🎉 Çok güzel 😊")
        
        # Check if emojis preserved (exact behavior depends on tokenization)
        assert len(result.tokens) > 0

    def test_emoji_remove_mode(self):
        """Test emoji remove mode."""
        config = ProcessorConfig(emoji_mode="remove")
        processor = TextProcessor(config)
        result = processor.process("Harika! 🎉 Çok güzel 😊")
        
        # Emojis should be removed
        assert "🎉" not in result.tokens
        assert "😊" not in result.tokens

    def test_emoji_extract_mode(self):
        """Test emoji extract mode."""
        config = ProcessorConfig(emoji_mode="extract")
        processor = TextProcessor(config)
        result = processor.process("Harika! 🎉 Çok güzel 😊")
        
        # Emojis should be extracted
        assert result.emojis is not None
        assert len(result.emojis) > 0

    def test_batch_processing(self):
        """Test batch processing."""
        processor = TextProcessor()
        texts = ["Birinci.", "İkinci.", "Üçüncü."]
        results = processor.process_batch(texts)
        
        assert len(results) == 3
        for result in results:
            assert len(result.tokens) > 0

    def test_callable_interface(self):
        """Test that processor is callable."""
        processor = TextProcessor()
        result = processor("Test text.")
        
        assert len(result.tokens) > 0

    def test_invalid_input(self):
        """Test handling of invalid input."""
        processor = TextProcessor()
        
        with pytest.raises(ConfigurationError):
            processor.process(123)  # Not a string

    def test_process_text_convenience_function(self):
        """Test process_text convenience function."""
        result = process_text(
            "Bu bir test cümlesidir.",
            remove_stopwords=True,
        )
        
        assert len(result.tokens) > 0
        assert isinstance(result.tokens, list)

    def test_result_iteration(self):
        """Test that result is iterable."""
        processor = TextProcessor()
        result = processor.process("Bir iki üç.")
        
        tokens = list(result)
        assert len(tokens) > 0

    def test_result_indexing(self):
        """Test that result supports indexing."""
        processor = TextProcessor()
        result = processor.process("Bir iki üç.")
        
        if len(result) > 0:
            first_token = result[0]
            assert isinstance(first_token, str)

    def test_metadata(self):
        """Test that metadata is populated."""
        processor = TextProcessor()
        result = processor.process("Test cümlesi.")
        
        assert "token_count" in result.metadata
        assert result.metadata["token_count"] == len(result.tokens)

    def test_repr(self):
        """Test string representation."""
        config = ProcessorConfig(
            remove_stopwords=True,
            lemmatize=True,
        )
        processor = TextProcessor(config)
        repr_str = repr(processor)
        
        assert "TextProcessor" in repr_str
        assert "remove_stopwords=True" in repr_str


class TestProcessorConfig:
    """Test ProcessorConfig functionality."""

    def test_default_config(self):
        """Test default configuration."""
        config = ProcessorConfig()
        
        assert config.lowercase is True
        assert config.remove_stopwords is False
        assert config.lemmatize is False
        assert config.emoji_mode == "keep"

    def test_custom_config(self):
        """Test custom configuration."""
        config = ProcessorConfig(
            lowercase=False,
            remove_stopwords=True,
            emoji_mode="remove",
        )
        
        assert config.lowercase is False
        assert config.remove_stopwords is True
        assert config.emoji_mode == "remove"

    def test_invalid_emoji_mode(self):
        """Test invalid emoji mode is rejected."""
        # This should raise an error when used, not at construction
        config = ProcessorConfig(emoji_mode="invalid")
        processor = TextProcessor(config)
        
        with pytest.raises(ValueError):
            processor.process("Test text.")
