"""Benchmark and quality checks for OCR corpora.

This script evaluates:
- Offset correctness for normalize-tokenize output
- Rust vs Python tokenization parity
- Throughput on a real dataset split
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass
from typing import Iterable, List, Tuple

from durak.tokenizer import REGEX_TOKEN_PATTERN, normalize_tokens
import durak

try:
    from datasets import load_dataset
except ImportError:  # pragma: no cover
    load_dataset = None  # type: ignore[assignment]


def _default_dataset() -> str:
    return "fatihburakkaragoz/old-nogay-turkish-ocr-corpus"


def _candidate_text_field(sample: object) -> str | None:
    if isinstance(sample, str):
        return sample
    if not isinstance(sample, dict):
        return None

    for key in ("text", "sentence", "content", "ocr", "value"):
        value = sample.get(key)
        if isinstance(value, str) and value.strip():
            return value

    # First non-empty string field as fallback.
    for value in sample.values():
        if isinstance(value, str) and value.strip():
            return value

    return None


def _python_tokenize_with_normalized_offsets(text: str) -> List[Tuple[str, int, int]]:
    tokens = []
    for match in REGEX_TOKEN_PATTERN.finditer(text):
        token = match.group(0)
        normalized_token = normalize_tokens([token])[0] if token else ""
        tokens.append((normalized_token, match.start(), match.end()))
    return tokens


def _iter_split_texts(split_obj, text_column: str | None, max_rows: int) -> Iterable[str]:
    count = 0
    for row in split_obj:
        if max_rows > 0 and count >= max_rows:
            break

        if isinstance(row, str):
            text = row
        elif isinstance(row, dict):
            if text_column and isinstance(row.get(text_column), str):
                text = row[text_column]
            else:
                text = _candidate_text_field(row)  # type: ignore[assignment]
        else:
            text = None

        if not isinstance(text, str):
            continue

        text = text.strip()
        if not text:
            continue

        count += 1
        yield text


@dataclass
class SplitReport:
    split: str
    rows: int = 0
    total_tokens: int = 0
    offset_errors: int = 0
    token_shape_errors: int = 0
    speed_texts_per_s: float = 0.0
    speed_tokens_per_s: float = 0.0
    elapsed_ms: float = 0.0

    def total_errors(self) -> int:
        return self.offset_errors + self.token_shape_errors


def _benchmark_function(
    fn, texts: List[str]
) -> Tuple[float, int]:
    start = time.perf_counter()
    total_tokens = 0
    for text in texts:
        total_tokens += len(fn(text))
    elapsed = (time.perf_counter() - start) * 1000
    return elapsed, total_tokens


def run_split_benchmark(
    split_name: str,
    split_obj,
    text_column: str | None,
    max_rows: int,
) -> SplitReport:
    if load_dataset is None:
        raise RuntimeError("`datasets` package required for this benchmark.")

    rust_ok = hasattr(durak, "_durak_core")
    rust_tokenize = getattr(durak, "tokenize_with_normalized_offsets", None)
    if not callable(rust_tokenize):
        raise RuntimeError(
            "Rust extension is required for dataset quality benchmark."
        )

    report = SplitReport(split=split_name)
    texts: List[str] = []

    for text in _iter_split_texts(split_obj, text_column, max_rows):
        report.rows += 1
        texts.append(text)

        rust_tokens = durak.tokenize_with_normalized_offsets(text)
        py_tokens = _python_tokenize_with_normalized_offsets(text)
        report.total_tokens += len(rust_tokens)

        if len(rust_tokens) != len(py_tokens):
            report.token_shape_errors += 1
            continue

        for (tok_r, start_r, end_r), (tok_p, start_p, end_p) in zip(
            rust_tokens, py_tokens
        ):
            if not (0 <= start_r <= end_r <= len(text)):
                report.offset_errors += 1
            if not (start_r == start_p and end_r == end_p and tok_r == tok_p):
                report.token_shape_errors += 1

    if not texts:
        return report

    py_elapsed, py_tokens = _benchmark_function(
        _python_tokenize_with_normalized_offsets, texts
    )
    rust_elapsed, rust_tokens = _benchmark_function(rust_tokenize, texts)
    report.speed_texts_per_s = len(texts) / (rust_elapsed / 1000) if rust_elapsed > 0 else 0.0
    report.speed_tokens_per_s = rust_tokens / (rust_elapsed / 1000) if rust_elapsed > 0 else 0.0
    report.elapsed_ms = rust_elapsed
    _ = py_elapsed
    _ = py_tokens
    return report


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dataset",
        default=_default_dataset(),
        help="Hugging Face dataset id.",
    )
    parser.add_argument(
        "--splits",
        nargs="*",
        default=["train", "validation", "test"],
        help="Dataset splits to benchmark.",
    )
    parser.add_argument(
        "--text-column",
        default=None,
        help="Explicit text field name.",
    )
    parser.add_argument(
        "--max-rows-per-split",
        type=int,
        default=0,
        help="Limit rows per split (0 = all).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if load_dataset is None:
        print("`datasets` package is not installed. Install with `pip install datasets`.")
        return

    dataset = load_dataset(args.dataset)
    split_names = list(dataset.keys()) if hasattr(dataset, "keys") else ["train"]
    print(f"Loaded dataset: {args.dataset}")
    print(f"Available splits: {', '.join(split_names)}")

    target_splits = [s for s in args.splits if s in split_names]
    if not target_splits:
        raise SystemExit(f"No target splits found in dataset. Available: {split_names}")

    reports = []
    for split_name in target_splits:
        split_obj = dataset[split_name]
        report = run_split_benchmark(
            split_name=split_name,
            split_obj=split_obj,
            text_column=args.text_column,
            max_rows=args.max_rows_per_split,
        )
        reports.append(report)

    print("\n================ Dataset benchmark summary =================")
    for report in reports:
        lines = [
            f"split={report.split}",
            f"rows={report.rows}",
            f"tokens={report.total_tokens}",
            f"errors(offset={report.offset_errors}, mismatch={report.token_shape_errors})",
            f"rust_time_ms={report.elapsed_ms:.2f}",
            f"throughput_tokens_s={report.speed_tokens_per_s:.1f}",
            f"throughput_rows_s={report.speed_texts_per_s:.1f}",
            f"errors_per_million_rows={report.total_errors()/max(report.rows,1)*1_000_000:.2f}",
        ]
        print(" | ".join(lines))

    total_rows = sum(r.rows for r in reports)
    total_tokens = sum(r.total_tokens for r in reports)
    total_errors = sum(r.total_errors() for r in reports)
    print("\nTotal rows:", total_rows)
    print("Total tokens:", total_tokens)
    print("Total errors:", total_errors)
    if total_rows:
        print(
            f"Overall errors per 100k rows: {total_errors / total_rows * 100_000:.2f}"
        )


if __name__ == "__main__":
    main()
