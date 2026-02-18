"""Exception hierarchy for Durak Turkish NLP toolkit.

Provides a structured exception hierarchy for type-safe error handling
and better debugging in production environments.

Exception Hierarchy:
    DurakError
    ├── ConfigurationError
    ├── ResourceError
    ├── RustExtensionError
    ├── LemmatizerError
    ├── NormalizerError
    ├── PipelineError
    ├── TokenizationError
    └── StopwordError

Usage:
    >>> from durak.exceptions import DurakError, LemmatizerError
    >>> try:
    ...     lemmatizer = Lemmatizer(strategy="hybrid")
    ...     result = lemmatizer("kitaplar")
    ... except LemmatizerError as e:
    ...     logger.error(f"Lemmatization failed: {e}")
    ...     fallback_to_simple_stemming()
    ... except DurakError as e:
    ...     logger.error(f"Durak error: {e}")
    ...     raise
"""

from __future__ import annotations


class DurakError(Exception):
    """Base exception for all Durak errors.

    All Durak-specific exceptions inherit from this class, allowing
    users to catch all package-related errors with a single except clause.

    Examples:
        >>> try:
        ...     # Any Durak operation
        ...     pass
        ... except DurakError:
        ...     # Handle all Durak errors
        ...     pass
    """

    pass


class ConfigurationError(DurakError):
    """Raised when module configuration is invalid.

    Indicates that initialization parameters or runtime configuration
    options are invalid, incompatible, or out of range.

    Examples:
        >>> from durak import Lemmatizer
        >>> # Invalid strategy name
        >>> lemmatizer = Lemmatizer(strategy="invalid")
        Traceback (most recent call last):
        ...
        durak.exceptions.ConfigurationError: Unknown strategy: invalid
    """

    pass


class ResourceError(DurakError):
    """Raised when embedded resources fail to load.

    Indicates that embedded dictionaries, stopword lists, or other
    package resources could not be loaded or parsed.

    Examples:
        >>> from durak import load_stopword_resource
        >>> # Non-existent resource
        >>> stopwords = load_stopword_resource("nonexistent/resource")
        Traceback (most recent call last):
        ...
        durak.exceptions.ResourceError: Resource not found: nonexistent/resource
    """

    pass


class RustExtensionError(DurakError):
    """Raised when Rust extension is unavailable or fails.

    Indicates that the compiled Rust extension (_durak_core) is either
    not installed or failed to load. This typically occurs in development
    environments before running `maturin develop`.

    Examples:
        >>> from durak import Lemmatizer
        >>> # Rust extension not compiled
        >>> lemmatizer = Lemmatizer()
        Traceback (most recent call last):
        ...
        durak.exceptions.RustExtensionError: Rust extension not installed
    """

    pass


class LemmatizerError(DurakError):
    """Raised when lemmatization fails.

    Indicates an error during the lemmatization process, such as
    invalid input, dictionary lookup failures, or heuristic errors.

    Examples:
        >>> from durak import Lemmatizer
        >>> lemmatizer = Lemmatizer()
        >>> # Invalid input type
        >>> result = lemmatizer(12345)
        Traceback (most recent call last):
        ...
        durak.exceptions.LemmatizerError: Input must be a string
    """

    pass


class NormalizerError(DurakError):
    """Raised when normalization fails.

    Indicates an error during text normalization, such as invalid
    input or configuration issues.

    Examples:
        >>> from durak import Normalizer
        >>> normalizer = Normalizer()
        >>> # Invalid input type
        >>> result = normalizer(12345)
        Traceback (most recent call last):
        ...
        durak.exceptions.NormalizerError: Input must be a string
    """

    pass


class PipelineError(DurakError):
    """Raised when pipeline execution fails.

    Wraps errors that occur during pipeline step execution,
    providing context about which step failed and why.

    Examples:
        >>> from durak import Pipeline
        >>> pipeline = Pipeline(["clean", "tokenize", "invalid_step"])
        >>> result = pipeline("test text")
        Traceback (most recent call last):
        ...
        durak.exceptions.PipelineError: Unknown pipeline step: invalid_step
    """

    pass


class TokenizationError(DurakError):
    """Raised when tokenization fails.

    Indicates an error during the tokenization process, such as
    invalid input, malformed text, or internal tokenizer failures.

    Examples:
        >>> from durak import tokenize
        >>> # Invalid input type
        >>> tokens = tokenize(12345)
        Traceback (most recent call last):
        ...
        durak.exceptions.TokenizationError: Input must be a string
    """

    pass


class StopwordError(DurakError):
    """Raised when stopword operations fail.

    Indicates errors during stopword loading, filtering, or
    resource management operations.

    Examples:
        >>> from durak import load_stopwords
        >>> # Invalid file path
        >>> stopwords = load_stopwords("/nonexistent/path.txt")
        Traceback (most recent call last):
        ...
        durak.exceptions.StopwordError: Failed to load stopwords
    """

    pass


# Backward compatibility alias (deprecated, will be removed in v1.0)
StopwordMetadataError = StopwordError
