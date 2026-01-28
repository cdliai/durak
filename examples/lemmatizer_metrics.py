"""
Lemmatizer Strategy Performance Comparison

Demonstrates how to use metrics to compare lemmatization strategies
on different corpus types and make data-driven decisions.
"""

from durak import Lemmatizer


def compare_strategies(corpus: list[str], corpus_name: str) -> None:
    """Compare all three lemmatization strategies on a corpus."""
    
    print(f"\n{'='*60}")
    print(f"Corpus: {corpus_name} ({len(corpus)} words)")
    print(f"{'='*60}\n")
    
    strategies = ["lookup", "heuristic", "hybrid"]
    
    for strategy in strategies:
        lemmatizer = Lemmatizer(strategy=strategy, collect_metrics=True)
        
        # Process corpus
        [lemmatizer(word) for word in corpus]
        
        # Get metrics
        metrics = lemmatizer.get_metrics()
        
        print(f"Strategy: {strategy.upper()}")
        print(metrics)
        print()


def main():
    # Test Corpus 1: Common words (high dictionary coverage)
    common_words = [
        "kitaplar", "evler", "geliyorum", "gittim", "yapıyoruz",
        "okuyorum", "yazdım", "içiyoruz", "yedik", "uyudum",
        "koşuyorum", "düşünüyorum", "anladım", "baktım", "dinledim",
    ] * 100  # 1500 total
    
    compare_strategies(common_words, "Common Words (High Dictionary Coverage)")
    
    # Test Corpus 2: Technical terms (lower dictionary coverage)
    technical_words = [
        "tokenizasyonlar", "normalizasyonları", "lemmatizasyon",
        "vektörizasyon", "klasterlemeler", "sınıflandırmalar",
        "regresyonlar", "transformatörler", "enkoderleri",
        "dekoderleri", "embedingleri", "finetuninglar",
    ] * 100  # 1200 total
    
    compare_strategies(technical_words, "Technical Terms (Low Dictionary Coverage)")
    
    # Test Corpus 3: Mixed (realistic workload)
    mixed_corpus = [
        # Common
        "kitaplar", "evler", "geliyorum", "gittim",
        # Technical
        "tokenizasyonlar", "normalizasyonları",
        # Proper nouns
        "Ankara'da", "İstanbul'dan", "Türkiye'de",
        # Inflected forms
        "yapabiliyormuşuz", "gelebilecekmiş", "konuşabiliyordu",
    ] * 100  # 1300 total
    
    compare_strategies(mixed_corpus, "Mixed Corpus (Realistic Workload)")
    
    # Demonstrate metrics export for analysis
    print("\n" + "="*60)
    print("Exporting Metrics for Analysis")
    print("="*60 + "\n")
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    for word in common_words[:100]:
        lemmatizer(word)
    
    metrics_dict = lemmatizer.get_metrics().to_dict()
    
    print("Metrics as dictionary (ready for pandas, logging, etc.):")
    print(metrics_dict)
    
    # Show reset functionality
    print("\nBefore reset:")
    print(f"Total calls: {lemmatizer.get_metrics().total_calls}")
    
    lemmatizer.reset_metrics()
    
    print("After reset:")
    print(f"Total calls: {lemmatizer.get_metrics().total_calls}")


if __name__ == "__main__":
    main()
