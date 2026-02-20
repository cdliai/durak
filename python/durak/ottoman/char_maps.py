"""Character mapping tables for Ottoman Turkish transliteration.

Maps between three layers:
1. Arabic Script (Ottoman Elifba)
2. Scholarly Latin Transliteration (IJMES/İA conventions)
3. Modern Turkish Latin

Includes handling for special diacritics and ambiguous characters.
"""

from __future__ import annotations

# Arabic script to scholarly Latin mapping
# Based on IJMES (International Journal of Middle East Studies) conventions
ARABIC_TO_LATIN: dict[str, str] = {
    # Basic consonants
    "ا": "ā",      # Elif (long a)
    "ب": "b",      # Be
    "پ": "p",      # Pe (Ottoman specific)
    "ت": "t",      # Te
    "ث": "s̱",      # Se (dot below)
    "ج": "c",      # Cim
    "چ": "ç",      # Çim (Ottoman specific)
    "ح": "ḥ",      # Ha (dot below)
    "خ": "ḫ",      # Hı (dot below)
    "د": "d",      # Dal
    "ذ": "ẕ",      # Zel (dot below)
    "ر": "r",      # Re
    "ز": "z",      # Ze
    "ژ": "j",      # Je (Ottoman specific)
    "س": "s",      # Sin
    "ش": "ş",      # Şın
    "ص": "ṣ",      # Sad (dot below)
    "ض": "ḍ",      # Dad (dot below)
    "ط": "ṭ",      # Tı (dot below)
    "ظ": "ẓ",      # Zı (dot below)
    "ع": "ʿ",      # Ayn (half ring)
    "غ": "ġ",      # Gayn (dot above)
    "ف": "f",      # Fe
    "ق": "ḳ",      # Kaf (dot below) - PRIMARY mapping
    "ک": "k",      # Kef (Ottoman variant)
    "گ": "g",      # Gaf (Ottoman specific)
    "ل": "l",      # Lam
    "م": "m",      # Mim
    "ن": "n",      # Nun
    "و": "v",      # Vav (consonant)
    "ه": "h",      # He
    "ی": "ı",      # Ye (Ottoman specific, dotless) → dotless ı
    "ي": "y",      # Ye (dotted)
    
    # Vowels (Ottoman specific)
    "َ": "a",       # Fatha
    "ِ": "i",       # Kesra
    "ُ": "u",       # Damma
    "ْ": "",        # Sukun (no vowel)
    "ّ": "",        # Teshdid (gemination, handled separately)
    "ًا": "an",     # Tenvin
    "ٍ": "in",      # Tenvin kesra
    "ٌ": "un",      # Tenvin damma
    
    # Extended Arabic letters
    "ة": "e",       # Te merbuta
    "ى": "ā",       # Elif mahsura
    "ٱ": "",        # Elif without hemze
}

# Scholarly Latin (with diacritics) to Modern Turkish
SCHOLARLY_TO_MODERN: dict[str, str] = {
    # Dotted consonants → plain
    "ḳ": "k",       # Kaf with dot below
    "ṣ": "s",       # Sad with dot below
    "ḍ": "d",       # Dad with dot below
    "ṭ": "t",       # Tı with dot below
    "ẓ": "z",       # Zı with dot below
    "ḥ": "h",       # Ha with dot below
    "ḫ": "h",       # Hı with dot below
    "ġ": "g",       # Gayn with dot above
    "ẓ": "z",       # Z with dot below (Ottoman ẓ → z)
    "ż": "d",       # Z with dot above → d (for words like ḳāżī → kadı)
    "s̱": "s",       # Se with line below
    "ẕ": "z",       # Zel with line below
    
    # Special characters
    "ʿ": "",        # Ayn (glottal stop, removed in modern)
    "ʾ": "",        # Hemze (removed in modern)
    
    # Long vowels with macrons → plain vowels
    "ā": "a",       # Long a
    "ī": "ı",       # Long i → dotless ı (Turkish)
    "ū": "u",       # Long u
    "ē": "e",       # Long e (rare)
    "ō": "o",       # Long o (rare)
    
    # Other diacritics
    "â": "a",       # Circumflex a
    "î": "i",       # Circumflex i
    "û": "u",       # Circumflex u
    "ê": "e",       # Circumflex e
    "ô": "o",       # Circumflex o
    
    # Regular consonants (pass through)
    "b": "b",
    "p": "p",
    "t": "t",
    "c": "c",
    "ç": "ç",
    "d": "d",
    "r": "r",
    "z": "z",
    "j": "j",
    "s": "s",
    "ş": "ş",
    "f": "f",
    "k": "k",
    "g": "g",
    "l": "l",
    "m": "m",
    "n": "n",
    "v": "v",
    "h": "h",
    "y": "y",
}

# Set of scholarly Latin characters with diacritics (excluding regular Turkish letters)
SCHOLARLY_DIACRITIC_CHARS: set[str] = {
    "ḳ", "ṣ", "ḍ", "ṭ", "ẓ", "ḥ", "ḫ", "ġ", "ẕ", "s̱",
    "ā", "ī", "ū", "ē", "ō",
    "â", "î", "û", "ê", "ô",
    "ʿ", "ʾ",
    "ż",  # Z with dot above
}

# Ambiguous character mappings
# Key Ottoman letter "ك" (kef) can represent multiple sounds
AMBIGUOUS_MAPPINGS: dict[str, list[str]] = {
    "ك": ["k", "g", "n", "y"],  # Kef variants
    "ق": ["k", "g"],            # Kaf variants (regional)
    "غ": ["g", "ğ"],            # Gayn variants
    "و": ["v", "o", "u", "ö", "ü"],  # Vav as consonant or vowel
}

# Context-dependent rules for ambiguous characters
# Format: (preceding_char, arabic_char, following_char) → latin_char
CONTEXT_RULES: list[tuple[str | None, str, str | None, str]] = [
    # Kef at word beginning → k
    (None, "ك", None, "k"),
    (" ", "ك", None, "k"),
    
    # Kef between vowels → g (softening)
    ("a", "ك", "a", "g"),
    ("e", "ك", "e", "g"),
    ("ı", "ك", "ı", "g"),
    ("i", "ك", "i", "g"),
    ("u", "ك", "u", "g"),
    ("ü", "ك", "ü", "g"),
    
    # Kef before front vowels → y
    (None, "ك", "e", "y"),
    (None, "ك", "i", "y"),
    (None, "ك", "ü", "y"),
    
    # Vav as vowel (after consonant, before consonant/end)
    ("b", "و", "r", "o"),  # boru
    ("k", "و", "p", "u"),  # kup
]

# Diacritic decomposition for normalization
# Maps precomposed characters to base + combining diacritic
DIACRITIC_DECOMPOSITION: dict[str, tuple[str, str]] = {
    # Dot below
    "ḳ": ("k", "\u0323"),  # k + combining dot below
    "ṣ": ("s", "\u0323"),
    "ḍ": ("d", "\u0323"),
    "ṭ": ("t", "\u0323"),
    "ẓ": ("z", "\u0323"),
    "ḥ": ("h", "\u0323"),
    "ḫ": ("h", "\u0323"),
    
    # Dot above
    "ġ": ("g", "\u0307"),  # g + combining dot above
    "ż": ("z", "\u0307"),  # z + combining dot above (Ottoman specific)
    
    # Macron
    "ā": ("a", "\u0304"),  # a + combining macron
    "ī": ("i", "\u0304"),
    "ū": ("u", "\u0304"),
    "ē": ("e", "\u0304"),
    "ō": ("o", "\u0304"),
    
    # Circumflex
    "â": ("a", "\u0302"),  # a + combining circumflex
    "î": ("i", "\u0302"),
    "û": ("u", "\u0302"),
    "ê": ("e", "\u0302"),
    "ô": ("o", "\u0302"),
    
    # Half ring (Ayn)
    "ʿ": ("", "\u02BF"),   # modifier letter left half ring
    "ʾ": ("", "\u02BE"),   # modifier letter right half ring
    
    # Line below
    "s̱": ("s", "\u0331"),  # s + combining macron below
    "ẕ": ("z", "\u0331"),
}

# Modern Turkish special characters for reference
MODERN_TURKISH_SPECIAL: set[str] = {
    "ç", "ğ", "ı", "ö", "ş", "ü",
    "Ç", "Ğ", "I", "Ö", "Ş", "Ü",
}

# Ottoman Turkish specific characters (scholarly)
OTTOMAN_SPECIAL: set[str] = set(SCHOLARLY_TO_MODERN.keys()) | {"ā", "ī", "ū", "ʿ", "ʾ"}

# Arabic script range for detection
ARABIC_RANGE = range(0x0600, 0x06FF)  # Arabic block
ARABIC_SUPPLEMENT = range(0x0750, 0x077F)  # Arabic Supplement
ARABIC_EXTENDED_A = range(0x08A0, 0x08FF)  # Arabic Extended-A

def is_arabic_char(char: str) -> bool:
    """Check if character is Arabic script."""
    if not char:
        return False
    code = ord(char)
    return (
        code in ARABIC_RANGE or
        code in ARABIC_SUPPLEMENT or
        code in ARABIC_EXTENDED_A
    )

def contains_arabic(text: str) -> bool:
    """Check if text contains any Arabic characters."""
    return any(is_arabic_char(c) for c in text)

def is_scholarly_latin(char: str) -> bool:
    """Check if character is scholarly Latin with diacritics."""
    return char in OTTOMAN_SPECIAL

def normalize_diacritics(text: str) -> str:
    """Normalize Unicode combining diacritics.
    
    Ensures NFC normalization so characters like ṣ are treated
    as single codepoints rather than s + combining dot.
    """
    import unicodedata
    return unicodedata.normalize("NFC", text)

__all__ = [
    "ARABIC_TO_LATIN",
    "SCHOLARLY_TO_MODERN",
    "AMBIGUOUS_MAPPINGS",
    "CONTEXT_RULES",
    "DIACRITIC_DECOMPOSITION",
    "MODERN_TURKISH_SPECIAL",
    "OTTOMAN_SPECIAL",
    "is_arabic_char",
    "contains_arabic",
    "is_scholarly_latin",
    "normalize_diacritics",
]