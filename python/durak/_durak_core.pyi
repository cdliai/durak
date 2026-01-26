"""Type stubs for the _durak_core Rust extension module.

This module provides high-performance Rust implementations of core NLP operations
for Turkish text processing.
"""

from __future__ import annotations

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

__all__ = [
    "fast_normalize",
    "tokenize_with_offsets",
    "lookup_lemma",
    "strip_suffixes",
    "get_detached_suffixes",
    "get_stopwords_base",
    "get_stopwords_metadata",
    "get_stopwords_social_media",
    "get_build_info",
    "get_resource_info",
    "get_build_info",
    "get_resource_info",
]

def get_build_info() -> Dict[str, str]:
    """Get Durak build information for reproducibility.
    
    Returns build metadata including package version, build date, and
    package name for research reproducibility tracking.
    
    Returns:
        Dictionary with keys: durak_version, build_date, package_name
    
    Examples:
        >>> info = get_build_info()
        >>> print(info['durak_version'])
        '0.4.0'
    """
    ...

def get_resource_info() -> Dict[str, Dict[str, str]]:
    """Get embedded resource versions and checksums.
    
    Returns metadata for all linguistic resources embedded in the binary,
    including versions, SHA256 checksums, item counts, and update dates.
    
    Returns:
        Dictionary mapping resource names to their metadata
    
    Examples:
        >>> resources = get_resource_info()
        >>> print(resources['stopwords_base']['checksum'][:12])
        '361908bbb0a4'
        >>> print(resources['stopwords_base']['item_count'])
        '118'
    """
    ...
