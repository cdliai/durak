"""Golden regression tests for core NLP behavior."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from durak.lemmatizer import Lemmatizer
from durak.normalizer import Normalizer
from durak.pipeline import Pipeline
from durak.tokenizer import tokenize_text

GOLDEN_CASES_PATH = Path(__file__).parent / "data" / "golden_regression_cases.json"


def _load_golden_cases() -> dict[str, list[dict[str, Any]]]:
    with GOLDEN_CASES_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _require_rust_extension() -> None:
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")


def test_golden_normalization_cases() -> None:
    _require_rust_extension()
    normalizer = Normalizer()
    cases = _load_golden_cases()["normalization"]

    for case in cases:
        assert normalizer(case["input"]) == case["expected"]


def test_golden_tokenization_cases() -> None:
    cases = _load_golden_cases()["tokenization"]

    for case in cases:
        assert tokenize_text(case["input"]) == case["expected"]


def test_golden_pipeline_cases() -> None:
    cases = _load_golden_cases()["pipeline"]

    for case in cases:
        pipeline = Pipeline(case["steps"])
        assert pipeline(case["input"]) == case["expected"]


def test_golden_lemmatization_cases() -> None:
    _require_rust_extension()
    cases = _load_golden_cases()["lemmatization"]

    for case in cases:
        lemmatizer = Lemmatizer(strategy=case["strategy"])
        assert lemmatizer(case["input"]) == case["expected"]
