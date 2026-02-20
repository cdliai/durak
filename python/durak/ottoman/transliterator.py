"""Ottoman Turkish transliterator with offset preservation.

Translates between three layers:
1. Arabic Script (Ottoman Elifba)
2. Scholarly Latin Transliteration
3. Modern Turkish Latin

Critical feature: Preserves character offsets for mapping back to original
document positions (needed for Ottoman Miner's bounding box alignment).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator

from .char_maps import (
    ARABIC_TO_LATIN,
    SCHOLARLY_TO_MODERN,
    AMBIGUOUS_MAPPINGS,
    CONTEXT_RULES,
    contains_arabic,
    is_arabic_char,
    normalize_diacritics,
)


@dataclass
class TransliterationMapping:
    """Mapping between original and transliterated text with offset tracking.
    
    Attributes:
        original: Original text (Arabic or scholarly Latin)
        transliterated: Transliterated text (Modern Turkish)
        char_mappings: List of (original_start, original_end, transliterated_start, transliterated_end)
        ambiguous_chars: List of positions where ambiguous character choices were made
    """
    original: str
    transliterated: str
    char_mappings: list[tuple[int, int, int, int]] = field(default_factory=list)
    ambiguous_chars: list[tuple[int, str, str]] = field(default_factory=list)
    
    def get_original_offset(self, transliterated_pos: int) -> int:
        """Get original character offset from transliterated position.
        
        Args:
            transliterated_pos: Position in transliterated text
            
        Returns:
            Position in original text
            
        Example:
            >>> mapping = transliterator.transliterate("ḳāżī")
            >>> mapping.get_original_offset(0)  # Position of 'k' in "kadı"
            0  # Position of 'ḳ' in "ḳāżī"
        """
        for orig_start, orig_end, trans_start, trans_end in self.char_mappings:
            if trans_start <= transliterated_pos < trans_end:
                # Calculate relative position within the mapping
                relative_pos = transliterated_pos - trans_start
                # Map back to original (may be multi-character to single)
                orig_len = orig_end - orig_start
                if orig_len == 1:
                    return orig_start
                else:
                    # Approximate: return start of original range
                    return orig_start
            elif trans_start > transliterated_pos:
                break
        return -1  # Not found
    
    def get_transliterated_offset(self, original_pos: int) -> int:
        """Get transliterated character offset from original position.
        
        Args:
            original_pos: Position in original text
            
        Returns:
            Position in transliterated text
        """
        for orig_start, orig_end, trans_start, trans_end in self.char_mappings:
            if orig_start <= original_pos < orig_end:
                return trans_start
            elif orig_start > original_pos:
                break
        return -1
    
    def get_token_offsets(self, token_start: int, token_end: int) -> tuple[int, int]:
        """Get original text offsets for a token span.
        
        Args:
            token_start: Start position in transliterated text
            token_end: End position in transliterated text
            
        Returns:
            (original_start, original_end)
            
        Example:
            >>> # Token "kadı" at positions 0-4 in transliterated text
            >>> mapping.get_token_offsets(0, 4)
            (0, 4)  # Corresponding positions in "ḳāżī"
        """
        orig_start = self.get_original_offset(token_start)
        # For end, we want the position after the last character
        orig_end = self.get_original_offset(token_end - 1)
        if orig_end >= 0:
            # Find the end of this character mapping
            for o_start, o_end, t_start, t_end in self.char_mappings:
                if t_start <= token_end - 1 < t_end:
                    orig_end = o_end
                    break
        return (orig_start, orig_end)


class OttomanTransliterator:
    """Transliterator for Ottoman Turkish with offset preservation.
    
    Handles conversion between:
    - Arabic script (Ottoman Elifba)
    - Scholarly Latin transliteration (with diacritics)
    - Modern Turkish Latin
    
    Preserves character offsets for mapping back to original document positions.
    
    Example:
        >>> transliterator = OttomanTransliterator()
        >>> 
        >>> # Arabic to Modern Turkish
        >>> mapping = transliterator.arabic_to_modern("قاضی")
        >>> print(mapping.transliterated)  # "kadı"
        >>> print(mapping.get_original_offset(0))  # 0 (points to 'ق')
        
        >>> # Scholarly to Modern Turkish
        >>> mapping = transliterator.scholarly_to_modern("ḳāżī")
        >>> print(mapping.transliterated)  # "kadı"
        >>> print(mapping.get_token_offsets(0, 4))  # (0, 4)
    """
    
    def __init__(
        self,
        use_context_rules: bool = True,
        preserve_diacritics: bool = False,
    ):
        """Initialize transliterator.
        
        Args:
            use_context_rules: Apply contextual rules for ambiguous characters
            preserve_diacritics: Keep diacritics in output (for scholarly mode)
        """
        self.use_context_rules = use_context_rules
        self.preserve_diacritics = preserve_diacritics
    
    def arabic_to_latin(self, text: str) -> TransliterationMapping:
        """Convert Arabic script to scholarly Latin transliteration.
        
        Args:
            text: Arabic script text
            
        Returns:
            TransliterationMapping with offsets
        """
        text = normalize_diacritics(text)
        
        transliterated_chars = []
        mappings = []
        ambiguous = []
        
        i = 0
        while i < len(text):
            char = text[i]
            
            # Check for Arabic character
            if is_arabic_char(char):
                # Get preceding and following for context
                prev_char = text[i - 1] if i > 0 else None
                next_char = text[i + 1] if i < len(text) - 1 else None
                
                # Try context rules first for ambiguous characters
                latin_char = self._apply_context_rules(prev_char, char, next_char)
                
                if latin_char is None:
                    # Use direct mapping
                    latin_char = ARABIC_TO_LATIN.get(char, char)
                
                # Record ambiguous character if applicable
                if char in AMBIGUOUS_MAPPINGS:
                    ambiguous.append((i, char, latin_char))
                
                # Record mapping
                trans_start = len("".join(transliterated_chars))
                transliterated_chars.append(latin_char)
                trans_end = len("".join(transliterated_chars))
                
                mappings.append((i, i + 1, trans_start, trans_end))
                i += 1
            else:
                # Non-Arabic character (space, punctuation, etc.)
                # Pass through but record mapping
                trans_start = len("".join(transliterated_chars))
                transliterated_chars.append(char)
                trans_end = len("".join(transliterated_chars))
                
                mappings.append((i, i + 1, trans_start, trans_end))
                i += 1
        
        return TransliterationMapping(
            original=text,
            transliterated="".join(transliterated_chars),
            char_mappings=mappings,
            ambiguous_chars=ambiguous,
        )
    
    def scholarly_to_modern(self, text: str) -> TransliterationMapping:
        """Convert scholarly Latin to Modern Turkish.
        
        Args:
            text: Scholarly Latin text with diacritics (e.g., "ḳāżī")
            
        Returns:
            TransliterationMapping with offsets
        """
        text = normalize_diacritics(text)
        
        # Build result incrementally
        result_chars = []
        mappings = []
        
        i = 0
        while i < len(text):
            char = text[i]
            
            # Check if this character has a direct mapping
            if char in SCHOLARLY_TO_MODERN:
                modern = SCHOLARLY_TO_MODERN[char]
                
                if self.preserve_diacritics and modern == "":
                    # Keep original if preserving and would be removed
                    modern = char
                
                # Record mapping
                trans_start = len("".join(result_chars))
                result_chars.append(modern)
                trans_end = len("".join(result_chars))
                mappings.append((i, i + 1, trans_start, trans_end))
            else:
                # Pass through unchanged (regular Latin letters, spaces, etc.)
                trans_start = len("".join(result_chars))
                result_chars.append(char)
                trans_end = len("".join(result_chars))
                mappings.append((i, i + 1, trans_start, trans_end))
            
            i += 1
        
        return TransliterationMapping(
            original=text,
            transliterated="".join(result_chars),
            char_mappings=mappings,
        )
    
    def arabic_to_modern(self, text: str) -> TransliterationMapping:
        """Convert Arabic script directly to Modern Turkish.
        
        This is a two-step process with combined offset tracking.
        
        Args:
            text: Arabic script text
            
        Returns:
            TransliterationMapping with offsets to original Arabic
        """
        # First: Arabic → Scholarly Latin
        scholarly_mapping = self.arabic_to_latin(text)
        
        # Second: Scholarly Latin → Modern Turkish
        modern_mapping = self.scholarly_to_modern(scholarly_mapping.transliterated)
        
        # Combine mappings: original Arabic → Modern Turkish
        combined_mappings = []
        for orig_start, orig_end, schol_start, schol_end in scholarly_mapping.char_mappings:
            # Find corresponding modern positions
            modern_start = modern_mapping.get_transliterated_offset(schol_start)
            modern_end = modern_mapping.get_transliterated_offset(schol_end - 1)
            if modern_end >= 0:
                # Find the actual end position
                for s, e, ms, me in modern_mapping.char_mappings:
                    if s == schol_end - 1:
                        modern_end = me
                        break
            
            if modern_start >= 0:
                combined_mappings.append((orig_start, orig_end, modern_start, modern_end))
        
        return TransliterationMapping(
            original=text,
            transliterated=modern_mapping.transliterated,
            char_mappings=combined_mappings,
            ambiguous_chars=scholarly_mapping.ambiguous_chars,
        )
    
    def auto_transliterate(self, text: str) -> TransliterationMapping:
        """Auto-detect script and transliterate to Modern Turkish.
        
        Detects if text is Arabic script or scholarly Latin and
        applies appropriate conversion.
        
        Args:
            text: Mixed or unknown script text
            
        Returns:
            TransliterationMapping
        """
        text = normalize_diacritics(text)
        
        if contains_arabic(text):
            return self.arabic_to_modern(text)
        else:
            # Assume scholarly Latin or already modern
            return self.scholarly_to_modern(text)
    
    def _apply_context_rules(
        self,
        prev_char: str | None,
        char: str,
        next_char: str | None,
    ) -> str | None:
        """Apply contextual rules for ambiguous characters.
        
        Args:
            prev_char: Preceding character (or None)
            char: Current character (Arabic)
            next_char: Following character (or None)
            
        Returns:
            Latin character if rule matches, None otherwise
        """
        if not self.use_context_rules:
            return None
        
        # Normalize previous character to Latin if it's Arabic
        prev_latin = ARABIC_TO_LATIN.get(prev_char, prev_char) if prev_char else None
        next_latin = ARABIC_TO_LATIN.get(next_char, next_char) if next_char else None
        
        # Extract just the base letter from Latin (remove diacritics)
        def get_base(char):
            if not char:
                return None
            # Simple heuristic: take first character if multi-char
            return char[0] if len(char) > 0 else char
        
        prev_base = get_base(prev_latin)
        next_base = get_base(next_latin)
        
        for rule_prev, rule_char, rule_next, result in CONTEXT_RULES:
            if rule_char != char:
                continue
            
            # Check preceding character
            if rule_prev is not None:
                if rule_prev == " " and prev_char != " ":
                    continue
                elif prev_base != rule_prev and prev_char != rule_prev:
                    continue
            
            # Check following character
            if rule_next is not None:
                if next_base != rule_next and next_char != rule_next:
                    continue
            
            return result
        
        return None


def ottoman_to_modern(text: str) -> str:
    """Convenience function: Convert Ottoman text to Modern Turkish.
    
    Auto-detects input script and applies appropriate conversion.
    
    Args:
        text: Ottoman text (Arabic script or scholarly Latin)
        
    Returns:
        Modern Turkish text
        
    Example:
        >>> ottoman_to_modern("قاضی")
        'kadı'
        >>> ottoman_to_modern("ḳāżī")
        'kadı'
    """
    transliterator = OttomanTransliterator()
    mapping = transliterator.auto_transliterate(text)
    return mapping.transliterated


__all__ = [
    "OttomanTransliterator",
    "TransliterationMapping",
    "ottoman_to_modern",
]