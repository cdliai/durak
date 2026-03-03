"""Tests for centralized resource-provider utilities."""

from __future__ import annotations

import json

from durak.resources_provider import DEFAULT_RESOURCE_PROVIDER


def test_load_detached_suffixes_not_empty() -> None:
    suffixes = DEFAULT_RESOURCE_PROVIDER.load_detached_suffixes()
    assert suffixes
    assert "da" in suffixes


def test_load_stopwords_metadata_text_is_valid_json() -> None:
    metadata_text = DEFAULT_RESOURCE_PROVIDER.load_stopwords_metadata_text()
    payload = json.loads(metadata_text)

    assert isinstance(payload, dict)
    assert "sets" in payload


def test_load_apostrophes_not_empty() -> None:
    apostrophes = DEFAULT_RESOURCE_PROVIDER.load_apostrophes()
    assert apostrophes
    assert "'" in apostrophes
