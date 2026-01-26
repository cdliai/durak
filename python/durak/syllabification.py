"""
Turkish Syllabification Module

Provides syllable segmentation for Turkish words according to linguistic rules.
Syllabification is fundamental for:
- Prosody research (stress patterns, rhythm analysis)
- Poetry analysis (rhyme detection, meter identification)
- TTS/Speech synthesis (proper pronunciation modeling)
- Educational tools (teaching Turkish syllable structure)
- Morphophonology (understanding vowel harmony and suffix attachment)

Turkish Syllable Structure:
- Structure: (C)(C)V(C)(C) where V is mandatory
- Vowel harmony respected
- Sonority principle for consonant clusters
- Word-final can end in any consonant

Examples:
    kitap       → ki-tap       (CV-CVC)
    merhaba     → mer-ha-ba    (CVC-CV-CV)
    okul        → o-kul        (V-CVC)
    anlamak     → an-la-mak    (VC-CV-CVC)
    İstanbul    → İs-tan-bul   (VC-CVC-CVC)
    karmaşık    → kar-ma-şık   (CVC-CV-CVC)
"""

from dataclasses import dataclass
from typing import Optional

try:
    from durak._durak_core import (
        syllabify as _syllabify_rust,
        syllabify_with_separator as _syllabify_with_separator_rust,
        syllable_count as _syllable_count_rust,
    )
    _RUST_AVAILABLE = True
except ImportError:
    _RUST_AVAILABLE = False


@dataclass
class SyllableInfo:
    """Detailed syllable information for a word.
    
    Attributes:
        word: Original word
        syllables: List of syllables
        count: Number of syllables
        structure: Syllable structure patterns (e.g., ['CV', 'CVC', 'CV'])
        stress_pattern: Stress pattern (0=unstressed, 1=primary stress)
                       In Turkish, primary stress is typically on final syllable
    """
    word: str
    syllables: list[str]
    count: int
    structure: list[str]
    stress_pattern: list[int]


def syllabify(word: str, separator: Optional[str] = None) -> list[str] | str:
    """Syllabify a Turkish word according to linguistic rules.
    
    Args:
        word: Turkish word to syllabify
        separator: If provided, join syllables with this separator and return string
                  If None, return list of syllables
    
    Returns:
        List of syllables if separator is None, otherwise hyphenated string
    
    Examples:
        >>> syllabify("merhaba")
        ['mer', 'ha', 'ba']
        
        >>> syllabify("kitap", separator="-")
        'ki-tap'
        
        >>> syllabify("İstanbul")
        ['İs', 'tan', 'bul']
    
    Raises:
        ValueError: If word is empty or contains non-alphabetic characters
    """
    if not word:
        raise ValueError("Word cannot be empty")
    
    if not _RUST_AVAILABLE:
        raise RuntimeError(
            "Rust syllabification module not available. "
            "Please rebuild the package with: pip install -e ."
        )
    
    if separator is None:
        return _syllabify_rust(word)
    else:
        return _syllabify_with_separator_rust(word, separator)


def count_syllables(word: str) -> int:
    """Count syllables in a Turkish word.
    
    Useful for filtering words by syllable count in poetry analysis.
    
    Args:
        word: Turkish word
    
    Returns:
        Number of syllables
    
    Examples:
        >>> count_syllables("ev")
        1
        
        >>> count_syllables("merhaba")
        3
        
        >>> count_syllables("bilgisayar")
        4
    """
    if not word:
        return 0
    
    if not _RUST_AVAILABLE:
        raise RuntimeError(
            "Rust syllabification module not available. "
            "Please rebuild the package with: pip install -e ."
        )
    
    return _syllable_count_rust(word)


class Syllabifier:
    """Turkish syllabification analyzer with advanced features.
    
    Provides detailed syllable analysis including structure patterns
    and stress detection.
    
    Examples:
        >>> syl = Syllabifier()
        >>> info = syl.analyze("anlamak")
        >>> print(info.syllables)
        ['an', 'la', 'mak']
        >>> print(info.count)
        3
        >>> print(info.stress_pattern)
        [0, 0, 1]  # Primary stress on final syllable
    """
    
    def __init__(self):
        """Initialize syllabifier."""
        if not _RUST_AVAILABLE:
            raise RuntimeError(
                "Rust syllabification module not available. "
                "Please rebuild the package with: pip install -e ."
            )
    
    def analyze(self, word: str) -> SyllableInfo:
        """Analyze syllable structure of a Turkish word.
        
        Args:
            word: Turkish word to analyze
        
        Returns:
            SyllableInfo object with detailed analysis
        
        Examples:
            >>> syl = Syllabifier()
            >>> info = syl.analyze("kitap")
            >>> info.syllables
            ['ki', 'tap']
            >>> info.structure
            ['CV', 'CVC']
            >>> info.stress_pattern
            [0, 1]
        """
        syllables = _syllabify_rust(word)
        count = len(syllables)
        
        # Determine syllable structure (CV, CVC, V, VC, etc.)
        structure = [self._get_structure(syl) for syl in syllables]
        
        # Turkish stress pattern: typically final syllable (exceptions exist)
        # For now, simple rule: last syllable gets primary stress
        stress_pattern = [0] * count
        if count > 0:
            stress_pattern[-1] = 1
        
        return SyllableInfo(
            word=word,
            syllables=syllables,
            count=count,
            structure=structure,
            stress_pattern=stress_pattern,
        )
    
    def count(self, word: str) -> int:
        """Count syllables in a word.
        
        Convenience method, equivalent to count_syllables().
        
        Args:
            word: Turkish word
        
        Returns:
            Number of syllables
        """
        return count_syllables(word)
    
    @staticmethod
    def _get_structure(syllable: str) -> str:
        """Determine the structure pattern of a syllable.
        
        Args:
            syllable: Single syllable
        
        Returns:
            Structure pattern (e.g., 'CV', 'CVC', 'V', 'VC')
        """
        vowels = set('aeıioöuüâîû')
        pattern = []
        
        for char in syllable.lower():
            if char in vowels:
                pattern.append('V')
            elif char.isalpha():
                pattern.append('C')
        
        return ''.join(pattern)


# Convenience exports
__all__ = [
    'syllabify',
    'count_syllables',
    'Syllabifier',
    'SyllableInfo',
]
