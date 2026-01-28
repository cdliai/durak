"""Text cleaning utilities for Durak."""

from __future__ import annotations

import html
import json
import re
import unicodedata
from collections.abc import Iterable
from functools import lru_cache, partial
from pathlib import Path
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

# Emoji pattern: comprehensive Unicode emoji ranges
# Covers emoji characters, emoji modifiers, and emoji sequences
# Note: No '+' quantifier to match individual emojis, not consecutive groups
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U00002702-\U000027B0"  # dingbats
    "\U000024C2-\U0001F251"  # enclosed characters
    "\U0001F900-\U0001F9FF"  # supplemental symbols and pictographs
    "\U0001FA00-\U0001FA6F"  # chess symbols
    "\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
    "\U00002600-\U000026FF"  # miscellaneous symbols
    "\U00002700-\U000027BF"  # dingbats
    "]"
    "(?:\uFE0F)?",  # Optional variation selector (e.g., ❤️ vs ❤)
    flags=re.UNICODE,
)

# Pattern for removing emojis (allows consecutive groups)
EMOJI_REMOVE_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"
    "\U0001F300-\U0001F5FF"
    "\U0001F680-\U0001F6FF"
    "\U0001F1E0-\U0001F1FF"
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FA6F"
    "\U0001FA70-\U0001FAFF"
    "\U00002600-\U000026FF"
    "\U00002700-\U000027BF"
    "\uFE0F"  # Include variation selector for removal
    "]+",
    flags=re.UNICODE,
)


def normalize_unicode(text: str) -> str:
    """Apply NFC normalization and map variants to standard characters."""
    if not text:
        return ""
    normalized = unicodedata.normalize("NFC", text)
    translation_table = str.maketrans(UNICODE_REPLACEMENTS)
    return normalized.translate(translation_table)


def strip_html(text: str) -> str:
    """Remove HTML tags, script/style content, and unescape HTML entities."""
    if not text:
        return ""
    without_blocks = SCRIPT_STYLE_PATTERN.sub(" ", text)
    without_tags = TAG_PATTERN.sub(" ", without_blocks)
    unescaped = html.unescape(without_tags)
    return collapse_whitespace(unescaped)


def collapse_whitespace(text: str) -> str:
    """Collapse consecutive whitespace characters into a single space."""
    if not text:
        return ""
    collapsed = WHITESPACE_PATTERN.sub(" ", text).strip()
    return re.sub(r"\s+([.,!?;:])", r"\1", collapsed)


def normalize_case(text: str, mode: str = "lower") -> str:
    """Normalize text casing with Turkish dotted/undotted I awareness."""
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
    """Remove HTTP(S) and www-prefixed URLs while keeping trailing punctuation."""
    if not text:
        return ""
    cleaned = URL_PATTERN.sub(_strip_trailing_punctuation, text)
    return collapse_whitespace(cleaned)


def remove_mentions_hashtags(text: str, *, keep_hash: bool = False) -> str:
    """Remove @mentions and hashtags"""
    if not text:
        return ""
    without_mentions = MENTION_PATTERN.sub(" ", text)

    def hashtag_replacer(match: re.Match[str]) -> str:
        keyword = match.group(0)[1:]
        return keyword if keep_hash else " "

    without_hashtags = HASHTAG_PATTERN.sub(hashtag_replacer, without_mentions)
    return collapse_whitespace(without_hashtags)


def remove_repeated_chars(text: str, *, max_repeats: int = 2) -> str:
    """Limit elongated characters and emojis to a maximum repeat threshold."""
    if not text:
        return ""
    if max_repeats < 1:
        raise ValueError("max_repeats must be >= 1")

    pattern = re.compile(rf"(.)\1{{{max_repeats},}}")

    def replacer(match: re.Match[str]) -> str:
        char = match.group(1)
        return char * max_repeats

    return pattern.sub(replacer, text)


def remove_emojis(text: str) -> str:
    """Remove all emoji characters from text.
    
    Useful for formal corpus processing where emojis are noise.
    
    Args:
        text: Input text potentially containing emojis
        
    Returns:
        Text with all emojis removed
        
    Examples:
        >>> remove_emojis("Harika! 🎉🎊 Çok güzel olmuş 😍")
        'Harika!  Çok güzel olmuş '
        >>> remove_emojis("Sade metin")
        'Sade metin'
    """
    if not text:
        return ""
    cleaned = EMOJI_REMOVE_PATTERN.sub(" ", text)
    return collapse_whitespace(cleaned)


def extract_emojis(text: str) -> list[str]:
    """Extract all emoji characters from text as a list.
    
    Useful for sentiment/emotion analysis as features before text cleaning.
    
    Args:
        text: Input text potentially containing emojis
        
    Returns:
        List of emoji characters found in the text (preserves order and duplicates)
        
    Examples:
        >>> extract_emojis("Müthiş gün! 🌞☀️🔥")
        ['🌞', '☀️', '🔥']
        >>> extract_emojis("Emoji yok")
        []
        >>> extract_emojis("Çok mutluyum! 😊😊😊")
        ['😊', '😊', '😊']
    """
    if not text:
        return []
    # Find all emoji matches and return as list
    return EMOJI_PATTERN.findall(text)


@lru_cache(maxsize=1)
def _load_emoji_sentiment_dict() -> dict[str, dict[str, str | float]]:
    """Load emoji sentiment dictionary from resources.
    
    Cached after first call to avoid repeated file I/O.
    
    Returns:
        Dictionary mapping emoji characters to sentiment metadata
    """
    resources_dir = Path(__file__).parent.parent.parent / "resources" / "tr"
    sentiment_file = resources_dir / "emoji_sentiment.json"
    
    if not sentiment_file.exists():
        return {}
    
    with sentiment_file.open(encoding="utf-8") as f:
        return json.load(f)


def map_emoji_sentiment(
    text: str,
    *,
    format: str = "label",
    unknown: str = "preserve",
) -> str:
    """Replace emojis with sentiment tokens.
    
    Useful for social media NLP where emojis carry sentiment signals.
    
    Args:
        text: Input text containing emojis
        format: Output format for known emojis:
            - "label": Replace with [LABEL] tokens (e.g., [HAPPY], [SAD])
            - "polarity": Replace with [POSITIVE], [NEGATIVE], [NEUTRAL]
        unknown: How to handle unknown emojis:
            - "preserve": Keep original emoji
            - "remove": Remove unknown emoji
            - "neutral": Replace with [NEUTRAL]
            
    Returns:
        Text with emojis replaced by sentiment tokens
        
    Examples:
        >>> map_emoji_sentiment("Harika! 😊🔥", format="label")
        'Harika! [HAPPY] [HOT]'
        >>> map_emoji_sentiment("Üzgünüm 😢", format="polarity")
        'Üzgünüm [NEGATIVE]'
        >>> map_emoji_sentiment("Test 🦄", unknown="neutral")
        'Test [NEUTRAL]'
    """
    if not text:
        return ""
    
    if format not in {"label", "polarity"}:
        raise ValueError(f"format must be 'label' or 'polarity', got '{format}'")
    
    if unknown not in {"preserve", "remove", "neutral"}:
        raise ValueError(
            f"unknown must be 'preserve', 'remove', or 'neutral', got '{unknown}'"
        )
    
    sentiment_dict = _load_emoji_sentiment_dict()
    
    def replacer(match: re.Match[str]) -> str:
        emoji = match.group(0)
        
        # Check sentiment dictionary
        if emoji in sentiment_dict:
            data = sentiment_dict[emoji]
            if format == "label":
                return f"[{data['label']}]"
            else:  # format == "polarity"
                return f"[{data['polarity'].upper()}]"
        
        # Handle unknown emoji
        if unknown == "preserve":
            return emoji
        elif unknown == "remove":
            return ""
        else:  # unknown == "neutral"
            return "[NEUTRAL]"
    
    result = EMOJI_PATTERN.sub(replacer, text)
    return collapse_whitespace(result)


def extract_emoji_sentiment(text: str) -> tuple[list[str], list[dict[str, str | float]]]:
    """Extract emojis and their sentiment data as structured output.
    
    Useful for detailed sentiment analysis with emoji intensity and polarity.
    
    Args:
        text: Input text containing emojis
        
    Returns:
        Tuple of:
        - List of emoji characters found
        - List of sentiment dictionaries (polarity, intensity, label)
          Unknown emojis get {"polarity": "neutral", "intensity": 0.5, "label": "UNKNOWN"}
          
    Examples:
        >>> emojis, sentiments = extract_emoji_sentiment("Test 😊😢")
        >>> emojis
        ['😊', '😢']
        >>> sentiments[0]
        {'polarity': 'positive', 'intensity': 0.7, 'label': 'HAPPY'}
    """
    if not text:
        return ([], [])
    
    emojis = extract_emojis(text)
    sentiment_dict = _load_emoji_sentiment_dict()
    
    sentiments = []
    for emoji in emojis:
        if emoji in sentiment_dict:
            sentiments.append(dict(sentiment_dict[emoji]))
        else:
            # Unknown emoji: neutral default
            sentiments.append({
                "polarity": "neutral",
                "intensity": 0.5,
                "label": "UNKNOWN",
            })
    
    return (emojis, sentiments)


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
    text: str | None,
    *,
    steps: Iterable[Callable[[str], str]] | None = None,
    emoji_mode: str = "keep",
    sentiment_format: str = "label",
    sentiment_unknown: str = "preserve",
) -> str | tuple[str, list[str]] | tuple[str, list[dict[str, str | float]]]:
    """Apply the configured cleaning steps sequentially with emoji handling.
    
    Args:
        text: Input text to clean
        steps: Custom cleaning pipeline (if None, uses DEFAULT_CLEANING_STEPS)
        emoji_mode: How to handle emojis:
            - "keep": Preserve emojis in the output (default)
            - "remove": Strip all emojis from the text
            - "extract": Return tuple of (cleaned_text, emoji_list)
            - "sentiment": Replace emojis with sentiment tokens
            - "sentiment_extract": Return tuple of (cleaned_text, sentiment_data)
        sentiment_format: Format for sentiment mode (only used with emoji_mode="sentiment"):
            - "label": [HAPPY], [SAD], etc. (default)
            - "polarity": [POSITIVE], [NEGATIVE], [NEUTRAL]
        sentiment_unknown: How to handle unknown emojis in sentiment mode:
            - "preserve": Keep original emoji (default)
            - "remove": Remove unknown emoji
            - "neutral": Replace with [NEUTRAL]
            
    Returns:
        - str: Cleaned text (if emoji_mode is "keep", "remove", or "sentiment")
        - tuple[str, list[str]]: (cleaned_text, emoji_list) if emoji_mode is "extract"
        - tuple[str, list[dict]]: (cleaned_text, sentiment_data) if emoji_mode is "sentiment_extract"
        
    Raises:
        ValueError: If emoji_mode is invalid
        
    Examples:
        >>> clean_text("Harika! 🎉", emoji_mode="keep")
        'harika! 🎉'
        >>> clean_text("Harika! 🎉", emoji_mode="remove")
        'harika!'
        >>> clean_text("Harika! 🎉", emoji_mode="extract")
        ('harika!', ['🎉'])
        >>> clean_text("Harika! 😊🔥", emoji_mode="sentiment")
        'harika! [HAPPY] [HOT]'
        >>> clean_text("Test 😊", emoji_mode="sentiment_extract")
        ('test', [{'polarity': 'positive', 'intensity': 0.7, 'label': 'HAPPY'}])
    """
    if not text:
        if emoji_mode == "extract":
            return ("", [])
        elif emoji_mode == "sentiment_extract":
            return ("", [])
        return ""
        
    valid_modes = {"keep", "remove", "extract", "sentiment", "sentiment_extract"}
    if emoji_mode not in valid_modes:
        raise ValueError(
            f"emoji_mode must be one of {valid_modes}, got '{emoji_mode}'"
        )
    
    # Extract emojis/sentiment data first if needed (before cleaning modifies the text)
    extracted_emojis: list[str] = []
    sentiment_data: list[dict[str, str | float]] = []
    
    if emoji_mode == "extract":
        extracted_emojis = extract_emojis(text)
    elif emoji_mode == "sentiment_extract":
        extracted_emojis, sentiment_data = extract_emoji_sentiment(text)
    
    # Apply cleaning pipeline
    pipeline = tuple(steps) if steps is not None else DEFAULT_CLEANING_STEPS
    cleaned = text
    for step in pipeline:
        cleaned = step(cleaned)
    
    # Always collapse whitespace at the end for consistent output
    if steps is not None:
        cleaned = collapse_whitespace(cleaned)
    
    # Handle emoji mode
    if emoji_mode == "remove":
        cleaned = remove_emojis(cleaned)
    elif emoji_mode == "extract":
        cleaned = remove_emojis(cleaned)
        return (cleaned, extracted_emojis)
    elif emoji_mode == "sentiment":
        cleaned = map_emoji_sentiment(
            cleaned,
            format=sentiment_format,
            unknown=sentiment_unknown,
        )
    elif emoji_mode == "sentiment_extract":
        cleaned = remove_emojis(cleaned)
        return (cleaned, sentiment_data)
    
    return cleaned


__all__ = [
    "normalize_unicode",
    "strip_html",
    "collapse_whitespace",
    "normalize_case",
    "remove_urls",
    "remove_mentions_hashtags",
    "remove_repeated_chars",
    "remove_emojis",
    "extract_emojis",
    "map_emoji_sentiment",
    "extract_emoji_sentiment",
    "clean_text",
    "DEFAULT_CLEANING_STEPS",
]
