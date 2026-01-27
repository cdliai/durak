#!/usr/bin/env python3
"""
Lemmatization Quality Evaluation Script

Evaluates different lemmatization strategies against gold-standard test sets.
Outputs precision, recall, F1, and strategy-specific metrics.

Usage:
    python scripts/evaluate_lemmatizer.py
    python scripts/evaluate_lemmatizer.py --test-set resources/tr/lemmas/eval/gold_standard.tsv
    python scripts/evaluate_lemmatizer.py --strategy hybrid --verbose
"""

from __future__ import annotations

import argparse
import csv
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "python"))

from durak.lemmatizer import Lemmatizer, Strategy


@dataclass
class EvaluationResult:
    """Evaluation metrics for a single strategy."""
    
    strategy: Strategy
    test_set: str
    total: int
    correct: int
    incorrect: int
    accuracy: float
    error_rate: float
    
    # Strategy-specific metrics (if collect_metrics=True)
    lookup_hit_rate: float | None = None
    avg_call_time_ms: float | None = None
    
    def __str__(self) -> str:
        lines = [
            f"\n{'='*60}",
            f"Strategy: {self.strategy.upper()}",
            f"{'='*60}",
            f"Test Set:     {self.test_set}",
            f"Total Cases:  {self.total}",
            f"Correct:      {self.correct} ({self.accuracy:.2%})",
            f"Incorrect:    {self.incorrect} ({self.error_rate:.2%})",
        ]
        
        if self.lookup_hit_rate is not None:
            lines.append(f"Lookup Hits:  {self.lookup_hit_rate:.2%}")
        if self.avg_call_time_ms is not None:
            lines.append(f"Avg Time:     {self.avg_call_time_ms:.3f}ms")
        
        return "\n".join(lines)


def load_test_set(path: Path) -> list[tuple[str, str, str]]:
    """Load TSV test set (word, lemma, source).
    
    Args:
        path: Path to TSV file with format: inflected<TAB>lemma<TAB>source
        
    Returns:
        List of (word, expected_lemma, source) tuples
    """
    test_cases = []
    
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.reader(f, delimiter="\t")
        
        for line in reader:
            # Skip empty lines and comments
            if not line or line[0].startswith("#"):
                continue
            
            if len(line) < 2:
                print(f"Warning: Skipping malformed line: {line}", file=sys.stderr)
                continue
            
            word = line[0].strip()
            expected_lemma = line[1].strip()
            source = line[2].strip() if len(line) > 2 else "unknown"
            
            test_cases.append((word, expected_lemma, source))
    
    return test_cases


def evaluate_strategy(
    strategy: Strategy,
    test_cases: list[tuple[str, str, str]],
    collect_metrics: bool = True,
    verbose: bool = False,
) -> EvaluationResult:
    """Evaluate a single lemmatization strategy.
    
    Args:
        strategy: Lemmatization strategy to test
        test_cases: List of (word, expected_lemma, source) tuples
        collect_metrics: Enable performance metrics collection
        verbose: Print per-case results
        
    Returns:
        EvaluationResult with accuracy and metrics
    """
    lemmatizer = Lemmatizer(strategy=strategy, collect_metrics=collect_metrics)
    
    correct = 0
    incorrect = 0
    errors = []
    
    for word, expected_lemma, source in test_cases:
        predicted = lemmatizer(word)
        
        if predicted == expected_lemma:
            correct += 1
            if verbose:
                print(f"✓ {word} → {predicted} (expected: {expected_lemma})")
        else:
            incorrect += 1
            errors.append((word, expected_lemma, predicted, source))
            if verbose:
                print(f"✗ {word} → {predicted} (expected: {expected_lemma}) [{source}]")
    
    total = len(test_cases)
    accuracy = correct / total if total > 0 else 0.0
    error_rate = incorrect / total if total > 0 else 0.0
    
    # Extract performance metrics if available
    lookup_hit_rate = None
    avg_call_time_ms = None
    
    if collect_metrics:
        metrics = lemmatizer.get_metrics()
        lookup_hit_rate = metrics.cache_hit_rate
        avg_call_time_ms = metrics.avg_call_time_ms
    
    result = EvaluationResult(
        strategy=strategy,
        test_set=Path(test_cases[0][0]).parent.name if test_cases else "unknown",
        total=total,
        correct=correct,
        incorrect=incorrect,
        accuracy=accuracy,
        error_rate=error_rate,
        lookup_hit_rate=lookup_hit_rate,
        avg_call_time_ms=avg_call_time_ms,
    )
    
    # Print error analysis if verbose
    if verbose and errors:
        print(f"\n{'='*60}")
        print(f"ERROR ANALYSIS ({strategy})")
        print(f"{'='*60}")
        for word, expected, predicted, source in errors[:20]:  # Limit to first 20
            print(f"{word:15} → {predicted:15} (expected: {expected:15}) [{source}]")
        if len(errors) > 20:
            print(f"... and {len(errors) - 20} more errors")
    
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate lemmatization strategies against test sets"
    )
    parser.add_argument(
        "--test-set",
        type=Path,
        default=Path("resources/tr/lemmas/eval/gold_standard.tsv"),
        help="Path to TSV test set (default: gold_standard.tsv)",
    )
    parser.add_argument(
        "--strategy",
        type=str,
        choices=["lookup", "heuristic", "hybrid", "all"],
        default="all",
        help="Strategy to evaluate (default: all)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print per-case results and error analysis",
    )
    parser.add_argument(
        "--no-metrics",
        action="store_true",
        help="Disable performance metrics collection",
    )
    
    args = parser.parse_args()
    
    # Load test set
    if not args.test_set.exists():
        print(f"Error: Test set not found: {args.test_set}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading test set: {args.test_set}")
    test_cases = load_test_set(args.test_set)
    print(f"Loaded {len(test_cases)} test cases\n")
    
    # Determine which strategies to evaluate
    strategies: list[Strategy] = (
        ["lookup", "heuristic", "hybrid"]
        if args.strategy == "all"
        else [args.strategy]  # type: ignore
    )
    
    # Run evaluation
    results = []
    for strategy in strategies:
        result = evaluate_strategy(
            strategy=strategy,
            test_cases=test_cases,
            collect_metrics=not args.no_metrics,
            verbose=args.verbose,
        )
        results.append(result)
        print(result)
    
    # Print comparison table if multiple strategies
    if len(results) > 1:
        print(f"\n{'='*60}")
        print("STRATEGY COMPARISON")
        print(f"{'='*60}")
        print(f"{'Strategy':<12} {'Accuracy':>10} {'Lookup Hits':>12} {'Avg Time (ms)':>14}")
        print("-" * 60)
        
        for result in results:
            lookup_str = (
                f"{result.lookup_hit_rate:.1%}" 
                if result.lookup_hit_rate is not None 
                else "N/A"
            )
            time_str = (
                f"{result.avg_call_time_ms:.3f}" 
                if result.avg_call_time_ms is not None 
                else "N/A"
            )
            print(
                f"{result.strategy:<12} "
                f"{result.accuracy:>9.2%} "
                f"{lookup_str:>12} "
                f"{time_str:>14}"
            )
    
    # Return exit code based on accuracy (fail if any strategy <80%)
    min_accuracy = min(r.accuracy for r in results)
    if min_accuracy < 0.80:
        print(
            f"\n⚠️  Warning: Minimum accuracy ({min_accuracy:.2%}) below threshold (80%)",
            file=sys.stderr,
        )
        sys.exit(1)
    
    print(f"\n✅ All strategies passed (min accuracy: {min_accuracy:.2%})")
    sys.exit(0)


if __name__ == "__main__":
    main()
