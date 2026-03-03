"""Utilities for handling detached Turkish suffix tokens."""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from durak.exceptions import ResourceError
from durak.resources_provider import DEFAULT_RESOURCE_PROVIDER

try:
    APOSTROPHE_TOKENS: tuple[str, ...] = DEFAULT_RESOURCE_PROVIDER.load_apostrophes()
except ResourceError:
    # Conservative fallback to keep suffix attachment usable if config is missing.
    APOSTROPHE_TOKENS = ("'",)


def _load_detached_suffixes() -> tuple[str, ...]:
    """Load detached suffixes through the centralized resource provider."""
    return DEFAULT_RESOURCE_PROVIDER.load_detached_suffixes()


DEFAULT_DETACHED_SUFFIXES = _load_detached_suffixes()

# Joining detached suffixes is intentionally conservative:
# these tokens are often function words or quoted particles, not suffix bases.
NON_JOINABLE_BASES: frozenset[str] = frozenset(
    {
        "ve",
        "de",
        "da",
        "ki",
        "mi",
        "mı",
        "mu",
        "mü",
        "ile",
        "ama",
        "fakat",
        "lakin",
        "ben",
        "sen",
        "o",
        "bu",
        "şu",
        "biz",
        "siz",
        "onlar",
    }
)


def _has_alpha(token: str | None) -> bool:
    return bool(token) and any(char.isalpha() for char in (token or ""))


def _matches_suffix(token: str | None, suffixes: set[str]) -> bool:
    if not token:
        return False
    normalized = token.lower()
    return normalized in suffixes


def _is_joinable_base(token: str | None, *, safe_mode: bool) -> bool:
    if not _has_alpha(token):
        return False
    if not safe_mode:
        return True
    assert token is not None
    normalized = token.lower()
    if normalized in NON_JOINABLE_BASES:
        return False
    # Very short tokens are frequently particles/abbreviations in noisy corpora.
    return len(normalized) >= 3


def attach_detached_suffixes(
    tokens: Sequence[str] | None,
    *,
    suffixes: Iterable[str] | None = None,
    allow_without_apostrophe: bool = False,
    safe_mode: bool = True,
    apostrophes: Iterable[str] | None = None,
) -> list[str]:
    """Join detached suffix tokens with their preceding base token.

    Examples:
        >>> attach_detached_suffixes(["ankara", "'", "da"])
        ["ankara'da"]
        >>> attach_detached_suffixes(["ankara", "da"], allow_without_apostrophe=True)
        ['ankarada']
    """
    if not tokens:
        return []

    suffix_set = {suffix.lower() for suffix in (suffixes or DEFAULT_DETACHED_SUFFIXES)}
    if apostrophes is not None:
        apostrophe_set = tuple(apostrophes)
    else:
        apostrophe_set = APOSTROPHE_TOKENS

    merged: list[str] = []
    index = 0

    while index < len(tokens):
        current = tokens[index]

        if not _has_alpha(current):
            merged.append(current)
            index += 1
            continue

        next_index = index + 1
        apostrophe_index = index + 2

        if (
            next_index < len(tokens)
            and _is_joinable_base(current, safe_mode=safe_mode)
            and tokens[next_index] in apostrophe_set
            and apostrophe_index < len(tokens)
            and _matches_suffix(tokens[apostrophe_index], suffix_set)
        ):
            combined = f"{current}{tokens[next_index]}{tokens[apostrophe_index]}"
            merged.append(combined)
            index += 3
            continue

        if (
            allow_without_apostrophe
            and next_index < len(tokens)
            and _is_joinable_base(current, safe_mode=safe_mode)
            and _matches_suffix(tokens[next_index], suffix_set)
        ):
            combined = f"{current}{tokens[next_index]}"
            merged.append(combined)
            index += 2
            continue

        merged.append(current)
        index += 1

    return merged


__all__ = [
    "APOSTROPHE_TOKENS",
    "DEFAULT_DETACHED_SUFFIXES",
    "attach_detached_suffixes",
]
