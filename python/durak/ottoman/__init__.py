"""Ottoman Turkish language support for Durak.

Provides transliteration, tokenization, and normalization for historical
Ottoman Turkish texts in both Arabic script (Elifba) and scholarly Latin
transliteration.

Designed for integration with Ottoman Miner and similar historical text
mining pipelines.

Example:
    >>> from durak.ottoman import OttomanProcessor
    >>> 
    >>> processor = OttomanProcessor(language_variant="ottoman")
    >>> result = processor.process("ḳāżī")
    >>> print(result.tokens)  # ['kadı']
    >>> print(result.original_tokens)  # ['ḳāżī']
    >>> print(result.offset_mappings)  # [{0: 0, 1: 1, ...}]
"""

from .transliterator import OttomanTransliterator, TransliterationMapping, ottoman_to_modern
from .processor import OttomanConfig, OttomanProcessingResult, OttomanProcessor
from .char_maps import (
    ARABIC_TO_LATIN,
    SCHOLARLY_TO_MODERN,
    AMBIGUOUS_MAPPINGS,
)

__all__ = [
    "OttomanTransliterator",
    "TransliterationMapping",
    "ottoman_to_modern",
    "OttomanProcessor",
    "OttomanConfig",
    "OttomanProcessingResult",
    "ARABIC_TO_LATIN",
    "SCHOLARLY_TO_MODERN",
    "AMBIGUOUS_MAPPINGS",
]