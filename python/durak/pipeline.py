"""Pipeline module for composing text processing steps."""

from __future__ import annotations

import re
import warnings
from typing import Any, Callable, Union

from durak.cleaning import (
    clean_text,
    collapse_whitespace,
    normalize_unicode,
    remove_mentions_hashtags,
    remove_repeated_chars,
    remove_urls,
    strip_html,
)
from durak.exceptions import ConfigurationError, PipelineError
from durak.normalizer import Normalizer
from durak.stopwords import remove_stopwords as remove_stopwords_fn
from durak.suffixes import attach_detached_suffixes
from durak.tokenizer import PUNCT_TOKEN, tokenize

STEP_REGISTRY: dict[str, Callable[..., Any]] = {
    "clean": clean_text,
    "normalize": Normalizer(),
    "tokenize": tokenize,
    "remove_stopwords": remove_stopwords_fn,
    "attach_suffixes": attach_detached_suffixes,
}

StepType = Union[str, Callable[..., Any]]


class Pipeline:
    """
    Composable text processing pipeline.

    Args:
        steps: List of step names (strings) or callable functions

    Raises:
        ConfigurationError: If steps list is empty or contains unknown step names

    Examples:
        >>> pipeline = Pipeline(["clean", "tokenize"])
        >>> tokens = pipeline("Hello world!")
        ['Hello', 'world', '!']

        >>> # With custom callable
        >>> pipeline = Pipeline(["clean", "tokenize", lambda t: [x.upper() for x in t]])
        >>> pipeline("hello")
        ['HELLO']
    """

    def __init__(self, steps: list[StepType]):
        if not steps:
            raise ConfigurationError("Pipeline must have at least one step")

        self.step_names: list[str] = []
        self.steps: list[Callable[..., Any]] = []

        for step in steps:
            if callable(step):
                self.step_names.append(getattr(step, "__name__", repr(step)))
                self.steps.append(step)
            elif isinstance(step, str):
                if step not in STEP_REGISTRY:
                    raise ConfigurationError(
                        f"Unknown pipeline step: '{step}'. "
                        f"Available steps: {', '.join(STEP_REGISTRY.keys())}"
                    )
                self.step_names.append(step)
                self.steps.append(STEP_REGISTRY[step])
            else:
                raise ConfigurationError(
                    f"Pipeline step must be a string or callable, "
                    f"got {type(step).__name__}"
                )

    def __call__(self, text: str) -> str | list[str]:
        """
        Process text through the pipeline.

        Args:
            text: Input text to process

        Returns:
            Processed result (type depends on pipeline steps)

        Raises:
            PipelineError: If input is not a string or step execution fails
        """
        if not isinstance(text, str):
            raise PipelineError(
                f"Pipeline input must be a string, got {type(text).__name__}"
            )

        doc: Any = text
        for step_name, step in zip(self.step_names, self.steps):
            try:
                doc = step(doc)
            except Exception as e:
                raise PipelineError(f"Pipeline step '{step_name}' failed: {e}") from e
        return doc

    def __repr__(self) -> str:
        return f"Pipeline([{', '.join(repr(name) for name in self.step_names)}])"


def process_text_with_steps(text: str, steps: list[StepType]) -> str | list[str]:
    """
    Convenience function for one-off pipeline processing with custom steps.

    Args:
        text: Input text
        steps: List of step names or callables

    Returns:
        Processed result

    Examples:
        >>> result = process_text_with_steps("Hello world!", ["clean", "tokenize"])
        ['Hello', 'world', '!']
    """
    pipeline = Pipeline(steps)
    return pipeline(text)


def process_text(
    text: str,
    *,
    remove_stopwords: bool = False,
    rejoin_suffixes: bool = False,
    lowercase: bool = True,
    strip_punct: bool = False,
) -> list[str]:
    """
    Simple one-off text processing with common options.

    .. deprecated:: 0.5.0
        Use :class:`Pipeline` for production code.
        This function will be removed in v1.0.

    Executes: clean → tokenize → [rejoin suffixes] → [remove stopwords]

    Args:
        text: Input text to process
        remove_stopwords: Whether to remove stopwords (default: False)
        rejoin_suffixes: Whether to reattach detached suffixes like "ankara ' da"
                         into "ankara'da" (default: False)
        lowercase: Whether to lowercase text during cleaning (default: True)
        strip_punct: Whether to strip punctuation from tokens (default: False)

    Returns:
        List of processed tokens

    Examples:
        >>> from durak import process_text
        >>> tokens = process_text("Türkiye'de NLP zor!")
        >>> tokens
        ["türkiye'de", "nlp", "zor", "!"]

        >>> tokens = process_text("Ankara ' da kaldım.", rejoin_suffixes=True)
        >>> tokens
        ["ankara'da", "kaldım", "."]

        >>> tokens = process_text("Bu bir test", remove_stopwords=True)
        >>> tokens
        ['test']
    """
    warnings.warn(
        "process_text() is deprecated and will be removed in v1.0. "
        "Use Pipeline(['clean', 'tokenize', ...]) instead.",
        DeprecationWarning,
        stacklevel=2,
    )

    if not isinstance(text, str):
        raise PipelineError(f"Input must be a string, got {type(text).__name__}")

    if not text:
        return []

    cleaned_result: str | tuple[str, list[str]]
    if lowercase:
        cleaned_result = clean_text(text)
    else:
        cleaned_result = collapse_whitespace(
            remove_mentions_hashtags(
                remove_repeated_chars(remove_urls(strip_html(normalize_unicode(text))))
            )
        )

    if isinstance(cleaned_result, tuple):
        cleaned = cleaned_result[0]
    else:
        cleaned = cleaned_result

    tokens = tokenize(cleaned)

    if strip_punct:
        tokens = [t for t in tokens if not re.fullmatch(PUNCT_TOKEN, t)]

    if rejoin_suffixes:
        tokens = attach_detached_suffixes(tokens)

    if remove_stopwords:
        tokens = remove_stopwords_fn(tokens)

    return tokens
