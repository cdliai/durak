"""Type stubs for the _durak_core Rust extension module.

This module provides high-performance Rust implementations of core NLP operations
for Turkish text processing.
"""

from __future__ import annotations

class Token:
    """Token with offset mapping to original text.

    Used for NER and other tasks requiring exact alignment with raw input.
    The start and end attributes are CHARACTER offsets (not byte offsets) for
    Python compatibility, ensuring text[start:end] correctly extracts the
    original token from the raw text.

    Attributes:
        text: The token text (may be normalized, e.g., lowercased)
        start: Start character offset in the original raw text
        end: End character offset in the original raw text

    Examples:
        >>> token = Token("merhaba", 0, 7)
        >>> token.text
        'merhaba'
        >>> token.start
        0
        >>> token.end
        7
    """

    text: str
    start: int
    end: int

    def __init__(self, text: str, start: int, end: int) -> None:
        """Create a new Token.

        Args:
            text: The token text (may be normalized)
            start: Start character offset in the original text
            end: End character offset in the original text
        """
        ...

    def __repr__(self) -> str:
        """Return string representation of the token.

        Returns:
            String in format: Token(text='...', start=N, end=M)
        """
        ...

def fast_normalize(text: str) -> str:
    """Fast normalization for Turkish text.

    Handles Turkish-specific I/ı and İ/i conversion correctly and lowercases the rest.
    This is a high-performance Rust implementation with single-pass allocation.

    Args:
        text: The text to normalize

    Returns:
        Normalized lowercase text with correct Turkish character handling

    Examples:
        >>> fast_normalize("ISTANBUL")
        'istanbul'
        >>> fast_normalize("İSTANBUL")
        'istanbul'
    """
    ...

def tokenize_with_offsets(text: str) -> list[tuple[str, int, int]]:
    """Tokenize text and return tokens with their character offsets.

    Returns tokens along with their start and end character positions in the
    original text. Offsets are character indices (not byte indices) for Python
    compatibility.

    Handles:
    - URLs (http://, https://, www.)
    - Emoticons (:), ;), :D, etc.)
    - Apostrophes (Turkish possessive/case markers)
    - Numbers (including decimals and ranges)
    - Hyphenated words
    - Punctuation

    Args:
        text: The text to tokenize

    Returns:
        List of (token, start_index, end_index) tuples where indices are
        character positions

    Examples:
        >>> tokenize_with_offsets("Merhaba dünya!")
        [('Merhaba', 0, 7), ('dünya', 8, 13), ('!', 13, 14)]
        >>> tokenize_with_offsets("ankara'da")
        [('ankara', 0, 6), ("'", 6, 7), ('da', 7, 9)]
    """
    ...

def lookup_lemma(word: str) -> str | None:
    """Perform exact dictionary lookup for lemmatization.

    Tier 1 lemmatization: Fast exact lookup in the internal dictionary.

    Args:
        word: The word to lemmatize

    Returns:
        The lemma if found in dictionary, None otherwise

    Examples:
        >>> lookup_lemma("kitaplar")
        'kitap'
        >>> lookup_lemma("unknown")
        None
    """
    ...

def strip_suffixes(word: str) -> str:
    """Heuristic suffix stripping for Turkish morphology.

    Tier 2 lemmatization: Rule-based suffix stripping with basic vowel harmony.
    Recursively strips common Turkish suffixes while preventing over-stripping
    of short roots (minimum length constraint).

    Args:
        word: The word to strip suffixes from

    Returns:
        The word with suffixes removed

    Examples:
        >>> strip_suffixes("kitaplardan")
        'kitap'
        >>> strip_suffixes("geliyorum")
        'gel'
    """
    ...

def get_detached_suffixes() -> list[str]:
    """Get embedded detached suffixes list.

    Returns the list of Turkish detached suffixes compiled into the binary
    from resources/tr/labels/DETACHED_SUFFIXES.txt at build time.

    Returns:
        List of detached suffix strings

    Examples:
        >>> suffixes = get_detached_suffixes()
        >>> 'da' in suffixes
        True
        >>> 'de' in suffixes
        True
    """
    ...

def get_stopwords_base() -> list[str]:
    """Get embedded Turkish base stopwords list.

    Returns the base Turkish stopwords compiled into the binary
    from resources/tr/stopwords/base/turkish.txt at build time.

    Returns:
        List of Turkish stopwords

    Examples:
        >>> stopwords = get_stopwords_base()
        >>> 've' in stopwords
        True
        >>> 'ama' in stopwords
        True
    """
    ...

def get_stopwords_metadata() -> str:
    """Get embedded stopwords metadata JSON.

    Returns the stopwords metadata JSON compiled into the binary
    from resources/tr/stopwords/metadata.json at build time.

    Returns:
        JSON string containing stopword metadata

    Examples:
        >>> import json
        >>> metadata = json.loads(get_stopwords_metadata())
        >>> 'sets' in metadata
        True
    """
    ...

def get_stopwords_social_media() -> list[str]:
    """Get embedded social media stopwords.

    Returns the social media domain-specific stopwords compiled into the binary
    from resources/tr/stopwords/domains/social_media.txt at build time.

    Returns:
        List of social media stopwords

    Examples:
        >>> sm_stopwords = get_stopwords_social_media()
        >>> len(sm_stopwords) > 0
        True
    """
    ...

def tokenize_normalized(text: str) -> list[Token]:
    """Tokenize text with normalization and return Token objects with offsets.

    This function combines tokenization and normalization in a single pass,
    returning Token objects that contain the normalized text along with
    character offsets pointing to the original positions in the raw input.

    This is essential for NER and other sequence labeling tasks where you need:
    1. Normalized tokens for model input
    2. Original character positions for label alignment

    The normalization applies Turkish-specific lowercase conversion (İ→i, I→ı)
    while preserving exact offset mapping to the raw text.

    Args:
        text: The text to tokenize and normalize

    Returns:
        List of Token objects with normalized text and original character offsets

    Examples:
        >>> tokens = tokenize_normalized("Ankara'da İstanbul'a gittim.")
        >>> tokens[0].text
        'ankara'
        >>> tokens[0].start
        0
        >>> tokens[0].end
        6
        >>> # Original text can be recovered:
        >>> # text[tokens[0].start:tokens[0].end] == "Ankara"

        >>> # Use case: NER training with normalized input
        >>> tokens = tokenize_normalized("İBB Başkanı Ekrem İmamoğlu")
        >>> # Model sees: ['ibb', 'başkanı', 'ekrem', 'imamoğlu']
        >>> # But labels align with: [(0,3), (4,11), (12,17), (18,26)]
    """
    ...

__all__ = [
    "Token",
    "fast_normalize",
    "tokenize_with_offsets",
    "tokenize_normalized",
    "lookup_lemma",
    "strip_suffixes",
    "get_detached_suffixes",
    "get_stopwords_base",
    "get_stopwords_metadata",
    "get_stopwords_social_media",
]
