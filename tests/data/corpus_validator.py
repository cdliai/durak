"""Lightweight corpus validator for Turkish-specific sanity checks."""

from __future__ import annotations

import re
from collections.abc import Iterable

from durak.cleaning import clean_text
from durak.stopwords import StopwordManager

TURKISH_DIACRITICS = {"ç", "ğ", "ı", "ö", "ş", "ü"}
PARTICLE_TOKENS = {"de", "da", "ki", "mi"}


def normalize_sentence(sentence: str) -> str:
    """Prepare sentences by stripping trailing whitespace and collapsing spaces."""
    return " ".join(sentence.strip().split())


def validate_corpus(sentences: Iterable[str]) -> list[str]:
    """Run sanity checks on iterable sentences"""
    manager = StopwordManager()
    issues: list[str] = []
    for index, sentence in enumerate(sentences):
        if not sentence or sentence.lstrip().startswith("#"):
            continue
        original = normalize_sentence(sentence)
        cleaned = clean_text(original)
        stripped_tokens = [
            token.strip(".,!?;:\"'()[]{}")
            for token in cleaned.split()
            if token.strip(".,!?;:\"'()[]{}")
        ]
        lowered_original = original.lower()

        for diacritic in TURKISH_DIACRITICS:
            if diacritic in lowered_original and diacritic not in cleaned:
                issues.append(
                    f"Sentence {index}: diacritic '{diacritic}' lost after cleaning."
                )

        for particle in PARTICLE_TOKENS:
            if (
                re.search(rf"\b{particle}\b", lowered_original)
                and particle not in stripped_tokens
            ):
                issues.append(
                    f"Sentence {index}: particle '{particle}' missing post-cleaning."
                )

        for token in stripped_tokens:
            if token in PARTICLE_TOKENS:
                continue
            for particle in PARTICLE_TOKENS:
                if token.endswith(particle) and manager.is_stopword(token):
                    issues.append(f"Sentence {index}: token '{token}' -> '{particle}'.")
                    break

    return issues
