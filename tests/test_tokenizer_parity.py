"""Parity tests between Python regex and Rust-backed tokenization."""

from __future__ import annotations

import pytest

from durak.tokenizer import RUST_TOKENIZER_AVAILABLE, tokenize, tokenize_text


@pytest.mark.skipif(not RUST_TOKENIZER_AVAILABLE, reason="Rust extension not installed")
@pytest.mark.parametrize(
    "text",
    [
        "Türkiye'ye gidiyorum.",
        "5-10 yıla bizi yakalayıp geçer.",
        "URL: https://karagoz.io/test?a=1",
        "Koş! (Hızlıca)",
        "Dr. Ahmet geldi.",
    ],
)
def test_regex_and_rust_tokenization_match(text: str) -> None:
    regex_tokens = tokenize(text, strategy="regex")
    rust_tokens = tokenize(text, strategy="rust")
    assert rust_tokens == regex_tokens


@pytest.mark.skipif(not RUST_TOKENIZER_AVAILABLE, reason="Rust extension not installed")
def test_auto_strategy_prefers_rust_when_available() -> None:
    text = "Merhaba dünya!"
    assert tokenize_text(text, strategy="auto") == tokenize_text(text, strategy="rust")
