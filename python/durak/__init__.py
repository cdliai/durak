"""Durak Turkish NLP toolkit."""

from __future__ import annotations

from importlib import metadata

from .cleaning import (
    clean_text,
    collapse_whitespace,
    extract_emojis,
    normalize_case,
    normalize_unicode,
    remove_emojis,
)
from .info import (
    get_bibtex_citation,
    get_build_info,
    get_resource_info,
    print_reproducibility_report,
)
from .exceptions import (
    ConfigurationError,
    DurakError,
    LemmatizerError,
    NormalizerError,
    PipelineError,
    ResourceError,
    RustExtensionError,
    StopwordError,
    StopwordMetadataError,  # Backward compatibility alias
    TokenizationError,
)
from .lemmatizer import Lemmatizer
from .normalizer import Normalizer
from .pipeline import Pipeline
from .processor import ProcessorConfig, ProcessingResult, TextProcessor, process_text
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
    # Modules
    "Lemmatizer",
    "Normalizer",
    "Pipeline",
    "ProcessorConfig",
    "ProcessingResult",
    "StopwordManager",
    "StopwordSnapshot",
    "TextProcessor",
    "Tokenizer",
    # Exceptions
    "ConfigurationError",
    "DurakError",
    "LemmatizerError",
    "NormalizerError",
    "PipelineError",
    "ResourceError",
    "RustExtensionError",
    "StopwordError",
    "StopwordMetadataError",  # Backward compatibility
    "TokenizationError",
    # Functions
    "attach_detached_suffixes",
    "clean_text",
    "collapse_whitespace",
    "get_bibtex_citation",
    "get_build_info",
    "get_resource_info",
    "is_stopword",
    "list_stopwords",
    "load_stopword_resource",
    "load_stopword_resources",
    "load_stopwords",
    "normalize_case",
    "normalize_tokens",
    "print_reproducibility_report",
    "extract_emojis",
    "remove_emojis",
    "normalize_unicode",
    "process_text",
    "remove_stopwords",
    "split_sentences",
    "tokenize",
    "tokenize_text",
    "tokenize_with_offsets",
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
