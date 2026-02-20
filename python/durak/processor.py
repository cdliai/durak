"""TextProcessor - High-level pipeline orchestration for Turkish NLP.

This module provides the TextProcessor class for v0.5.0, which offers a
configurable, high-level interface for text processing pipelines.

Example:
    >>> from durak import TextProcessor
    >>> 
    >>> # Default pipeline: clean → tokenize → lemmatize → remove stopwords
    >>> processor = TextProcessor()
    >>> result = processor.process("Türkiye'de NLP çok zor!")
    
    >>> # Custom configuration
    >>> processor = TextProcessor(
    ...     lowercase=True,
    ...     remove_stopwords=True,
    ...     lemmatize=True,
    ...     attach_suffixes=True,
    ... )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal

from durak.cleaning import clean_text, normalize_case
from durak.exceptions import ConfigurationError
from durak.lemmatizer import Lemmatizer
from durak.stopwords import BASE_STOPWORDS, StopwordManager, remove_stopwords
from durak.suffixes import attach_detached_suffixes
from durak.tokenizer import tokenize


@dataclass
class ProcessorConfig:
    """Configuration for TextProcessor.
    
    Attributes:
        lowercase: Whether to lowercase text (handles Turkish I/ı correctly)
        remove_stopwords: Whether to filter out stopwords
        lemmatize: Whether to apply lemmatization
        attach_suffixes: Whether to reattach detached suffixes
        remove_punctuation: Whether to remove punctuation tokens
        emoji_mode: How to handle emojis: "keep", "remove", or "extract"
        stopword_manager: Custom stopword manager (uses default if None)
        lemmatizer: Custom lemmatizer (uses default if None)
    """
    lowercase: bool = True
    remove_stopwords: bool = False
    lemmatize: bool = False
    attach_suffixes: bool = False
    remove_punctuation: bool = False
    emoji_mode: Literal["keep", "remove", "extract"] = "keep"
    stopword_manager: StopwordManager | None = None
    lemmatizer: Lemmatizer | None = None


@dataclass
class ProcessingResult:
    """Result of text processing.
    
    Attributes:
        tokens: List of processed tokens
        lemmas: List of lemmas (if lemmatization was enabled)
        emojis: List of extracted emojis (if emoji_mode was "extract")
        metadata: Processing metadata (token count, etc.)
    """
    tokens: list[str] = field(default_factory=list)
    lemmas: list[str] | None = None
    emojis: list[str] | None = None
    metadata: dict = field(default_factory=dict)
    
    def __len__(self) -> int:
        return len(self.tokens)
    
    def __iter__(self):
        return iter(self.tokens)
    
    def __getitem__(self, index: int) -> str:
        return self.tokens[index]


class TextProcessor:
    """High-level text processor for Turkish NLP pipelines.
    
    Orchestrates the full processing pipeline: cleaning → tokenization →
    (optional) suffix reattachment → (optional) lemmatization → 
    (optional) stopword removal.
    
    Args:
        config: ProcessorConfig instance with processing options
        
    Example:
        >>> # Basic usage with defaults
        >>> processor = TextProcessor()
        >>> result = processor.process("Merhaba dünya!")
        
        >>> # With custom configuration
        >>> config = ProcessorConfig(
        ...     lowercase=True,
        ...     remove_stopwords=True,
        ...     lemmatize=True,
        ... )
        >>> processor = TextProcessor(config)
        >>> result = processor.process("Kitapları okuyorum.")
        >>> print(result.tokens)
        ['kitap', 'okuyorum']
        >>> print(result.lemmas)
        ['kitap', 'oku']
        
        >>> # Batch processing
        >>> texts = ["Birinci text.", "İkinci text."]
        >>> results = processor.process_batch(texts)
    """
    
    def __init__(self, config: ProcessorConfig | None = None):
        """Initialize the text processor.
        
        Args:
            config: Configuration object. Uses defaults if None.
        """
        self.config = config or ProcessorConfig()
        
        # Initialize components based on config
        if self.config.stopword_manager is None and self.config.remove_stopwords:
            self.config.stopword_manager = StopwordManager()
        
        if self.config.lemmatizer is None and self.config.lemmatize:
            self.config.lemmatizer = Lemmatizer(strategy="hybrid")
    
    def process(self, text: str) -> ProcessingResult:
        """Process a single text through the pipeline.
        
        Args:
            text: Input text to process
            
        Returns:
            ProcessingResult with tokens and optional metadata
            
        Example:
            >>> processor = TextProcessor(ProcessorConfig(lemmatize=True))
            >>> result = processor.process("Kitaplar okunuyor.")
            >>> result.tokens
            ['kitaplar', 'okunuyor']
            >>> result.lemmas
            ['kitap', 'oku']
        """
        if not isinstance(text, str):
            raise ConfigurationError(f"Input must be a string, got {type(text).__name__}")
        
        result = ProcessingResult()
        
        # Step 1: Clean text (with emoji handling)
        if self.config.emoji_mode == "extract":
            cleaned, emojis = clean_text(text, emoji_mode="extract")
            result.emojis = emojis
        else:
            cleaned = clean_text(text, emoji_mode=self.config.emoji_mode)
        
        # Step 2: Additional lowercase normalization if needed
        # (clean_text already lowercases via DEFAULT_CLEANING_STEPS)
        
        # Step 3: Tokenize
        tokens = tokenize(cleaned, strip_punct=self.config.remove_punctuation)
        
        # Step 4: Reattach detached suffixes
        if self.config.attach_suffixes:
            tokens = attach_detached_suffixes(tokens)
        
        # Step 5: Lemmatize (before stopword removal to help with matching)
        if self.config.lemmatize and self.config.lemmatizer:
            lemmas = [self.config.lemmatizer(token) for token in tokens]
            result.lemmas = lemmas
        
        # Step 6: Remove stopwords
        if self.config.remove_stopwords and self.config.stopword_manager:
            # Filter both tokens and lemmas together
            filtered_indices = [
                i for i, token in enumerate(tokens)
                if not self.config.stopword_manager.is_stopword(token)
            ]
            tokens = [tokens[i] for i in filtered_indices]
            if result.lemmas:
                result.lemmas = [result.lemmas[i] for i in filtered_indices]
        
        result.tokens = tokens
        result.metadata = {
            "token_count": len(tokens),
            "had_emojis": result.emojis is not None and len(result.emojis) > 0,
            "lemmatized": result.lemmas is not None,
        }
        
        return result
    
    def process_batch(self, texts: list[str]) -> list[ProcessingResult]:
        """Process multiple texts efficiently.
        
        Args:
            texts: List of input texts
            
        Returns:
            List of ProcessingResult objects
            
        Example:
            >>> processor = TextProcessor()
            >>> texts = ["Birinci.", "İkinci.", "Üçüncü."]
            >>> results = processor.process_batch(texts)
            >>> [r.tokens for r in results]
            [['birinci'], ['ikinci'], ['üçüncü']]
        """
        return [self.process(text) for text in texts]
    
    def __call__(self, text: str) -> ProcessingResult:
        """Allow processor to be called directly.
        
        Example:
            >>> processor = TextProcessor()
            >>> result = processor("Merhaba!")  # Same as processor.process("Merhaba!")
        """
        return self.process(text)
    
    def __repr__(self) -> str:
        parts = []
        if self.config.lowercase:
            parts.append("lowercase=True")
        if self.config.remove_stopwords:
            parts.append("remove_stopwords=True")
        if self.config.lemmatize:
            parts.append("lemmatize=True")
        if self.config.attach_suffixes:
            parts.append("attach_suffixes=True")
        if self.config.remove_punctuation:
            parts.append("remove_punctuation=True")
        return f"TextProcessor({', '.join(parts)})"


# Convenience function for one-off processing
def process_text(
    text: str,
    *,
    lowercase: bool = True,
    remove_stopwords: bool = False,
    lemmatize: bool = False,
    attach_suffixes: bool = False,
    remove_punctuation: bool = False,
    emoji_mode: Literal["keep", "remove", "extract"] = "keep",
) -> ProcessingResult:
    """Process text with a one-off configuration.
    
    Convenience function for simple use cases without creating a processor.
    
    Args:
        text: Input text to process
        lowercase: Whether to lowercase (default: True)
        remove_stopwords: Whether to remove stopwords (default: False)
        lemmatize: Whether to lemmatize (default: False)
        attach_suffixes: Whether to reattach suffixes (default: False)
        remove_punctuation: Whether to remove punctuation (default: False)
        emoji_mode: How to handle emojis (default: "keep")
        
    Returns:
        ProcessingResult with processed tokens
        
    Example:
        >>> result = process_text(
        ...     "Türkiye'de NLP çok zor!",
        ...     remove_stopwords=True,
        ...     attach_suffixes=True,
        ... )
        >>> result.tokens
        ["türkiye'de", "nlp", "zor"]
    """
    config = ProcessorConfig(
        lowercase=lowercase,
        remove_stopwords=remove_stopwords,
        lemmatize=lemmatize,
        attach_suffixes=attach_suffixes,
        remove_punctuation=remove_punctuation,
        emoji_mode=emoji_mode,
    )
    processor = TextProcessor(config)
    return processor.process(text)


__all__ = [
    "ProcessorConfig",
    "ProcessingResult",
    "TextProcessor",
    "process_text",
]