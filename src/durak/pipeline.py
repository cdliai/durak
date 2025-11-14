"""High-level processing pipeline helpers."""

from __future__ import annotations

from collections.abc import Iterable

from .cleaning import clean_text
from .stopwords import StopwordManager
from .stopwords import remove_stopwords as _remove_stopwords
from .suffixes import attach_detached_suffixes as _attach_detached_suffixes
from .tokenizer import tokenize

__all__ = ["process_text"]


def process_text(
    text: str | None,
    *,
    clean: bool = True,
    tokenizer: str = "regex",
    remove_stopwords: bool = False,
    stopword_manager: StopwordManager | None = None,
    stopword_base: Iterable[str] | None = None,
    stopword_additions: Iterable[str] | None = None,
    stopword_keep: Iterable[str] | None = None,
    stopword_case_sensitive: bool | None = None,
    rejoin_suffixes: bool = False,
    rejoin_suffix_list: Iterable[str] | None = None,
    rejoin_suffix_allow_without_apostrophe: bool = True,
) -> list[str]:
    """Clean, tokenize, and optionally remove stopwords from text.
    Args:
        text: The text to process.
        clean: Whether to clean the text. Defaults to True.
        tokenizer: The tokenizer strategy to use. Defaults to "regex".
        remove_stopwords: Whether to remove stopwords. Defaults to False.
        stopword_manager: A StopwordManager instance to use. If not provided,
            a default one will be created.
        stopword_base: A base set of stopwords to use.
        stopword_additions: A set of stopwords to add to the base set.
        stopword_keep: A set of stopwords to keep.
        stopword_case_sensitive: Whether stopword matching should be case
            sensitive.
        rejoin_suffixes: Whether to rejoin detached suffixes. Defaults to
            False.
        rejoin_suffix_list: A list of suffixes to rejoin.
        rejoin_suffix_allow_without_apostrophe: Whether to allow rejoining
            suffixes without an apostrophe. Defaults to True.
    Returns:
        A list of processed tokens.
    Raises:
        ValueError: If stopword or suffix rejoin configuration is provided
            but the corresponding feature is disabled.
    Examples:
        >>> process_text("Bu bir test!", remove_stopwords=True)
        ['test', '!']
    """
    if text is None:
        return []

    if not remove_stopwords and any(
        option is not None
        for option in (
            stopword_manager,
            stopword_base,
            stopword_additions,
            stopword_keep,
            stopword_case_sensitive,
        )
    ):
        raise ValueError(
            "Stopword configuration provided but remove_stopwords=False. "
            "Set remove_stopwords=True to enable stopword filtering."
        )

    if not rejoin_suffixes and (
        rejoin_suffix_list is not None
        or not rejoin_suffix_allow_without_apostrophe
    ):
        raise ValueError(
            "Suffix rejoin configuration provided but rejoin_suffixes=False. "
            "Set rejoin_suffixes=True to enable suffix reattachment."
        )

    processed = clean_text(text) if clean else text
    tokens = tokenize(processed, strategy=tokenizer)

    if rejoin_suffixes:
        tokens = _attach_detached_suffixes(
            tokens,
            suffixes=rejoin_suffix_list,
            allow_without_apostrophe=rejoin_suffix_allow_without_apostrophe,
        )

    if remove_stopwords:
        tokens = _remove_stopwords(
            tokens,
            manager=stopword_manager,
            base=stopword_base,
            additions=stopword_additions,
            keep=stopword_keep,
            case_sensitive=stopword_case_sensitive,
        )

    return list(tokens)
