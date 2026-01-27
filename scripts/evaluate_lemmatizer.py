#!/usr/bin/env python3
"""
Lemmatization Evaluation Framework

Evaluates precision, recall, and F1 scores for different lemmatization strategies
against gold-standard test sets.

Usage:
    python scripts/evaluate_lemmatizer.py [--test-set PATH] [--strategy STRATEGY]
    python scripts/evaluate_lemmatizer.py --all  # Compare all strategies
"""

import argparse
import json
from pathlib import Path

try:
    from durak.lemmatizer import Lemmatizer
except ImportError:
    print("❌ Error: durak package not installed. Run 'pip install -e .' first.")
    exit(1)


def load_test_set(test_set_path: Path) -> list[tuple[str, str, str]]:
    """
    Load gold-standard test set from TSV file.
    
    Returns:
        List of (inflected_word, expected_lemma, source) tuples
    """
    test_cases = []
    
    with open(test_set_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue
                
            parts = line.split("\t")
            if len(parts) >= 2:
                inflected = parts[0].strip()
                lemma = parts[1].strip()
                source = parts[2].strip() if len(parts) >= 3 else "unknown"
                test_cases.append((inflected, lemma, source))
    
    return test_cases


def evaluate_strategy(
    strategy: str,
    test_set_path: Path,
    verbose: bool = False
) -> dict:
    """
    Evaluate a single lemmatization strategy.
    
    Args:
        strategy: "lookup", "heuristic", or "hybrid"
        test_set_path: Path to gold-standard TSV file
        verbose: If True, print per-word results
    
    Returns:
        Dictionary with evaluation metrics
    """
    lemmatizer = Lemmatizer(strategy=strategy)
    test_cases = load_test_set(test_set_path)
    
    correct = 0
    errors = []
    
    for inflected, expected_lemma, source in test_cases:
        predicted_lemma = lemmatizer(inflected)
        
        if predicted_lemma == expected_lemma:
            correct += 1
            if verbose:
                print(f"✓ {inflected} → {predicted_lemma}")
        else:
            errors.append({
                "word": inflected,
                "expected": expected_lemma,
                "predicted": predicted_lemma,
                "source": source
            })
            if verbose:
                print(f"✗ {inflected} → {predicted_lemma} (expected: {expected_lemma})")
    
    total = len(test_cases)
    accuracy = correct / total if total > 0 else 0.0
    
    return {
        "strategy": strategy,
        "test_set": str(test_set_path.name),
        "total": total,
        "correct": correct,
        "incorrect": total - correct,
        "accuracy": accuracy,
        "errors": errors
    }


def print_results(results: Dict, show_errors: bool = False):
    """Pretty-print evaluation results"""
    print(f"\n{'='*60}")
    print(f"Strategy: {results['strategy'].upper()}")
    print(f"Test Set: {results['test_set']}")
    print(f"{'='*60}")
    print(f"Total cases:    {results['total']}")
    print(f"Correct:        {results['correct']} ({results['accuracy']:.1%})")
    print(f"Incorrect:      {results['incorrect']}")
    print(f"Accuracy:       {results['accuracy']:.1%}")
    
    if show_errors and results['errors']:
        print(f"\n{'-'*60}")
        print("Errors:")
        print(f"{'-'*60}")
        for err in results['errors'][:10]:  # Show first 10 errors
            print(f"  {err['word']:<15} → {err['predicted']:<10} (expected: {err['expected']})")
        
        if len(results['errors']) > 10:
            print(f"  ... and {len(results['errors']) - 10} more errors")


def compare_strategies(test_set_path: Path, show_errors: bool = False):
    """Compare all three strategies side-by-side"""
    strategies = ["lookup", "heuristic", "hybrid"]
    all_results = []
    
    print(f"\n📊 Evaluating all strategies on {test_set_path.name}...")
    
    for strategy in strategies:
        results = evaluate_strategy(strategy, test_set_path, verbose=False)
        all_results.append(results)
        print_results(results, show_errors=show_errors)
    
    # Print comparison table
    print(f"\n{'='*60}")
    print("STRATEGY COMPARISON")
    print(f"{'='*60}")
    print(f"{'Strategy':<15} {'Accuracy':>10} {'Correct':>10} {'Total':>10}")
    print(f"{'-'*60}")
    
    for res in all_results:
        print(
            f"{res['strategy']:<15} "
            f"{res['accuracy']:>9.1%} "
            f"{res['correct']:>10} "
            f"{res['total']:>10}"
        )
    
    return all_results


def save_baseline(results: list[Dict], baseline_path: Path):
    """Save evaluation results as baseline for regression detection"""
    baseline_data = {
        "baseline_version": "0.4.0",
        "test_set": results[0]["test_set"],
        "strategies": {
            res["strategy"]: {
                "accuracy": res["accuracy"],
                "correct": res["correct"],
                "total": res["total"]
            }
            for res in results
        }
    }
    
    baseline_path.parent.mkdir(parents=True, exist_ok=True)
    with open(baseline_path, "w") as f:
        json.dump(baseline_data, f, indent=2)
    
    print(f"\n✅ Baseline saved to {baseline_path}")


def check_regression(results: list[Dict], baseline_path: Path, threshold: float = 0.05):
    """Check if accuracy dropped significantly from baseline"""
    if not baseline_path.exists():
        print(f"\n⚠️  No baseline found at {baseline_path}")
        return False
    
    with open(baseline_path) as f:
        baseline = json.load(f)
    
    print(f"\n🔍 Checking for regressions (threshold: {threshold:.1%})...")
    
    regression_found = False
    
    for res in results:
        strategy = res["strategy"]
        current_acc = res["accuracy"]
        baseline_acc = baseline["strategies"][strategy]["accuracy"]
        diff = current_acc - baseline_acc
        
        status = "✅" if diff >= -threshold else "❌"
        print(f"{status} {strategy:<12} {baseline_acc:.1%} → {current_acc:.1%} ({diff:+.1%})")
        
        if diff < -threshold:
            regression_found = True
    
    return regression_found


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate lemmatization strategies",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Evaluate single strategy
  python scripts/evaluate_lemmatizer.py --strategy lookup
  
  # Compare all strategies
  python scripts/evaluate_lemmatizer.py --all
  
  # Save results as baseline
  python scripts/evaluate_lemmatizer.py --all --save-baseline
  
  # Check for regressions
  python scripts/evaluate_lemmatizer.py --all --check-regression
        """
    )
    
    parser.add_argument(
        "--test-set",
        type=Path,
        default=Path("resources/tr/lemmas/eval/gold_standard.tsv"),
        help="Path to gold-standard test set (default: resources/tr/lemmas/eval/gold_standard.tsv)"
    )
    
    parser.add_argument(
        "--strategy",
        choices=["lookup", "heuristic", "hybrid"],
        help="Evaluate a single strategy"
    )
    
    parser.add_argument(
        "--all",
        action="store_true",
        help="Compare all strategies"
    )
    
    parser.add_argument(
        "--show-errors",
        action="store_true",
        help="Show detailed error cases"
    )
    
    parser.add_argument(
        "--save-baseline",
        action="store_true",
        help="Save results as baseline for regression detection"
    )
    
    parser.add_argument(
        "--check-regression",
        action="store_true",
        help="Check for regressions against saved baseline"
    )
    
    parser.add_argument(
        "--baseline-path",
        type=Path,
        default=Path("benchmarks/lemmatization_baseline.json"),
        help="Path to baseline file (default: benchmarks/lemmatization_baseline.json)"
    )
    
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.05,
        help="Regression threshold (default: 0.05 = 5%%)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Print per-word results"
    )
    
    args = parser.parse_args()
    
    # Validate test set exists
    if not args.test_set.exists():
        print(f"❌ Error: Test set not found: {args.test_set}")
        print("   Expected path: resources/tr/lemmas/eval/gold_standard.tsv")
        exit(1)
    
    # Run evaluation
    if args.all:
        results = compare_strategies(args.test_set, show_errors=args.show_errors)
        
        if args.save_baseline:
            save_baseline(results, args.baseline_path)
        
        if args.check_regression:
            if check_regression(results, args.baseline_path, args.threshold):
                print("\n❌ Regression detected!")
                exit(1)
            else:
                print("\n✅ No regressions detected")
    
    elif args.strategy:
        results = evaluate_strategy(args.strategy, args.test_set, verbose=args.verbose)
        print_results(results, show_errors=args.show_errors)
    
    else:
        # Default: compare all strategies
        results = compare_strategies(args.test_set, show_errors=args.show_errors)
        
        if args.check_regression:
            if check_regression(results, args.baseline_path, args.threshold):
                print("\n❌ Regression detected!")
                exit(1)
            else:
                print("\n✅ No regressions detected")


if __name__ == "__main__":
    main()
