"""Strict canonical gold-output tests for end-to-end pipeline behavior."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from durak.cleaning import clean_text
from durak.pipeline import Pipeline

CANONICAL_GOLD_PATH = Path(__file__).parent / "data" / "e2e_pipeline_canonical_gold.json"


def _load_cases() -> list[dict[str, Any]]:
    payload = json.loads(CANONICAL_GOLD_PATH.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list):
        raise TypeError("Canonical gold fixture must contain a 'cases' list.")
    return cases


def _unwrap_cleaned_text(cleaned_result: str | tuple[str, list[str]]) -> str:
    if isinstance(cleaned_result, tuple):
        return cleaned_result[0]
    return cleaned_result


def test_canonical_gold_fixture_shape() -> None:
    cases = _load_cases()
    assert len(cases) >= 8
    for case in cases:
        assert isinstance(case.get("id"), str)
        assert isinstance(case.get("text"), str)
        assert isinstance(case.get("expected_clean"), str)
        assert isinstance(case.get("expected_tokens"), list)
        assert isinstance(case.get("expected_attached_tokens"), list)
        assert isinstance(case.get("expected_filtered_tokens"), list)


def test_canonical_gold_pipeline_outputs() -> None:
    cases = _load_cases()

    tokenize_pipeline = Pipeline(["clean", "tokenize"])
    attached_pipeline = Pipeline(["clean", "tokenize", "attach_suffixes"])
    filtered_pipeline = Pipeline(
        ["clean", "tokenize", "attach_suffixes", "remove_stopwords"]
    )

    for case in cases:
        text = case["text"]

        cleaned = _unwrap_cleaned_text(clean_text(text))
        assert cleaned == case["expected_clean"], case["id"]

        tokens = tokenize_pipeline(text)
        assert tokens == case["expected_tokens"], case["id"]

        attached_tokens = attached_pipeline(text)
        assert attached_tokens == case["expected_attached_tokens"], case["id"]

        filtered_tokens = filtered_pipeline(text)
        assert filtered_tokens == case["expected_filtered_tokens"], case["id"]
