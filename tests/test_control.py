"""Tests for backend control layer."""

from __future__ import annotations

import pytest

from durak.control import (
    RUST_TOKENIZER_AVAILABLE,
    DurakController,
    capability_matrix,
    resolve_backend,
)
from durak.exceptions import ConfigurationError


def test_capability_matrix_exposes_rust_and_python() -> None:
    matrix = capability_matrix()
    assert "rust" in matrix
    assert "python" in matrix
    assert matrix["python"]["available"] is True


def test_auto_backend_resolution() -> None:
    resolved = resolve_backend("auto")
    if RUST_TOKENIZER_AVAILABLE:
        assert resolved == "rust"
    else:
        assert resolved == "python"


def test_python_backend_normalize_and_tokenize() -> None:
    controller = DurakController(backend="python")
    assert controller.normalize("IŞIK ve İZMİR") == "ışık ve izmir"
    assert controller.tokenize("Merhaba dünya!") == ["Merhaba", "dünya", "!"]


def test_python_backend_rejects_offsets_and_lemmatize() -> None:
    controller = DurakController(backend="python")

    with pytest.raises(ConfigurationError, match="Offset tokenization"):
        controller.tokenize("Merhaba", with_offsets=True)

    with pytest.raises(ConfigurationError, match="requires backend='rust'"):
        controller.lemmatize("kitaplar")


@pytest.mark.skipif(not RUST_TOKENIZER_AVAILABLE, reason="Rust extension not installed")
def test_rust_backend_basic_operations() -> None:
    controller = DurakController(backend="rust")

    normalized = controller.normalize("İSTANBUL")
    assert normalized == "istanbul"

    tokens = controller.tokenize("Türkiye'ye gidiyorum.")
    assert tokens == ["Türkiye'ye", "gidiyorum", "."]

    offsets = controller.tokenize("Ali gel.", with_offsets=True)
    assert offsets == [("Ali", 0, 3), ("gel", 4, 7), (".", 7, 8)]

    assert controller.lemmatize("kitaplar") == "kitap"


@pytest.mark.skipif(not RUST_TOKENIZER_AVAILABLE, reason="Rust extension not installed")
def test_parity_between_rust_and_python_for_shared_features() -> None:
    rust = DurakController(backend="rust")
    py = DurakController(backend="python")
    text = "Türkiye'ye gidiyorum."

    assert rust.normalize(text) == py.normalize(text)
    assert rust.tokenize(text) == py.tokenize(text)
