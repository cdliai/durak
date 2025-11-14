"""Text cleaning utilities for Durak."""

from __future__ import annotations

import html
import re
import unicodedata
from collections.abc import Iterable
from functools import partial
from typing import Callable

# Common stylistic variants mapped to ASCII or Turkish canonical characters.
UNICODE_REPLACEMENTS = {
    "\u2018": "'",
    "\u2019": "'",
    "\u201c": '"',
    "\u201d": '"',
    "\u2014": "-",
    "\u2013": "-",
    "\u00a0": " ",
}

# Replace script/style blocks before stripping tags to avoid leaking JS/CSS.
SCRIPT_STYLE_PATTERN = re.compile(
    r"<(script|style).*?>.*?</\1>", flags=re.IGNORECASE | re.DOTALL
)
TAG_PATTERN = re.compile(r"<[^>]+>")
URL_PATTERN = re.compile(r"(?P<url>(https?://|www\.)[^\s]+)", flags=re.IGNORECASE)
MENTION_PATTERN = re.compile(r"(?<!\w)@[^\s#@]+", flags=re.UNICODE)
HASHTAG_PATTERN = re.compile(r"(?<!\w)#[^\s#@]+", flags=re.UNICODE)
WHITESPACE_PATTERN = re.compile(r"\s+")

TRAILING_PUNCTUATION = {".", ",", "!", "?", ";", ":"}


def normalize_unicode(text: str) -> str:
    """Apply NFC normalization and map variants to standard characters.
    Args:
        text: The text to normalize.
    Returns:
        The normalized text.
    """
    if not text:
        return ""
    normalized = unicodedata.normalize("NFC", text)
    translation_table = str.maketrans(UNICODE_REPLACEMENTS)
    return normalized.translate(translation_table)


def strip_html(text: str) -> str:
    """Remove HTML tags, script/style content, and unescape HTML entities.
    Args:
        text: The text to strip HTML from.
    Returns:
        The text with HTML removed.
    """
    if not text:
        return ""
    without_blocks = SCRIPT_STYLE_PATTERN.sub(" ", text)
    without_tags = TAG_PATTERN.sub(" ", without_blocks)
    unescaped = html.unescape(without_tags)
    return collapse_whitespace(unescaped)


def collapse_whitespace(text: str) -> str:
    """Collapse consecutive whitespace characters into a single space.
    Args:
        text: The text to collapse whitespace in.
    Returns:
        The text with whitespace collapsed.
    """
    if not text:
        return ""
    collapsed = WHITESPACE_PATTERN.sub(" ", text).strip()
    return re.sub(r"\s+([.,!?;:])", r"\1", collapsed)


def normalize_case(text: str, mode: str = "lower") -> str:
    """Normalize text casing with Turkish dotted/undotted I awareness.
    Args:
        text: The text to normalize.
        mode: The normalization mode. Can be "lower", "upper", or "none".
            Defaults to "lower".
    Returns:
        The normalized text.
    Raises:
        ValueError: If an unsupported mode is provided.
    """
    if not text or mode == "none":
        return text

    if mode == "lower":
        adjusted = (
            text.replace("I", "ı")
            .replace("İ", "i")
            .replace("Â", "â")
            .replace("Î", "î")
            .replace("Û", "û")
        )
        return adjusted.lower()
    if mode == "upper":
        adjusted = (
            text.replace("i", "İ")
            .replace("ı", "I")
            .replace("â", "Â")
            .replace("î", "Î")
            .replace("û", "Û")
        )
        return adjusted.upper()

    raise ValueError(
        f"Unsupported mode '{mode}'. Expected 'lower', 'upper', or 'none'."
    )


def _strip_trailing_punctuation(match: re.Match[str]) -> str:
    """Helper that preserves punctuation immediately following a URL."""
    url = match.group("url")
    trailing = ""
    while url and url[-1] in TRAILING_PUNCTUATION:
        trailing = url[-1] + trailing
        url = url[:-1]
    return trailing


def remove_urls(text: str) -> str:
    """Remove HTTP(S) and www-prefixed URLs while keeping trailing punctuation.
    Args:
        text: The text to remove URLs from.
    Returns:
        The text with URLs removed.
    """
    if not text:
        return ""
    cleaned = URL_PATTERN.sub(_strip_trailing_punctuation, text)
    return collapse_whitespace(cleaned)


def remove_mentions_hashtags(text: str, *, keep_hash: bool = False) -> str:
    """Remove @mentions and hashtags.
    Args:
        text: The text to remove mentions and hashtags from.
        keep_hash: Whether to keep the hashtag symbol. Defaults to False.
    Returns:
        The text with mentions and hashtags removed.
    """
    if not text:
        return ""
    without_mentions = MENTION_PATTERN.sub(" ", text)

    def hashtag_replacer(match: re.Match[str]) -> str:
        keyword = match.group(0)[1:]
        return keyword if keep_hash else " "

    without_hashtags = HASHTAG_PATTERN.sub(hashtag_replacer, without_mentions)
    return collapse_whitespace(without_hashtags)


def remove_repeated_chars(text: str, *, max_repeats: int = 2) -> str:
    """Limit elongated characters and emojis to a maximum repeat threshold.
    Args:
        text: The text to remove repeated characters from.
        max_repeats: The maximum number of times a character can be repeated.
            Defaults to 2.
    Returns:
        The text with repeated characters removed.
    Raises:
        ValueError: If max_repeats is less than 1.
    """
    if not text:
        return ""
    if max_repeats < 1:
        raise ValueError("max_repeats must be >= 1")

    pattern = re.compile(rf"(.)\1{{{max_repeats},}}")

    def replacer(match: re.Match[str]) -> str:
        char = match.group(1)
        return char * max_repeats

    return pattern.sub(replacer, text)


DEFAULT_CLEANING_STEPS: tuple[Callable[[str], str], ...] = (
    normalize_unicode,
    strip_html,
    remove_urls,
    partial(normalize_case, mode="lower"),
    remove_mentions_hashtags,
    partial(remove_repeated_chars, max_repeats=2),
    collapse_whitespace,
)


def clean_text(
    text: str | None, *, steps: Iterable[Callable[[str], str]] | None = None
) -> str:
    """Apply the configured cleaning steps sequentially.
    Args:
        text: The text to clean.
        steps: An iterable of cleaning functions to apply. Defaults to
            `DEFAULT_CLEANING_STEPS`.
    Returns:
        The cleaned text.
    """
    if not text:
        return ""
    pipeline = tuple(steps) if steps is not None else DEFAULT_CLEANING_STEPS
    cleaned = text
    for step in pipeline:
        cleaned = step(cleaned)
    # Always collapse whitespace at the end for consistent output.
    return collapse_whitespace(cleaned) if steps is not None else cleaned


__all__ = [
    "normalize_unicode",
    "strip_html",
    "collapse_whitespace",
    "normalize_case",
    "remove_urls",
    "remove_mentions_hashtags",
    "remove_repeated_chars",
    "clean_text",
    "DEFAULT_CLEANING_STEPS",
]
