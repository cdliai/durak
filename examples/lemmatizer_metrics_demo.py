#!/usr/bin/env python3
"""
Lemmatizer Performance Metrics Demo

Demonstrates how to use the metrics collection feature to compare
lemmatization strategies and monitor performance.

Issue #63: Add Strategy Performance Metrics to Lemmatizer
"""

from durak.lemmatizer import Lemmatizer


def demo_basic_metrics():
    """Basic metrics collection example"""
    print("=" * 60)
    print("BASIC METRICS COLLECTION")
    print("=" * 60)
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    # Process some sample words
    test_words = [
        "kitaplar", "evler", "geliyorum", "gidiyorum",
        "unknownword123", "testleri", "arabalar",
    ]
    
    results = {}
    for word in test_words:
        lemma = lemmatizer(word)
        results[word] = lemma
    
    # Display results
    print("\nLemmatization Results:")
    for word, lemma in results.items():
        status = "📖" if lemma != word else "🔧"
        print(f"  {status} {word:<20} → {lemma}")
    
    # Show metrics
    print(f"\n{lemmatizer.get_metrics()}")


def demo_strategy_comparison():
    """Compare all three strategies side-by-side"""
    print("\n" + "=" * 60)
    print("STRATEGY COMPARISON")
    print("=" * 60)
    
    # Test corpus
    corpus = [
        # Words likely in dictionary
        "kitaplar", "evler", "geliyorum", "gittim",
        # Words likely NOT in dictionary
        "unknownword", "testleri", "deneysel",
        # Common words
        "insanlar", "çocuklar", "yapıyorum",
    ]
    
    strategies = ["lookup", "heuristic", "hybrid"]
    
    for strategy in strategies:
        lemmatizer = Lemmatizer(strategy=strategy, collect_metrics=True)
        
        for word in corpus:
            _ = lemmatizer(word)
        
        metrics = lemmatizer.get_metrics()
        
        print(f"\n{'─' * 60}")
        print(f"Strategy: {strategy.upper()}")
        print(f"{'─' * 60}")
        print(f"  Total Calls:         {metrics.total_calls:,}")
        print(f"  Lookup Hits:         {metrics.lookup_hits:,}")
        print(f"  Heuristic Calls:     {metrics.heuristic_calls:,}")
        print(f"  Cache Hit Rate:      {metrics.cache_hit_rate:.1%}")
        print(f"  Avg Call Time:       {metrics.avg_call_time_ms:.3f}ms")


def demo_large_corpus():
    """Benchmark with larger corpus"""
    print("\n" + "=" * 60)
    print("LARGE CORPUS BENCHMARK")
    print("=" * 60)
    
    # Simulate larger corpus (repeated words)
    base_words = [
        "kitaplar", "evler", "insanlar", "çocuklar",
        "geliyorum", "gidiyorum", "yapıyorum",
        "arabalar", "masalar", "testleri",
    ]
    
    # Repeat to create ~1000 calls
    corpus = base_words * 100
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    for word in corpus:
        _ = lemmatizer(word)
    
    metrics = lemmatizer.get_metrics()
    
    print(f"\nProcessed {metrics.total_calls:,} words")
    hit_pct = metrics.cache_hit_rate
    print(f"Lookup Hits:         {metrics.lookup_hits:,} ({hit_pct:.1%})")
    print(f"Heuristic Fallbacks: {metrics.heuristic_calls:,}")
    print(f"Total Time:          {metrics.total_time:.3f}s")
    print(f"Avg Call Time:       {metrics.avg_call_time_ms:.4f}ms")
    throughput = metrics.total_calls / metrics.total_time
    print(f"Throughput:          {throughput:,.0f} words/sec")


def demo_incremental_monitoring():
    """Monitor metrics over time with resets"""
    print("\n" + "=" * 60)
    print("INCREMENTAL MONITORING")
    print("=" * 60)
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    batches = [
        ["kitaplar", "evler", "geliyorum"],
        ["arabalar", "masalar", "testleri"],
        ["unknownword1", "unknownword2", "unknownword3"],
    ]
    
    for i, batch in enumerate(batches, 1):
        lemmatizer.reset_metrics()
        
        for word in batch:
            _ = lemmatizer(word)
        
        metrics = lemmatizer.get_metrics()
        
        print(f"\nBatch {i}:")
        print(f"  Words:        {metrics.total_calls}")
        print(f"  Lookup Hits:  {metrics.lookup_hits} ({metrics.cache_hit_rate:.0%})")
        print(f"  Heuristic:    {metrics.heuristic_calls}")


def main():
    """Run all demos"""
    print("\n🔬 Lemmatizer Performance Metrics Demo")
    print("Issue #63: Strategy Performance Metrics\n")
    
    try:
        demo_basic_metrics()
        demo_strategy_comparison()
        demo_large_corpus()
        demo_incremental_monitoring()
        
        print("\n" + "=" * 60)
        print("✅ All demos completed successfully!")
        print("=" * 60)
        
    except ImportError as e:
        print(f"\n❌ Error: {e}")
        print("Make sure durak is installed: pip install -e .")


if __name__ == "__main__":
    main()
