"""Internal interface contracts used to keep module boundaries explicit."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class NormalizerLike(Protocol):
    """Contract for text normalizers."""

    def __call__(self, text: str) -> str: ...


@runtime_checkable
class CleanerLike(Protocol):
    """Contract for text cleaning stages."""

    def __call__(self, text: str) -> str | tuple[str, list[str]]: ...


@runtime_checkable
class TokenizerLike(Protocol):
    """Contract for tokenization stages."""

    def __call__(self, text: str | None, *, strip_punct: bool = False) -> list[str]: ...


@runtime_checkable
class LemmatizerLike(Protocol):
    """Contract for word-level lemmatizers."""

    def __call__(self, word: str) -> str: ...


@runtime_checkable
class PipelineStepLike(Protocol):
    """Generic pipeline-stage contract."""

    def __call__(self, doc: Any) -> Any: ...


@runtime_checkable
class ResourceProviderLike(Protocol):
    """Contract for resource-loading adapters."""

    def load_detached_suffixes(self) -> tuple[str, ...]: ...
    def load_stopwords_metadata_text(self) -> str: ...
    def load_apostrophes(self) -> tuple[str, ...]: ...
