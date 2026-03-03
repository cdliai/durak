"""Core contracts and shared data models for Durak internals."""

from .interfaces import (
    CleanerLike,
    LemmatizerLike,
    NormalizerLike,
    PipelineStepLike,
    ResourceProviderLike,
    TokenizerLike,
)
from .types import Document, TokenSpan

__all__ = [
    "CleanerLike",
    "Document",
    "LemmatizerLike",
    "NormalizerLike",
    "PipelineStepLike",
    "ResourceProviderLike",
    "TokenizerLike",
    "TokenSpan",
]
