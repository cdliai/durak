"""Shared internal data models for pipeline-oriented processing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class TokenSpan:
    """Token with start/end character offsets."""

    token: str
    start: int
    end: int


@dataclass
class Document:
    """Canonical mutable payload for advanced pipeline stages."""

    text: str
    tokens: list[str] = field(default_factory=list)
    token_spans: list[TokenSpan] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
