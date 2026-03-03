"""End-to-end corpus analysis for pipeline quality and consistency."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

from durak.cleaning import clean_text
from durak.control import DurakController
from durak.pipeline import Pipeline
from durak.tokenizer import RUST_TOKENIZER_AVAILABLE

E2E_CORPUS_PATH = Path(__file__).parent / "data" / "e2e_pipeline_corpus_cases.json"


@dataclass(frozen=True)
class E2ECase:
    """Single corpus case for end-to-end validation."""

    id: str
    kind: str
    text: str
    min_tokens: int
    required_tokens: tuple[str, ...]
    absent_in_clean: tuple[str, ...] = ()
    joined_tokens: tuple[str, ...] = ()
    removed_by_stopwords: tuple[str, ...] = ()


def _as_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list):
        raise TypeError("Expected list for tuple-compatible fields.")
    if not all(isinstance(item, str) for item in value):
        raise TypeError("Tuple-compatible fields must contain only strings.")
    return tuple(value)


def _load_cases() -> list[E2ECase]:
    payload = json.loads(E2E_CORPUS_PATH.read_text(encoding="utf-8"))
    raw_cases = payload.get("cases")
    if not isinstance(raw_cases, list):
        raise TypeError("Corpus fixture must contain a 'cases' list.")

    cases: list[E2ECase] = []
    for raw in raw_cases:
        if not isinstance(raw, dict):
            raise TypeError("Each corpus case must be a JSON object.")

        case = E2ECase(
            id=str(raw["id"]),
            kind=str(raw["kind"]),
            text=str(raw["text"]),
            min_tokens=int(raw["min_tokens"]),
            required_tokens=_as_tuple(raw.get("required_tokens", [])),
            absent_in_clean=_as_tuple(raw.get("absent_in_clean")),
            joined_tokens=_as_tuple(raw.get("joined_tokens")),
            removed_by_stopwords=_as_tuple(raw.get("removed_by_stopwords")),
        )
        if case.kind not in {"clean", "noisy"}:
            raise TypeError(f"Unsupported case kind '{case.kind}' for {case.id}.")
        cases.append(case)

    return cases


def test_e2e_corpus_is_large_and_diverse() -> None:
    cases = _load_cases()
    clean_count = sum(1 for case in cases if case.kind == "clean")
    noisy_count = sum(1 for case in cases if case.kind == "noisy")

    assert len(cases) >= 30
    assert clean_count >= 12
    assert noisy_count >= 12


def test_e2e_pipeline_quality_analysis() -> None:
    cases = _load_cases()

    base_pipeline = Pipeline(["clean", "tokenize"])
    suffix_pipeline = Pipeline(["clean", "tokenize", "attach_suffixes"])
    filtered_pipeline = Pipeline(
        ["clean", "tokenize", "attach_suffixes", "remove_stopwords"]
    )

    total_raw_tokens = 0
    total_filtered_tokens = 0
    suffix_expectations = 0
    forbidden_checks = 0

    for case in cases:
        cleaned = clean_text(case.text)
        assert isinstance(cleaned, str)

        tokens = base_pipeline(case.text)
        tokens_with_suffixes = suffix_pipeline(case.text)
        filtered_tokens = filtered_pipeline(case.text)

        assert isinstance(tokens, list)
        assert isinstance(tokens_with_suffixes, list)
        assert isinstance(filtered_tokens, list)

        assert len(tokens) >= case.min_tokens, (
            f"{case.id}: expected at least {case.min_tokens} tokens, got {len(tokens)}"
        )
        assert tokens == base_pipeline(case.text), f"{case.id}: non-deterministic base output"
        assert tokens_with_suffixes == suffix_pipeline(case.text), (
            f"{case.id}: non-deterministic suffix output"
        )
        assert filtered_tokens == filtered_pipeline(case.text), (
            f"{case.id}: non-deterministic filtered output"
        )

        assert all(token.strip() for token in tokens), f"{case.id}: empty token detected"
        assert len(filtered_tokens) <= len(tokens_with_suffixes), (
            f"{case.id}: stopword filtering increased token count"
        )

        for required in case.required_tokens:
            assert required in tokens, f"{case.id}: missing required token '{required}'"

        cleaned_lower = cleaned.lower()
        for forbidden in case.absent_in_clean:
            forbidden_checks += 1
            assert forbidden.lower() not in cleaned_lower, (
                f"{case.id}: forbidden marker '{forbidden}' still in cleaned text"
            )

        for joined in case.joined_tokens:
            suffix_expectations += 1
            assert joined in tokens_with_suffixes, (
                f"{case.id}: expected joined token '{joined}' not found"
            )

        for removed in case.removed_by_stopwords:
            assert removed in tokens_with_suffixes, (
                f"{case.id}: token '{removed}' missing before stopword filter"
            )
            assert removed not in filtered_tokens, (
                f"{case.id}: token '{removed}' not removed by stopword filter"
            )

        total_raw_tokens += len(tokens_with_suffixes)
        total_filtered_tokens += len(filtered_tokens)

    assert total_filtered_tokens < total_raw_tokens

    reduction_pct = 100.0 * (total_raw_tokens - total_filtered_tokens) / total_raw_tokens
    assert reduction_pct >= 5.0

    print(
        "E2E pipeline summary: "
        f"cases={len(cases)}, "
        f"raw_tokens={total_raw_tokens}, "
        f"filtered_tokens={total_filtered_tokens}, "
        f"stopword_reduction={reduction_pct:.2f}%, "
        f"suffix_assertions={suffix_expectations}, "
        f"forbidden_clean_markers_checked={forbidden_checks}"
    )


@pytest.mark.skipif(not RUST_TOKENIZER_AVAILABLE, reason="Rust extension not installed")
def test_e2e_backend_tokenization_parity_on_cleaned_corpus() -> None:
    cases = _load_cases()
    rust_controller = DurakController(backend="rust")
    python_controller = DurakController(backend="python")

    for case in cases:
        cleaned = clean_text(case.text)
        assert isinstance(cleaned, str)

        rust_tokens = rust_controller.tokenize(cleaned)
        python_tokens = python_controller.tokenize(cleaned)
        assert rust_tokens == python_tokens, (
            f"{case.id}: backend tokenization mismatch\n"
            f"rust={rust_tokens}\n"
            f"python={python_tokens}"
        )
