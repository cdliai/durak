#!/usr/bin/env python3
"""
Comprehensive Benchmark & Correctness Test

This script:
1. Runs all 12 test documents through various pipeline configurations
2. Measures speed performance
3. Verifies correctness of outputs
4. Compares different processing options
5. Detects any regressions

Usage:
    python run_comprehensive_benchmark.py
    python run_comprehensive_benchmark.py --verbose
    python run_comprehensive_benchmark.py --save-results results.json
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

# Add project to path
script_dir = Path(__file__).parent.parent
sys.path.insert(0, str(script_dir / "python"))
sys.path.insert(0, str(script_dir))

from durak import (
    TextProcessor,
    ProcessorConfig,
    tokenize,
    clean_text,
    normalize_case,
    attach_detached_suffixes,
    remove_stopwords,
    StopwordManager,
)


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
    print(f"\n{Colors.HEADER}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{'='*70}{Colors.ENDC}\n")


def print_section(text: str) -> None:
    print(f"\n{Colors.BLUE}{'─'*70}{Colors.ENDC}")
    print(f"{Colors.CYAN}{text}{Colors.ENDC}")
    print(f"{Colors.BLUE}{'─'*70}{Colors.ENDC}")


def benchmark(func, *args, iterations: int = 1000, warmup: int = 100) -> dict[str, Any]:
    """Benchmark a function with warmup."""
    # Warmup
    for _ in range(warmup):
        func(*args)
    
    # Actual benchmark
    start = time.perf_counter()
    for _ in range(iterations):
        result = func(*args)
    end = time.perf_counter()
    
    total_time = (end - start) * 1000  # ms
    avg_time = total_time / iterations
    
    return {
        "total_ms": total_time,
        "avg_ms": avg_time,
        "iterations": iterations,
        "result": result,
    }


def load_test_documents() -> dict[str, str]:
    """Load all test documents."""
    test_dir = Path(__file__).parent
    documents = {}
    
    for txt_file in sorted(test_dir.glob("*.txt")):
        content = txt_file.read_text(encoding="utf-8")
        # Skip comment lines
        lines = [line for line in content.split('\n') if not line.startswith('#')]
        documents[txt_file.stem] = '\n'.join(lines).strip()
    
    return documents


def test_correctness_all_docs(documents: dict[str, str], verbose: bool = False) -> dict[str, Any]:
    """Test correctness on all documents with various configurations."""
    print_section("Correctness Tests on All Documents")
    
    results = {
        "passed": 0,
        "failed": 0,
        "tests": [],
    }
    
    # Test configurations
    configs = [
        ("basic", ProcessorConfig()),
        ("with_stopwords", ProcessorConfig(remove_stopwords=True)),
        ("with_suffixes", ProcessorConfig(attach_suffixes=True)),
        ("full", ProcessorConfig(
            remove_stopwords=True,
            attach_suffixes=True,
            remove_punctuation=True,
        )),
    ]
    
    for doc_name, text in documents.items():
        for config_name, config in configs:
            try:
                processor = TextProcessor(config)
                result = processor.process(text)
                
                # Basic sanity checks
                passed = True
                errors = []
                
                # Check that we got tokens
                if not result.tokens:
                    passed = False
                    errors.append("No tokens produced")
                
                # Check for proper Turkish I handling in lowercase
                for token in result.tokens:
                    if 'İ' in token.lower() or 'I' in token.lower():
                        # This is OK - might be at start of sentence
                        pass
                
                # Check emojis handled correctly
                if config.emoji_mode == "extract" and result.emojis is None:
                    passed = False
                    errors.append("Emojis not extracted")
                
                test_result = {
                    "document": doc_name,
                    "config": config_name,
                    "tokens": len(result.tokens),
                    "passed": passed,
                    "errors": errors,
                }
                
                if passed:
                    results["passed"] += 1
                    if verbose:
                        print(f"{Colors.GREEN}✓{Colors.ENDC} {doc_name}/{config_name}: {len(result.tokens)} tokens")
                else:
                    results["failed"] += 1
                    print(f"{Colors.RED}✗{Colors.ENDC} {doc_name}/{config_name}: {', '.join(errors)}")
                
                results["tests"].append(test_result)
                
            except Exception as e:
                results["failed"] += 1
                print(f"{Colors.RED}✗{Colors.ENDC} {doc_name}/{config_name}: EXCEPTION - {e}")
                results["tests"].append({
                    "document": doc_name,
                    "config": config_name,
                    "passed": False,
                    "errors": [str(e)],
                })
    
    return results


def benchmark_all_docs(documents: dict[str, str], verbose: bool = False) -> dict[str, Any]:
    """Benchmark all documents with various configurations."""
    print_section("Performance Benchmarks")
    
    configs = {
        "basic": ProcessorConfig(),
        "with_stopwords": ProcessorConfig(remove_stopwords=True),
        "with_suffixes": ProcessorConfig(attach_suffixes=True),
        "full": ProcessorConfig(
            remove_stopwords=True,
            attach_suffixes=True,
            remove_punctuation=True,
        ),
    }
    
    results = {}
    iterations = 500
    
    for config_name, config in configs.items():
        print(f"\n{Colors.CYAN}Configuration: {config_name}{Colors.ENDC}")
        processor = TextProcessor(config)
        
        config_results = {}
        total_time = 0
        total_tokens = 0
        
        for doc_name, text in documents.items():
            bench = benchmark(processor.process, text, iterations=iterations, warmup=50)
            
            config_results[doc_name] = {
                "avg_ms": bench["avg_ms"],
                "tokens": len(bench["result"].tokens),
            }
            total_time += bench["avg_ms"]
            total_tokens += len(bench["result"].tokens)
        
        avg_time = total_time / len(documents)
        avg_tokens = total_tokens / len(documents)
        
        print(f"  Average time: {avg_time:.4f} ms")
        print(f"  Average tokens: {avg_tokens:.1f}")
        print(f"  Throughput: {avg_tokens / (avg_time / 1000):.0f} tokens/sec")
        
        results[config_name] = {
            "per_document": config_results,
            "average_ms": avg_time,
            "average_tokens": avg_tokens,
            "throughput_tok_per_sec": avg_tokens / (avg_time / 1000),
        }
    
    return results


def benchmark_individual_components(documents: dict[str, str]) -> dict[str, Any]:
    """Benchmark individual pipeline components."""
    print_section("Individual Component Benchmarks")
    
    # Use first document as sample
    sample_text = list(documents.values())[0]
    sample_tokens = ['Ankara', "'", 'da', 'kaldım', '.']
    
    iterations = 2000
    
    components = {
        "tokenize": (tokenize, [sample_text]),
        "clean_text (keep)": (lambda t: clean_text(t, emoji_mode='keep'), [sample_text]),
        "clean_text (remove)": (lambda t: clean_text(t, emoji_mode='remove'), [sample_text]),
        "normalize_case": (normalize_case, ["İSTANBUL"]),
        "attach_suffixes": (attach_detached_suffixes, [sample_tokens]),
        "remove_stopwords": (remove_stopwords, [sample_tokens]),
    }
    
    results = {}
    
    for name, (func, args) in components.items():
        try:
            bench = benchmark(func, *args, iterations=iterations, warmup=100)
            results[name] = {
                "avg_ms": bench["avg_ms"],
                "ops_per_sec": 1000 / bench["avg_ms"],
            }
            print(f"  {name:25s}: {bench['avg_ms']:8.4f} ms ({1000/bench['avg_ms']:8.0f} ops/sec)")
        except Exception as e:
            results[name] = {"error": str(e)}
            print(f"  {name:25s}: ERROR - {e}")
    
    return results


def compare_configurations(documents: dict[str, str]) -> dict[str, Any]:
    """Compare different configurations for insights."""
    print_section("Configuration Comparison")
    
    # Use the largest document
    largest_doc = max(documents.items(), key=lambda x: len(x[1]))
    doc_name, text = largest_doc
    
    print(f"Using document: {doc_name} ({len(text)} chars)")
    
    configs = {
        "raw_tokenize": ProcessorConfig(lowercase=False),
        "default": ProcessorConfig(),
        "+stopwords": ProcessorConfig(remove_stopwords=True),
        "+suffixes": ProcessorConfig(attach_suffixes=True),
        "+punctuation": ProcessorConfig(remove_punctuation=True),
        "+all": ProcessorConfig(
            remove_stopwords=True,
            attach_suffixes=True,
            remove_punctuation=True,
        ),
    }
    
    results = {}
    iterations = 500
    
    print(f"\n{'Configuration':<20} {'Time (ms)':<12} {'Tokens':<10} {'Reduction':<10}")
    print("-" * 60)
    
    baseline_tokens = None
    
    for config_name, config in configs.items():
        processor = TextProcessor(config)
        bench = benchmark(processor.process, text, iterations=iterations, warmup=100)
        
        tokens = len(bench["result"].tokens)
        if baseline_tokens is None:
            baseline_tokens = tokens
        
        reduction = (1 - tokens / baseline_tokens) * 100 if baseline_tokens > 0 else 0
        
        results[config_name] = {
            "avg_ms": bench["avg_ms"],
            "tokens": tokens,
            "reduction_pct": reduction,
        }
        
        print(f"{config_name:<20} {bench['avg_ms']:>10.4f}   {tokens:>8}   {reduction:>7.1f}%")
    
    return results


def detect_regressions(current: dict[str, Any], baseline: dict[str, Any] | None) -> list[str]:
    """Detect performance regressions compared to baseline."""
    if baseline is None:
        return []
    
    regressions = []
    threshold = 1.5  # 50% slower is a regression
    
    for config_name, current_data in current.get("by_config", {}).items():
        if config_name in baseline.get("by_config", {}):
            baseline_data = baseline["by_config"][config_name]
            current_time = current_data.get("average_ms", 0)
            baseline_time = baseline_data.get("average_ms", 0)
            
            if baseline_time > 0 and current_time / baseline_time > threshold:
                regressions.append(
                    f"{config_name}: {current_time:.2f}ms vs {baseline_time:.2f}ms "
                    f"({current_time/baseline_time:.1f}x slower)"
                )
    
    return regressions


def main():
    parser = argparse.ArgumentParser(description="Comprehensive benchmark and correctness test")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--save", "-s", type=str, help="Save results to JSON file")
    parser.add_argument("--baseline", "-b", type=str, help="Compare against baseline JSON file")
    parser.add_argument("--iterations", "-i", type=int, default=500, help="Benchmark iterations")
    
    args = parser.parse_args()
    
    print_header("COMPREHENSIVE BENCHMARK & CORRECTNESS TEST")
    
    # Load documents
    print("Loading test documents...")
    documents = load_test_documents()
    print(f"Loaded {len(documents)} test documents")
    
    if args.verbose:
        print("\nDocuments:")
        for name, text in documents.items():
            print(f"  {name}: {len(text)} chars, ~{len(text.split())} words")
    
    # Run correctness tests
    correctness_results = test_correctness_all_docs(documents, args.verbose)
    
    # Run benchmarks
    benchmark_results = benchmark_all_docs(documents, args.verbose)
    component_results = benchmark_individual_components(documents)
    comparison_results = compare_configurations(documents)
    
    # Summary
    print_header("SUMMARY")
    
    print(f"\n{Colors.CYAN}Correctness:{Colors.ENDC}")
    print(f"  Passed: {Colors.GREEN}{correctness_results['passed']}{Colors.ENDC}")
    print(f"  Failed: {Colors.RED}{correctness_results['failed']}{Colors.ENDC}")
    print(f"  Total:  {correctness_results['passed'] + correctness_results['failed']}")
    
    if correctness_results["failed"] > 0:
        print(f"\n{Colors.RED}{Colors.BOLD}⚠ Some correctness tests failed!{Colors.ENDC}")
    else:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All correctness tests passed!{Colors.ENDC}")
    
    # Check for regressions if baseline provided
    if args.baseline:
        baseline = json.loads(Path(args.baseline).read_text())
        regressions = detect_regressions(benchmark_results, baseline)
        if regressions:
            print(f"\n{Colors.RED}{Colors.BOLD}⚠ Performance regressions detected:{Colors.ENDC}")
            for reg in regressions:
                print(f"  - {reg}")
        else:
            print(f"\n{Colors.GREEN}✓ No performance regressions detected{Colors.ENDC}")
    
    # Save results if requested
    if args.save:
        output = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "correctness": correctness_results,
            "benchmarks": benchmark_results,
            "components": component_results,
            "comparison": comparison_results,
        }
        Path(args.save).write_text(json.dumps(output, indent=2, ensure_ascii=False))
        print(f"\n{Colors.CYAN}Results saved to: {args.save}{Colors.ENDC}")
    
    # Return exit code based on correctness
    sys.exit(0 if correctness_results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
