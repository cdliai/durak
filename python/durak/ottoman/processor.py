"""Ottoman Turkish text processor with script detection and transliteration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..cleaning import clean_text
from ..tokenizer import tokenize
from ..exceptions import ConfigurationError, DurakError, ResourceError
from .char_maps import (
    ARABIC_TO_LATIN,
    SCHOLARLY_TO_MODERN,
    SCHOLARLY_DIACRITIC_CHARS,
    contains_arabic,
    normalize_diacritics,
)
from .transliterator import TransliterationMapping, OttomanTransliterator


@dataclass
class OttomanConfig:
    """Configuration for Ottoman text processing.
    
    Attributes:
        language_variant: Language variant ("ottoman", "modern", "mixed")
        auto_transliterate: Whether to auto-transliterate to modern Turkish
        remove_punctuation: Whether to remove punctuation during tokenization
        preserve_original: Whether to preserve original tokens in result
        lowercase: Whether to lowercase output tokens
        emoji_mode: How to handle emojis ("remove", "keep", "extract")
        custom_stopwords: Additional stopwords to use (set or path to JSON file)
        custom_suffixes: Additional suffixes to remove (list or path to JSON file)
        use_durak_stopwords: Whether to use durak's default stopwords
        use_context_rules: Whether to apply contextual rules for ambiguous chars
    """
    language_variant: str = "ottoman"
    auto_transliterate: bool = True
    remove_punctuation: bool = True
    preserve_original: bool = True
    lowercase: bool = False
    emoji_mode: str = "remove"
    custom_stopwords: set[str] | str | Path | None = None
    custom_suffixes: list[str] | str | Path | None = None
    use_durak_stopwords: bool = True
    use_context_rules: bool = True
    
    def __post_init__(self):
        """Validate configuration."""
        valid_variants = {"ottoman", "modern", "mixed"}
        if self.language_variant not in valid_variants:
            raise ConfigurationError(
                f"Invalid language_variant: {self.language_variant!r}. "
                f"Must be one of: {valid_variants}"
            )


@dataclass
class OttomanProcessingResult:
    """Result of Ottoman text processing.
    
    Attributes:
        tokens: List of processed (transliterated) tokens
        original_tokens: List of original tokens (if preserve_original=True)
        offset_mappings: List of TransliterationMapping with char-level offsets
        script_types: List of detected script types per token
        metadata: Additional processing metadata
    """
    tokens: list[str] = field(default_factory=list)
    original_tokens: list[str] | None = None
    offset_mappings: list[TransliterationMapping] = field(default_factory=list)
    script_types: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __len__(self) -> int:
        return len(self.tokens)
    
    def __iter__(self):
        return iter(self.tokens)
    
    def __getitem__(self, index: int) -> str:
        return self.tokens[index]
    
    def get_original(self, index: int) -> str | None:
        """Get original token at index."""
        if self.original_tokens and index < len(self.original_tokens):
            return self.original_tokens[index]
        return None
    
    def get_script_type(self, index: int) -> str | None:
        """Get script type at index."""
        if index < len(self.script_types):
            return self.script_types[index]
        return None


def load_stopwords(path: str | Path) -> set[str]:
    """Load stopwords from JSON file.
    
    Args:
        path: Path to JSON file containing stopwords list
        
    Returns:
        Set of stopwords
        
    Raises:
        DurakError: If file cannot be loaded
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
            elif isinstance(data, dict) and 'stopwords' in data:
                return set(data['stopwords'])
            else:
                raise ResourceError(f"Invalid stopwords format in {path}")
    except (json.JSONDecodeError, IOError) as e:
        raise ResourceError(f"Failed to load stopwords from {path}: {e}")


def load_suffixes(path: str | Path) -> list[str]:
    """Load suffixes from JSON file.
    
    Args:
        path: Path to JSON file containing suffixes list
        
    Returns:
        List of suffixes
        
    Raises:
        DurakError: If file cannot be loaded
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and 'suffixes' in data:
                return data['suffixes']
            else:
                raise ResourceError(f"Invalid suffixes format in {path}")
    except (json.JSONDecodeError, IOError) as e:
        raise ResourceError(f"Failed to load suffixes from {path}: {e}")


def _load_default_stopwords() -> set[str]:
    """Load default Ottoman stopwords."""
    # Common Ottoman Turkish stopwords
    return {
        "ve", "ile", "için", "bu", "şu", "o", "bir", "ki", "de", "da",
        "ama", "fakat", "lakin", "çünkü", "şayet", "eğer", "gibi", "kadar",
        "her", "bazı", "hiç", "bütün", "tüm", "diğer", "öbür", "kendi",
    }


class OttomanProcessor:
    """Main processor for Ottoman Turkish text.
    
    Provides comprehensive text processing including script detection,
    transliteration, tokenization, and normalization with offset preservation
    for OCR bounding box alignment.
    
    Example:
        >>> processor = OttomanProcessor()
        >>> result = processor.process("ḳāżī")
        >>> print(result.tokens)
        ['kadı']
        >>> print(result.original_tokens)
        ['ḳāżī']
    """
    
    def __init__(self, config: OttomanConfig | None = None):
        """Initialize processor with configuration.
        
        Args:
            config: OttomanConfig instance or None for defaults
        """
        self.config = config or OttomanConfig()
        self.transliterator = OttomanTransliterator(
            use_context_rules=self.config.use_context_rules
        )
        
        # Initialize stopwords
        self.stopwords: set[str] = set()
        if self.config.use_durak_stopwords:
            self.stopwords.update(_load_default_stopwords())
        if self.config.custom_stopwords:
            # If string/path provided, load from file; otherwise use as set
            if isinstance(self.config.custom_stopwords, (str, Path)):
                self.stopwords.update(load_stopwords(self.config.custom_stopwords))
            else:
                self.stopwords.update(self.config.custom_stopwords)
        
        # Initialize suffixes
        self.suffixes: list[str] = []
        if self.config.custom_suffixes:
            # If string/path provided, load from file; otherwise use as list
            if isinstance(self.config.custom_suffixes, (str, Path)):
                self.suffixes = load_suffixes(self.config.custom_suffixes)
            else:
                self.suffixes = self.config.custom_suffixes.copy()
    
    def _contains_scholarly_latin(self, text: str) -> bool:
        """Check if text contains scholarly Latin characters with diacritics."""
        return any(char in SCHOLARLY_DIACRITIC_CHARS for char in text)
    
    def _scholarly_to_modern_chars(self, text: str) -> str:
        """Convert scholarly Latin characters to modern Turkish for tokenization.
        
        This is used to make text tokenizable - the actual transliteration
        with proper offsets is done via TransliterationMapping.
        """
        result = []
        for char in text:
            result.append(SCHOLARLY_TO_MODERN.get(char, char))
        return ''.join(result)
    
    def _arabic_to_latin_chars(self, text: str) -> str:
        """Convert Arabic characters to Latin for tokenization.
        
        Simple character-by-character conversion for tokenization purposes.
        """
        result = []
        for char in text:
            result.append(ARABIC_TO_LATIN.get(char, char))
        return ''.join(result)
    
    def process(self, text: str) -> OttomanProcessingResult:
        """Process Ottoman Turkish text.
        
        Pipeline:
        1. Unicode normalization (NFC)
        2. Text cleaning (emoji handling)
        3. Tokenization (on pre-normalized text for token boundary detection)
        4. Token-level transliteration (for offset preservation)
        5. Stopword removal (optional)
        
        Args:
            text: Input text in Arabic script, scholarly Latin, or modern Turkish
            
        Returns:
            OttomanProcessingResult with tokens and offset mappings
        """
        if not isinstance(text, str):
            raise ConfigurationError(f"Input must be string, got {type(text).__name__}")
        
        result = OttomanProcessingResult()
        
        # Step 1: Normalize Unicode (NFC for diacritics)
        text = normalize_diacritics(text)
        
        # Step 2: Clean text (handle emojis, etc.)
        cleaned_result = clean_text(text, emoji_mode=self.config.emoji_mode)
        if isinstance(cleaned_result, tuple):
            cleaned, emojis = cleaned_result
        else:
            cleaned = cleaned_result
            emojis = []
        
        # Step 3: Detect script type
        if contains_arabic(cleaned):
            script_type = "arabic"
        elif self._contains_scholarly_latin(cleaned):
            script_type = "scholarly_latin"
        else:
            script_type = "modern_latin"
        
        # Step 4: Transliterate full text first (for tokenization), then tokenize
        # Always create a mapping for offset preservation, even when not auto-transliterating
        if script_type == "arabic":
            full_mapping = self.transliterator.arabic_to_modern(cleaned)
            if self.config.auto_transliterate:
                text_for_tokenization = full_mapping.transliterated
            else:
                # For tokenization, still need to normalize, but will use original tokens
                text_for_tokenization = full_mapping.transliterated
        elif script_type == "scholarly_latin":
            full_mapping = self.transliterator.scholarly_to_modern(cleaned)
            if self.config.auto_transliterate:
                text_for_tokenization = full_mapping.transliterated
            else:
                # For tokenization, still need to normalize, but will use original tokens
                text_for_tokenization = full_mapping.transliterated
        else:
            # Modern Latin - no transliteration needed
            text_for_tokenization = cleaned
            full_mapping = None
        
        # Step 5: Tokenize the (transliterated) text
        tokens = tokenize(text_for_tokenization, strip_punct=self.config.remove_punctuation)
        
        # Step 6: Build results with proper transliteration mappings
        processed_tokens = []
        original_tokens_result = [] if self.config.preserve_original else None
        offset_mappings = []
        script_types = []
        
        # Build per-token mappings by mapping modern tokens back to original
        if full_mapping is not None:
            # For each modern token, find the corresponding original text
            search_start = 0
            for token in tokens:
                # Find position in transliterated text
                trans_text = text_for_tokenization
                trans_lower = trans_text.lower()
                token_lower = token.lower()
                
                trans_idx = trans_lower.find(token_lower, search_start)
                if trans_idx == -1:
                    trans_idx = search_start
                
                # Map to original position using the full mapping
                orig_start = full_mapping.get_original_offset(trans_idx)
                orig_end_pos = trans_idx + len(token) - 1
                orig_end = full_mapping.get_original_offset(orig_end_pos)
                
                # Find the end of this character range
                if orig_end >= 0:
                    for o_s, o_e, t_s, t_e in full_mapping.char_mappings:
                        if t_s <= orig_end_pos < t_e:
                            orig_end = o_e
                            break
                
                if orig_start >= 0 and orig_end >= orig_start:
                    original_token = cleaned[orig_start:orig_end]
                else:
                    original_token = token
                
                # Determine output token based on auto_transliterate setting
                if self.config.auto_transliterate:
                    output_token = token
                else:
                    output_token = original_token
                
                # Create mapping for this token
                token_mapping = TransliterationMapping(
                    original=original_token,
                    transliterated=token,
                    char_mappings=[(0, len(original_token), 0, len(token))],
                )
                
                processed_tokens.append(output_token)
                if original_tokens_result is not None:
                    original_tokens_result.append(original_token)
                offset_mappings.append(token_mapping)
                script_types.append(script_type)
                
                # Update search position for next token
                search_start = trans_idx + len(token)
        else:
            # No transliteration needed (modern Latin)
            for token in tokens:
                processed_tokens.append(token)
                if original_tokens_result is not None:
                    original_tokens_result.append(token)
                offset_mappings.append(TransliterationMapping(
                    original=token,
                    transliterated=token,
                    char_mappings=[(0, len(token), 0, len(token))],
                ))
                script_types.append(script_type)
        
        # Step 6: Remove stopwords (using processed/modern tokens for matching)
        if self.stopwords:
            filtered_indices = [
                i for i, token in enumerate(processed_tokens)
                if token.lower() not in self.stopwords
            ]
            processed_tokens = [processed_tokens[i] for i in filtered_indices]
            if original_tokens_result is not None:
                original_tokens_result = [original_tokens_result[i] for i in filtered_indices]
            offset_mappings = [offset_mappings[i] for i in filtered_indices]
            script_types = [script_types[i] for i in filtered_indices]
        
        # Build result
        result.tokens = processed_tokens
        result.original_tokens = original_tokens_result
        result.offset_mappings = offset_mappings
        result.script_types = script_types
        result.metadata = {
            "token_count": len(processed_tokens),
            "original_script_types": script_types,
            "emojis_extracted": len(emojis) if emojis else 0,
            "language_variant": self.config.language_variant,
            "auto_transliterated": self.config.auto_transliterate,
        }
        
        return result
    
    def __call__(self, text: str) -> OttomanProcessingResult:
        """Allow processor to be called directly."""
        return self.process(text)
    
    def process_batch(self, texts: list[str]) -> list[OttomanProcessingResult]:
        """Process multiple texts in batch.
        
        Args:
            texts: List of input texts to process
            
        Returns:
            List of OttomanProcessingResult, one per input text
        """
        return [self.process(text) for text in texts]
    
    def get_offsets_for_token(
        self, 
        result: OttomanProcessingResult,
        token_index: int,
    ) -> tuple[int, int] | None:
        """Get offset mapping for a specific token.
        
        Args:
            result: Processing result containing offset mappings
            token_index: Index of token in result
            
        Returns:
            Tuple of (start_offset, end_offset) or None
        """
        if 0 <= token_index < len(result.offset_mappings):
            mapping = result.offset_mappings[token_index]
            # Return the character offsets for the original text
            if mapping.char_mappings:
                # Get the first and last character mappings
                first = mapping.char_mappings[0]
                last = mapping.char_mappings[-1]
                return (first[0], last[1])  # (orig_start, orig_end)
        return None
    
    def get_bounding_box_info(
        self,
        token_index: int,
        result: OttomanProcessingResult,
    ) -> dict[str, Any] | None:
        """Get bounding box information for OCR alignment.
        
        This is a placeholder for integration with Ottoman Miner's
        PDF processing pipeline. The actual bounding box coordinates
        would come from the OCR system.
        
        Args:
            token_index: Index of token
            result: Processing result
            
        Returns:
            Dictionary with offset information for bounding box calculation
        """
        offsets = self.get_offsets_for_token(result, token_index)
        if offsets is None:
            return None
        
        mapping = result.offset_mappings[token_index]
        return {
            "token": mapping.transliterated,
            "original": mapping.original,
            "char_mappings": mapping.char_mappings,
            "offsets": offsets,
            "script_type": result.script_types[token_index] if token_index < len(result.script_types) else None,
        }


# Convenience function
def ottoman_to_modern(text: str) -> str:
    """Quick conversion from Ottoman (Arabic or scholarly) to modern Turkish.
    
    Args:
        text: Text in Arabic script or scholarly Latin
        
    Returns:
        Modern Turkish text
        
    Example:
        >>> ottoman_to_modern("ḳāżī")
        'kadı'
        >>> ottoman_to_modern("قاضی")
        'kadı'
    """
    transliterator = OttomanTransliterator()
    return transliterator.auto_transliterate(text).transliterated
