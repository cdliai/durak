"""Type stubs for the _durak_core Rust extension module.

This module provides high-performance Rust implementations of core NLP operations
for Turkish text processing.
"""

from __future__ import annotations

def fast_normalize(text: str, lowercase: bool = True, handle_turkish_i: bool = True) -> str:
    """Fast normalization for Turkish text.

    Handles Turkish-specific I/ı and İ/i conversion correctly with configurable options.
    This is a high-performance Rust implementation with single-pass allocation.

    Args:
        text: The text to normalize
        lowercase: If True, convert to lowercase (default: True)
        handle_turkish_i: If True, handle Turkish I/ı and İ/i conversion (default: True)

    Returns:
        Normalized text with correct Turkish character handling

    Examples:
        >>> fast_normalize("ISTANBUL")
        'istanbul'
        >>> fast_normalize("İSTANBUL")
        'istanbul'
        >>> fast_normalize("İSTANBUL", lowercase=False)
        'İSTANBUL'
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

    Tier 1 lemmatization: Fast exact lookup in the embedded Turkish lemma dictionary.
    The dictionary contains 1,362+ inflected forms mapped to their base lemmas,
    loaded from resources/tr/lemmas/turkish_lemma_dict.txt at build time.

    Coverage:
    - High-frequency nouns with case/plural suffixes
    - Common verb inflections (tense, aspect, person markers)
    - Systematic vowel harmony patterns (front/back vowel classes)

    Args:
        word: The inflected word to lemmatize

    Returns:
        The base lemma if found in dictionary, None otherwise

    Examples:
        >>> lookup_lemma("kitaplar")
        'kitap'
        >>> lookup_lemma("geliyorum")
        'gel'
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

def strip_suffixes_validated(
    word: str,
    strict: bool = False,
    min_root_length: int = 2,
    check_harmony: bool = True
) -> str:
    """Strip suffixes with root validation and morphotactic constraints.

    Advanced lemmatization that validates candidate roots against a dictionary,
    checks vowel harmony, and ensures morphologically valid suffix ordering.
    Prevents over-stripping by applying multiple validation layers.

    Args:
        word: The word to process
        strict: If True, check dictionary first; if False, use phonotactic rules only
        min_root_length: Minimum acceptable root length (default: 2)
        check_harmony: If True, validate vowel harmony before stripping (default: True)

    Returns:
        The word with validated suffix stripping

    Examples:
        >>> strip_suffixes_validated("kitaplardan")
        'kitap'
        >>> strip_suffixes_validated("geliyorum", strict=True)
        'gel'
        >>> strip_suffixes_validated("evlerimizden", check_harmony=True)
        'ev'
    """
    ...

def check_vowel_harmony_py(root: str, suffix: str) -> bool:
    """Check if a suffix harmonizes with a root word.

    Validates Turkish vowel harmony rules between a root word and a suffix.
    Turkish vowel harmony requires suffixes to match the vowel category
    (front/back and rounded/unrounded) of the root word's last vowel.

    Args:
        root: The root word to check
        suffix: The suffix to validate against the root

    Returns:
        True if the suffix harmonizes with the root, False otherwise

    Examples:
        >>> check_vowel_harmony_py("ev", "ler")  # Back vowel + front vowel suffix
        False
        >>> check_vowel_harmony_py("ev", "lar")  # Back vowel + back vowel suffix
        True
        >>> check_vowel_harmony_py("kitap", "de")
        True
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
    "strip_suffixes_validated",
    "check_vowel_harmony_py",
    "get_detached_suffixes",
    "get_stopwords_base",
    "get_stopwords_metadata",
    "get_stopwords_social_media",
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
