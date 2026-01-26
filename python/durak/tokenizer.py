"""Tokenizer utilities for Durak."""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass

from durak.cleaning import normalize_case

# Regex patterns tuned for Turkish tokenisation.
APOSTROPHE_TOKEN = r"[A-Za-zÇĞİÖŞÜçğıöşü]+(?:'[A-Za-zÇĞİÖŞÜçğıöşü]+)?"
NUMBER_TOKEN = r"\d+(?:[.,]\d+)*(?:[-–]\d+)?"
URL_TOKEN = r"https?://[^\s]+|www\.[^\s]+"
EMOTICON_TOKEN = r"[:;=8][-^']?[)DPOo(\[/\\]"
WORD_TOKEN = r"[A-Za-zÇĞİÖŞÜçğıöşü]+(?:-[A-Za-zÇĞİÖŞÜçğıöşü]+)*"
PUNCT_TOKEN = r"[^\w\s]"

REGEX_TOKEN_PATTERN = re.compile(
    f"({URL_TOKEN}|{EMOTICON_TOKEN}|{APOSTROPHE_TOKEN}|{NUMBER_TOKEN}|{WORD_TOKEN}|{PUNCT_TOKEN})",
    flags=re.UNICODE,
)

SENTENCE_END_PATTERN = re.compile(r"([.!?…]+)(\s+|$)")
ABBREVIATIONS = {
    "dr.",
    "prof.",
    "doç.",
    "alb.",
    "sn.",
    "mr.",
    "mrs.",
    "ms.",
}


class TokenizationError(RuntimeError):
    """Raised when tokenization strategies encounter unexpected errors."""


Tokenizer = Callable[[str], list[str]]
SentenceSplitter = Callable[[str], list[str]]

TOKENIZER_REGISTRY: dict[str, Tokenizer] = {}
SENTENCE_SPLITTER_REGISTRY: dict[str, SentenceSplitter] = {}


def register_tokenizer(name: str, func: Tokenizer) -> None:
    TOKENIZER_REGISTRY[name] = func


def register_sentence_splitter(name: str, func: SentenceSplitter) -> None:
    SENTENCE_SPLITTER_REGISTRY[name] = func


def regex_tokenize(text: str) -> list[str]:
    """Tokenize text using regex patterns."""
    matches = REGEX_TOKEN_PATTERN.findall(text)
    return [match for match in matches if match.strip()]


def regex_sentence_split(text: str | None) -> list[str]:
    """Split text into sentences using regex patterns.
    Args:
        text: Input text to split, can be None
    Returns:
        List of sentences
    """
    if text is None:
        return []
    sentences: list[str] = []
    start = 0
    for match in SENTENCE_END_PATTERN.finditer(text):
        end = match.end()
        candidate = text[start:end].strip()
        if not candidate:
            start = end
            continue
        lower_candidate = candidate.lower()
        if lower_candidate.split()[-1] in ABBREVIATIONS:
            continue
        sentences.append(candidate)
        start = end
    if start < len(text):
        remainder = text[start:].strip()
        if remainder:
            sentences.append(remainder)
    return sentences


register_tokenizer("regex", regex_tokenize)
register_sentence_splitter("regex", regex_sentence_split)


def tokenize(
    text: str | None,
    *,
    strategy: str = "regex",
    strip_punct: bool = False,
) -> list[str]:
    """Tokenize text with optional punctuation stripping.

    Examples:
        >>> tokenize("Durak, kolay mı?", strip_punct=True)
        ['Durak', 'kolay', 'mı']
    """
    if text is None:
        return []
    tokenizer = TOKENIZER_REGISTRY.get(strategy)
    if tokenizer is None:
        raise TokenizationError(f"Unknown tokenizer strategy '{strategy}'.")
    tokens = tokenizer(text)
    if strip_punct:
        tokens = [token for token in tokens if not re.fullmatch(PUNCT_TOKEN, token)]
    return tokens


def tokenize_text(
    text: str | None,
    strategy: str = "regex",
    *,
    strip_punct: bool = False,
) -> list[str]:
    """Backward-compatible wrapper around :func:`tokenize`.

    Examples:
        >>> tokenize_text("Durak, kolay mı?", strip_punct=True)
        ['Durak', 'kolay', 'mı']
    """
    return tokenize(text, strategy=strategy, strip_punct=strip_punct)


def split_sentences(text: str, strategy: str = "regex") -> list[str]:
    splitter = SENTENCE_SPLITTER_REGISTRY.get(strategy)
    if splitter is None:
        raise TokenizationError(f"Unknown sentence splitter strategy '{strategy}'.")
    return splitter(text)





try:
    from . import _durak_core
    tokenize_with_offsets = _durak_core.tokenize_with_offsets
    tokenize_with_normalized_offsets = _durak_core.tokenize_with_normalized_offsets
except ImportError:
    def tokenize_with_offsets(text: str) -> list[tuple[str, int, int]]:
        raise ImportError("Rust extension not installed")
    
    def tokenize_with_normalized_offsets(text: str) -> list[tuple[str, int, int]]:
        raise ImportError("Rust extension not installed")


def normalize_tokens(
    tokens: Iterable[str],
    *,
    lower: bool = True,
    strip_punct: bool = False,
) -> list[str]:
    normalized: list[str] = []
    for token in tokens:
        if strip_punct and re.fullmatch(PUNCT_TOKEN, token):
            continue
        normalized_token = normalize_case(token, mode="lower") if lower else token
        normalized.append(normalized_token)
    return normalized


@dataclass
class SubwordTokenizer:
    """Placeholder interface for future subword tokenizers."""

    name: str

    def tokenize(self, tokens: Sequence[str]) -> Sequence[str]:
        raise NotImplementedError("Subword tokenizers are not implemented yet.")
