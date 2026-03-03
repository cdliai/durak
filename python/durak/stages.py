"""Dedicated stage callables used by the Pipeline orchestrator."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from durak.cleaning import clean_text
from durak.normalizer import Normalizer
from durak.stopwords import remove_stopwords as remove_stopwords_fn
from durak.suffixes import attach_detached_suffixes
from durak.tokenizer import tokenize

_NORMALIZER = Normalizer()


def clean_stage(text: str) -> str:
    cleaned = clean_text(text)
    if isinstance(cleaned, tuple):
        return cleaned[0]
    return cleaned


def normalize_stage(text: str) -> str:
    return _NORMALIZER(text)


def tokenize_stage(text: str) -> list[str]:
    return tokenize(text)


def remove_stopwords_stage(tokens: list[str]) -> list[str]:
    return remove_stopwords_fn(tokens)


def attach_suffixes_stage(tokens: list[str]) -> list[str]:
    return attach_detached_suffixes(
        tokens,
        allow_without_apostrophe=False,
        safe_mode=True,
    )


STEP_REGISTRY: dict[str, Callable[..., Any]] = {
    "clean": clean_stage,
    "normalize": normalize_stage,
    "tokenize": tokenize_stage,
    "remove_stopwords": remove_stopwords_stage,
    "attach_suffixes": attach_suffixes_stage,
}

__all__ = ["STEP_REGISTRY"]
