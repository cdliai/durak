"""Durak Turkish NLP toolkit."""

from __future__ import annotations

from importlib import metadata

from .cleaning import (
    clean_text,
    collapse_whitespace,
    extract_emoji_sentiment,
    extract_emojis,
    map_emoji_sentiment,
    normalize_case,
    normalize_unicode,
    remove_emojis,
)
from .lemmatizer import Lemmatizer
from .normalizer import Normalizer
from .pipeline import Pipeline, process_text
from .stopwords import (
    BASE_STOPWORDS,
    DEFAULT_STOPWORD_RESOURCE,
    StopwordManager,
    StopwordSnapshot,
    is_stopword,
    list_stopwords,
    load_stopword_resource,
    load_stopword_resources,
    load_stopwords,
    remove_stopwords,
)
from .suffixes import (
    APOSTROPHE_TOKENS,
    DEFAULT_DETACHED_SUFFIXES,
    attach_detached_suffixes,
)
from .tokenizer import (
    TokenizationError,
    Tokenizer,
    normalize_tokens,
    split_sentences,
    tokenize,
    tokenize_text,
    tokenize_with_offsets,
)

__all__ = [
    "__version__",
    "APOSTROPHE_TOKENS",
    "BASE_STOPWORDS",
    "DEFAULT_STOPWORD_RESOURCE",
    "DEFAULT_DETACHED_SUFFIXES",
    "Lemmatizer",
    "Normalizer",
    "Pipeline",
    "StopwordManager",
    "StopwordSnapshot",
    "attach_detached_suffixes",
    "clean_text",
    "collapse_whitespace",
    "extract_emoji_sentiment",
    "extract_emojis",
    "is_stopword",
    "list_stopwords",
    "load_stopword_resource",
    "load_stopword_resources",
    "load_stopwords",
    "map_emoji_sentiment",
    "normalize_case",
    "normalize_unicode",
    "normalize_tokens",
    "process_text",
    "remove_emojis",
    "remove_stopwords",
    "split_sentences",
    "tokenize",
    "tokenize_text",
    "tokenize_with_offsets",
    "Tokenizer",
    "TokenizationError",
]

try:
    __version__ = metadata.version("durak-nlp")
except metadata.PackageNotFoundError:  # pragma: no cover - fallback during dev installs
    __version__ = "0.4.0"

# Import Rust extension - gracefully degrade if not available
try:
    from . import _durak_core
except ImportError:
    _durak_core = None  # type: ignore[assignment]
