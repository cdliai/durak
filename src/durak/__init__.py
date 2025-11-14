"""Durak: A Turkish Natural Language Processing Toolkit.

Durak is a comprehensive toolkit for Turkish NLP, providing essential tools for
text cleaning, tokenization, stopword removal, and more.
"""

from __future__ import annotations

from importlib import metadata

from .cleaning import clean_text, collapse_whitespace, normalize_case, normalize_unicode
from .pipeline import process_text
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
from .tokenizer import normalize_tokens, split_sentences, tokenize, tokenize_text

__all__ = [
    "__version__",
    "APOSTROPHE_TOKENS",
    "BASE_STOPWORDS",
    "DEFAULT_STOPWORD_RESOURCE",
    "DEFAULT_DETACHED_SUFFIXES",
    "StopwordManager",
    "StopwordSnapshot",
    "attach_detached_suffixes",
    "clean_text",
    "collapse_whitespace",
    "is_stopword",
    "list_stopwords",
    "load_stopword_resource",
    "load_stopword_resources",
    "load_stopwords",
    "normalize_case",
    "normalize_unicode",
    "normalize_tokens",
    "process_text",
    "remove_stopwords",
    "split_sentences",
    "tokenize",
    "tokenize_text",
]

try:
    __version__ = metadata.version("durak-nlp")
    """The version of the Durak package."""
except metadata.PackageNotFoundError:  # pragma: no cover - fallback during dev installs
    __version__ = "0.2.0"
    """The version of the Durak package."""
