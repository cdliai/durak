from __future__ import annotations

from typing import Literal

try:
    from durak._durak_core import lookup_lemma, strip_suffixes
except ImportError:
    def lookup_lemma(word: str) -> str | None:
        raise ImportError("Rust extension not installed")
    def strip_suffixes(word: str) -> str:
        raise ImportError("Rust extension not installed")

Strategy = Literal["lookup", "heuristic", "hybrid"]

class Lemmatizer:
    """
    Tiered Lemmatizer backed by Rust.
    
    Strategies:
    - lookup: Use only the exact dictionary 
      (fastest, high precision, low recall on OOV).
    - heuristic: Use only suffix stripping (fast, works on OOV, lower precision).
    - hybrid: Try lookup first, fallback to heuristic (default).
    """
    def __init__(self, strategy: Strategy = "hybrid"):
        self.strategy = strategy

    def __call__(self, word: str) -> str:
        if not word:
            return ""
            
        # Tier 1: Lookup
        if self.strategy in ("lookup", "hybrid"):
            lemma = lookup_lemma(word)
            if lemma is not None:
                return lemma
            if self.strategy == "lookup":
                return word  # Return as-is if not found

        # Tier 2: Heuristic
        if self.strategy in ("heuristic", "hybrid"):
            return strip_suffixes(word)
            
        return word

    def __repr__(self) -> str:
        return f"Lemmatizer(strategy='{self.strategy}')"
