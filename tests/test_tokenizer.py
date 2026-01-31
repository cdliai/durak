from pathlib import Path

import pytest
from durak import tokenize
from durak.tokenizer import normalize_tokens, split_sentences, tokenize_text

from tests.data.corpus_validator import validate_corpus


@pytest.mark.parametrize(
    ("text", "expected_tokens"),
    [
        ("Türkiye'ye gidiyorum.", ["Türkiye'ye", "gidiyorum", "."]),
        (
            "5-10 yıla bizi yakalayıp geçer.",
            ["5-10", "yıla", "bizi", "yakalayıp", "geçer", "."],
        ),
        (
            "URL: https://karagoz.io/test?a=1",
            ["URL", ":", "https://karagoz.io/test?a=1"],
        ),
    ],
)
def test_regex_tokenize_preserves_turkish_features(
    text: str, expected_tokens: list[str]
) -> None:
    tokens = tokenize_text(text)
    assert tokens == expected_tokens


def test_sentence_split_handles_abbreviations() -> None:
    text = "Dr. Ahmet geldi. Hastayı muayene etti!"
    sentences = split_sentences(text)
    assert sentences == ["Dr. Ahmet geldi.", "Hastayı muayene etti!"]


def test_tokenizer_integration_with_corpus_validator() -> None:
    sample_path = Path(__file__).parent / "data" / "sample_sentences.txt"
    sentences = sample_path.read_text(encoding="utf-8").splitlines()

    tokenized_sentences = [" ".join(tokenize_text(sentence)) for sentence in sentences]
    issues = validate_corpus(tokenized_sentences)
    assert not issues, f"Tokenizer introduced corpus issues: {issues}"


def test_normalize_tokens_lowering_and_punct_stripping() -> None:
    tokens = ["Merhaba", ",", "DURAK", "!"]
    normalized = normalize_tokens(tokens, lower=True, strip_punct=True)
    assert normalized == ["merhaba", "durak"]


def test_tokenize_accepts_strip_punct_flag() -> None:
    text = "Durak, kolay mı?"
    tokens_with_punct = tokenize(text)
    assert tokens_with_punct == ["Durak", ",", "kolay", "mı", "?"]

    tokens_without_punct = tokenize(text, strip_punct=True)
    assert tokens_without_punct == ["Durak", "kolay", "mı"]
