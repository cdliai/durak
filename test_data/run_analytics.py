#!/usr/bin/env python3
"""
Durak Pipeline Analytics & Correctness Checker

This script runs comprehensive tests on Turkish text samples and provides:
- Speed/performance analytics
- Correctness verification against expected outputs
- Detailed reporting of pipeline behavior

Usage:
    python run_analytics.py
    python run_analytics.py --verbose
    python run_analytics.py --iterations 100
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

# Add the project to path - need parent directory for proper imports
# IMPORTANT: Insert at beginning to override any installed versions
script_dir = Path(__file__).parent.parent  # Go up to project root
sys.path.insert(0, str(script_dir / "python"))
sys.path.insert(0, str(script_dir))  # Also add project root

# Debug: Show which durak is being used
if "-v" in sys.argv or "--verbose" in sys.argv:
    import durak
    print(f"Using durak from: {durak.__file__}", file=sys.stderr)

try:
    from durak import (
        Lemmatizer,
        Normalizer,
        attach_detached_suffixes,
        clean_text,
        tokenize,
        extract_emojis,
        normalize_case,
    )
    from durak import _durak_core
    # Check if Rust extension is actually functional (not None)
    RUST_AVAILABLE = _durak_core is not None
except ImportError as e:
    print(f"Warning: Some imports failed: {e}")
    RUST_AVAILABLE = False
    # Try individual imports
    try:
        from durak.cleaning import normalize_case, clean_text, extract_emojis
    except ImportError:
        normalize_case = None
        clean_text = None
        extract_emojis = None
    try:
        from durak.suffixes import attach_detached_suffixes
    except ImportError:
        attach_detached_suffixes = None
    try:
        from durak.tokenizer import tokenize
    except ImportError:
        tokenize = None
    try:
        from durak import Lemmatizer, Normalizer
    except ImportError:
        Lemmatizer = None
        Normalizer = None


class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_header(text: str) -> None:
    print(f"\n{Colors.HEADER}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*60}{Colors.ENDC}\n")


def print_section(text: str) -> None:
    print(f"\n{Colors.BLUE}{'─'*60}{Colors.ENDC}")
    print(f"{Colors.CYAN}{text}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'─'*60}{Colors.ENDC}")


def print_pass(text: str) -> None:
    print(f"{Colors.GREEN}✓ PASS:{Colors.ENDC} {text}")


def print_fail(text: str, details: str = "") -> None:
    print(f"{Colors.RED}✗ FAIL:{Colors.ENDC} {text}")
    if details:
        print(f"       {Colors.YELLOW}{details}{Colors.ENDC}")


def print_info(text: str) -> None:
    print(f"{Colors.CYAN}ℹ INFO:{Colors.ENDC} {text}")


def load_test_files() -> dict[str, str]:
    """Load all test files from the test_data directory."""
    test_dir = Path(__file__).parent
    test_files = {}
    
    for txt_file in sorted(test_dir.glob("*.txt")):
        content = txt_file.read_text(encoding="utf-8")
        # Skip comment lines
        lines = [line for line in content.split('\n') if not line.startswith('#')]
        test_files[txt_file.stem] = '\n'.join(lines).strip()
    
    return test_files


def benchmark(func, text: str, iterations: int = 100) -> dict[str, Any]:
    """Benchmark a function over multiple iterations."""
    # Warmup
    for _ in range(10):
        func(text)
    
    # Actual benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        result = func(text)
    end = time.perf_counter()
    
    total_time = (end - start) * 1000  # Convert to ms
    avg_time = total_time / iterations
    
    return {
        "total_ms": total_time,
        "avg_ms": avg_time,
        "iterations": iterations,
        "result": result,
    }


def test_turkish_i_handling(verbose: bool = False) -> dict[str, Any]:
    """Test Turkish I/ı and İ/i handling."""
    print_section("Turkish I/ı & İ/i Handling")
    
    if normalize_case is None:
        print_info("Skipping Turkish I tests - normalize_case not available")
        return {"passed": 0, "failed": 0, "skipped": True}
    
    test_cases = [
        ("İSTANBUL", "istanbul"),    # İ → i (dotted)
        ("IĞDIR", "ığdır"),          # I → ı (dotless)
        ("İngiltere", "ingiltere"),  # İ → i (dotted)
        ("ÇİÇEKLER", "çiçekler"),    # Normal Turkish chars
        ("Istanbul", "ıstanbul"),    # I → ı (dotless) - technically correct
    ]
    
    results = {"passed": 0, "failed": 0, "tests": []}
    
    for input_text, expected in test_cases:
        normalized = normalize_case(input_text, mode="lower")
        passed = normalized == expected
        
        test_result = {
            "input": input_text,
            "expected": expected,
            "got": normalized,
            "passed": passed,
        }
        results["tests"].append(test_result)
        
        if passed:
            results["passed"] += 1
            if verbose:
                print_pass(f"'{input_text}' → '{normalized}'")
        else:
            results["failed"] += 1
            print_fail(f"'{input_text}'", f"Expected: '{expected}', Got: '{normalized}'")
    
    return results


def test_cleaning_functions(test_data: dict[str, str], verbose: bool = False) -> dict[str, Any]:
    """Test text cleaning functions."""
    print_section("Text Cleaning Functions")
    
    if clean_text is None or extract_emojis is None:
        print_info("Skipping cleaning tests - functions not available")
        return {"passed": 0, "failed": 0, "skipped": True}
    
    results = {"passed": 0, "failed": 0, "tests": []}
    
    # Test emoji extraction
    if "03_social_media" in test_data:
        text = "Harika! 🎉🎊 Çok güzel olmuş 😍"
        emojis = extract_emojis(text)
        expected = ["🎉", "🎊", "😍"]
        passed = emojis == expected
        
        if passed:
            results["passed"] += 1
            if verbose:
                print_pass(f"Emoji extraction: found {len(emojis)} emojis")
        else:
            results["failed"] += 1
            print_fail("Emoji extraction", f"Expected: {expected}, Got: {emojis}")
    
    # Test cleaning with emoji modes
    test_text = "Harika! 🎉 Çok güzel"
    
    # Mode: keep
    cleaned_keep = clean_text(test_text, emoji_mode="keep")
    if "🎉" in cleaned_keep:
        results["passed"] += 1
        if verbose:
            print_pass("Emoji mode 'keep' preserved emojis")
    else:
        results["failed"] += 1
        print_fail("Emoji mode 'keep'", "Emojis were removed")
    
    # Mode: remove
    cleaned_remove = clean_text(test_text, emoji_mode="remove")
    if "🎉" not in cleaned_remove:
        results["passed"] += 1
        if verbose:
            print_pass("Emoji mode 'remove' removed emojis")
    else:
        results["failed"] += 1
        print_fail("Emoji mode 'remove'", "Emojis were not removed")
    
    # Mode: extract
    cleaned_extract, extracted = clean_text(test_text, emoji_mode="extract")
    if isinstance(extracted, list) and "🎉" in extracted and "🎉" not in cleaned_extract:
        results["passed"] += 1
        if verbose:
            print_pass("Emoji mode 'extract' returned tuple with emojis")
    else:
        results["failed"] += 1
        print_fail("Emoji mode 'extract'", f"Unexpected result: {type(extracted)}, {extracted}")
    
    return results


def test_suffix_reattachment(verbose: bool = False) -> dict[str, Any]:
    """Test detached suffix reattachment."""
    print_section("Detached Suffix Reattachment")
    
    if attach_detached_suffixes is None:
        print_info("Skipping suffix tests - function not available")
        return {"passed": 0, "failed": 0, "skipped": True}
    
    test_cases = [
        (["Ankara", "'", "da"], ["Ankara'da"]),
        (["İstanbul", "'", "ya"], ["İstanbul'ya"]),  # Dative case with buffer consonant
        (["ev", "de"], ["evde"]),  # Without apostrophe
        (["Ankara", "da"], ["Ankarada"]),  # Without apostrophe
        (["İstanbul", "'", "da"], ["İstanbul'da"]),  # Locative case
    ]
    
    results = {"passed": 0, "failed": 0, "tests": []}
    
    for tokens, expected in test_cases:
        result = attach_detached_suffixes(tokens)
        passed = result == expected
        
        if passed:
            results["passed"] += 1
            if verbose:
                print_pass(f"{' '.join(tokens)} → {result}")
        else:
            results["failed"] += 1
            print_fail(f"{' '.join(tokens)}", f"Expected: {expected}, Got: {result}")
    
    return results


def test_tokenization(test_data: dict[str, str], verbose: bool = False) -> dict[str, Any]:
    """Test tokenization on various text types."""
    print_section("Tokenization Tests")
    
    if tokenize is None:
        print_info("Skipping tokenization tests - function not available")
        return {"passed": 0, "failed": 0, "skipped": True}
    
    results = {"passed": 0, "failed": 0, "tests": []}
    
    # Test basic tokenization
    text = "Türkiye'de NLP zor."
    tokens = tokenize(text)
    
    if len(tokens) >= 4 and "Türkiye'de" in tokens:
        results["passed"] += 1
        if verbose:
            print_pass(f"Basic tokenization: {tokens}")
    else:
        results["failed"] += 1
        print_fail("Basic tokenization", f"Unexpected tokens: {tokens}")
    
    # Test with punctuation stripping
    tokens_no_punct = tokenize(text, strip_punct=True)
    if "." not in tokens_no_punct:
        results["passed"] += 1
        if verbose:
            print_pass(f"Strip punctuation: {tokens_no_punct}")
    else:
        results["failed"] += 1
        print_fail("Strip punctuation", f"Punctuation still present: {tokens_no_punct}")
    
    return results


def test_lemmatization(verbose: bool = False) -> dict[str, Any]:
    """Test lemmatization functionality."""
    print_section("Lemmatization Tests")
    
    if not RUST_AVAILABLE or Lemmatizer is None:
        print_info("Skipping lemmatization tests - Rust extension not available")
        return {"passed": 0, "failed": 0, "skipped": True}
    
    lemmatizer = Lemmatizer(strategy="hybrid")
    
    test_cases = [
        ("kitaplar", "kitap"),
        ("evler", "ev"),
        ("geliyorum", "gel"),
        ("adamlar", "adam"),
    ]
    
    results = {"passed": 0, "failed": 0, "tests": []}
    
    for word, expected_lemma in test_cases:
        lemma = lemmatizer(word)
        passed = lemma == expected_lemma
        
        if passed:
            results["passed"] += 1
            if verbose:
                print_pass(f"'{word}' → '{lemma}'")
        else:
            results["failed"] += 1
            print_fail(f"'{word}'", f"Expected: '{expected_lemma}', Got: '{lemma}'")
    
    return results


def run_performance_benchmarks(test_data: dict[str, str], iterations: int = 100) -> dict[str, Any]:
    """Run performance benchmarks."""
    print_header("PERFORMANCE BENCHMARKS")
    
    results = {}
    
    # Combine all test texts into a corpus
    corpus = "\n\n".join(test_data.values())
    
    print(f"\nCorpus size: {len(corpus)} characters, {len(corpus.split())} words")
    print(f"Iterations: {iterations}\n")
    
    # Benchmark normalization
    if RUST_AVAILABLE:
        print_section("Rust vs Python Normalization")
        
        # Rust fast_normalize
        rust_result = benchmark(_durak_core.fast_normalize, "İSTANBUL'da NLP", iterations)
        print(f"  Rust fast_normalize:    {rust_result['avg_ms']:.4f} ms avg")
        
        # Python normalize_case
        py_result = benchmark(lambda x: normalize_case(x, mode="lower"), "İSTANBUL'da NLP", iterations)
        print(f"  Python normalize_case:  {py_result['avg_ms']:.4f} ms avg")
        
        speedup = py_result['avg_ms'] / rust_result['avg_ms']
        print(f"  {Colors.GREEN}Speedup: {speedup:.2f}x{Colors.ENDC}")
        
        results["normalization"] = {
            "rust_ms": rust_result['avg_ms'],
            "python_ms": py_result['avg_ms'],
            "speedup": speedup,
        }
        
        # Tokenization benchmark
        print_section("Tokenization")
        tok_result = benchmark(_durak_core.tokenize_with_offsets, corpus, iterations)
        print(f"  tokenize_with_offsets:  {tok_result['avg_ms']:.4f} ms avg")
        
        results["tokenization"] = {
            "avg_ms": tok_result['avg_ms'],
        }
    
    # Cleaning benchmark
    print_section("Text Cleaning")
    if clean_text:
        clean_result = benchmark(lambda x: clean_text(x, emoji_mode="extract"), corpus, iterations)
    else:
        clean_result = {"avg_ms": 0, "note": "Not available"}
    print(f"  clean_text (extract):   {clean_result['avg_ms']:.4f} ms avg")
    
    results["cleaning"] = {
        "avg_ms": clean_result['avg_ms'],
    }
    
    # Full pipeline benchmark
    print_section("Full Pipeline (clean → tokenize → suffix_reattach)")
    if clean_text and tokenize and attach_detached_suffixes:
        def full_pipeline(text: str) -> list[str]:
            cleaned = clean_text(text, emoji_mode="remove")
            tokens = tokenize(cleaned)
            return attach_detached_suffixes(tokens)
        
        pipeline_result = benchmark(full_pipeline, corpus, iterations // 10)  # Fewer iterations for full pipeline
        print(f"  Full pipeline:          {pipeline_result['avg_ms']:.4f} ms avg")
        
        results["full_pipeline"] = {
            "avg_ms": pipeline_result['avg_ms'],
        }
    else:
        print_info("Full pipeline not available - missing components")
    
    return results


def run_correctness_tests(test_data: dict[str, str], verbose: bool = False) -> dict[str, Any]:
    """Run all correctness tests."""
    print_header("CORRECTNESS TESTS")
    
    all_results = {}
    
    all_results["turkish_i"] = test_turkish_i_handling(verbose)
    all_results["cleaning"] = test_cleaning_functions(test_data, verbose)
    all_results["suffixes"] = test_suffix_reattachment(verbose)
    all_results["tokenization"] = test_tokenization(test_data, verbose)
    all_results["lemmatization"] = test_lemmatization(verbose)
    
    # Summary
    total_passed = sum(r.get("passed", 0) for r in all_results.values())
    total_failed = sum(r.get("failed", 0) for r in all_results.values())
    
    print_header("CORRECTNESS SUMMARY")
    print(f"\n  {Colors.GREEN}Passed: {total_passed}{Colors.ENDC}")
    print(f"  {Colors.RED}Failed: {total_failed}{Colors.ENDC}")
    print(f"  Total:  {total_passed + total_failed}")
    
    all_results["summary"] = {
        "passed": total_passed,
        "failed": total_failed,
        "total": total_passed + total_failed,
    }
    
    return all_results


def generate_detailed_report(test_data: dict[str, str], results: dict[str, Any], output_path: Path) -> None:
    """Generate a detailed JSON report."""
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rust_available": RUST_AVAILABLE,
        "test_files": list(test_data.keys()),
        "results": results,
    }
    
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n{Colors.CYAN}Detailed report saved to: {output_path}{Colors.ENDC}")


def main():
    parser = argparse.ArgumentParser(description="Durak Pipeline Analytics & Correctness Checker")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--iterations", "-i", type=int, default=100, help="Benchmark iterations")
    parser.add_argument("--report", "-r", type=Path, default=None, help="Save report to JSON file")
    parser.add_argument("--correctness-only", "-c", action="store_true", help="Run only correctness tests")
    parser.add_argument("--benchmark-only", "-b", action="store_true", help="Run only benchmarks")
    
    args = parser.parse_args()
    
    print_header("DURAK PIPELINE ANALYTICS")
    print(f"Rust extension: {Colors.GREEN if RUST_AVAILABLE else Colors.RED}{'Available' if RUST_AVAILABLE else 'Not Available'}{Colors.ENDC}")
    
    # Load test data
    test_data = load_test_files()
    print(f"Loaded {len(test_data)} test files")
    
    all_results = {}
    
    # Run tests
    if not args.benchmark_only:
        correctness_results = run_correctness_tests(test_data, args.verbose)
        all_results["correctness"] = correctness_results
    
    if not args.correctness_only:
        perf_results = run_performance_benchmarks(test_data, args.iterations)
        all_results["performance"] = perf_results
    
    # Save report if requested
    if args.report:
        generate_detailed_report(test_data, all_results, args.report)
    
    # Final status
    if not args.benchmark_only:
        failed = all_results.get("correctness", {}).get("summary", {}).get("failed", 0)
        if failed > 0:
            print(f"\n{Colors.RED}{Colors.BOLD}Some tests failed. Please review the output above.{Colors.ENDC}\n")
            sys.exit(1)
        else:
            print(f"\n{Colors.GREEN}{Colors.BOLD}All tests passed!{Colors.ENDC}\n")


if __name__ == "__main__":
    main()
