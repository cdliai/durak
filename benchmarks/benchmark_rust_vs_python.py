"""Benchmark comparing Rust vs Python implementations.

Measures performance differences between pure Python implementations
and Rust-accelerated functions.
"""

import time


def benchmark(func, *args, iterations=10000):
    """Run a benchmark and return average execution time."""
    start = time.perf_counter()
    for _ in range(iterations):
        func(*args)
    end = time.perf_counter()
    return (end - start) / iterations * 1000  # Return ms per call


def main():
    import durak

    print("=" * 70)
    print("Rust vs Python Performance Benchmark")
    print("=" * 70)

    # Test text
    test_text = "İstanbul'da Merhaba Dünya! Bu bir TEST cümlesidir."
    large_text = test_text * 100

    # 1. Normalization Benchmark
    print("\n1. Text Normalization")
    print("-" * 70)

    # Python version
    def python_normalize(text):
        return durak.normalize_case(text)

    # Rust version
    try:
        from durak import _durak_core

        def rust_normalize(text):
            return _durak_core.fast_normalize(text)

        py_time = benchmark(python_normalize, test_text)
        rust_time = benchmark(rust_normalize, test_text)

        print(f"Python normalize: {py_time:.4f} ms per call")
        print(f"Rust normalize:   {rust_time:.4f} ms per call")
        print(f"Speedup:          {py_time / rust_time:.2f}x")

    except ImportError:
        print("Rust extension not available. Run: maturin develop")

    # 2. Tokenization Benchmark
    print("\n2. Tokenization with Offsets")
    print("-" * 70)

    # Python version
    def python_tokenize(text):
        return durak.tokenize_with_offsets(text)

    # Rust version
    try:
        from durak import _durak_core

        def rust_tokenize(text):
            return _durak_core.tokenize_with_offsets(text)

        py_time = benchmark(python_tokenize, large_text, iterations=1000)
        rust_time = benchmark(rust_tokenize, large_text, iterations=1000)

        print(f"Python tokenize: {py_time:.4f} ms per call")
        print(f"Rust tokenize:   {rust_time:.4f} ms per call")
        print(f"Speedup:         {py_time / rust_time:.2f}x")

    except ImportError:
        print("Rust extension not available")

    # 3. Resource Loading Benchmark
    print("\n3. Resource Loading")
    print("-" * 70)

    try:
        from durak import _durak_core

        # File-based loading
        def load_from_file():
            return durak.load_stopword_resource("base/turkish")

        # Embedded Rust loading
        def load_from_rust():
            return _durak_core.get_stopwords_base()

        file_time = benchmark(load_from_file, iterations=100)
        rust_time = benchmark(load_from_rust, iterations=100)

        print(f"File-based load:   {file_time:.4f} ms per call")
        print(f"Embedded Rust load: {rust_time:.4f} ms per call")
        print(f"Speedup:            {file_time / rust_time:.2f}x")

    except ImportError:
        print("Rust extension not available")

    # 4. Lemmatizer Cache Benchmark
    print("\n4. Lemmatizer LRU Cache Performance")
    print("-" * 70)

    # Generate corpus with Zipfian distribution (realistic word frequency)
    # Top 100 words cover ~50% of tokens in typical Turkish text
    common_words = [
        "kitap", "ev", "araba", "okul", "öğrenci", "öğretmen", "ders",
        "sınıf", "masa", "sandalye", "kapı", "pencere", "bahçe", "ağaç",
        "çocuk", "anne", "baba", "kardeş", "arkadaş", "komşu"
    ] * 50  # 1000 tokens, highly repetitive

    rare_words = [
        f"nadir_kelime_{i}" for i in range(1000)
    ]  # 1000 unique tokens

    # Test 1: Cache-friendly workload (repetitive)
    lemmatizer_cached = durak.Lemmatizer(cache_size=10_000)
    lemmatizer_nocache = durak.Lemmatizer(cache_size=0)

    def lemmatize_corpus(lemmatizer, words):
        for word in words:
            lemmatizer(word)

    cached_time = benchmark(lemmatize_corpus, lemmatizer_cached, common_words, iterations=10)
    nocache_time = benchmark(lemmatize_corpus, lemmatizer_nocache, common_words, iterations=10)

    cache_info = lemmatizer_cached.get_cache_info()
    hit_rate = cache_info.hits / (cache_info.hits + cache_info.misses) if cache_info else 0

    print(f"Repetitive corpus (1000 tokens, 20 unique words):")
    print(f"  With cache:    {cached_time:.4f} ms per call")
    print(f"  Without cache: {nocache_time:.4f} ms per call")
    print(f"  Speedup:       {nocache_time / cached_time:.2f}x")
    print(f"  Cache hit rate: {hit_rate:.1%}")

    # Test 2: Cache-hostile workload (all unique)
    lemmatizer_cached.clear_cache()
    cached_time_unique = benchmark(lemmatize_corpus, lemmatizer_cached, rare_words, iterations=10)
    nocache_time_unique = benchmark(lemmatize_corpus, lemmatizer_nocache, rare_words, iterations=10)

    cache_info_unique = lemmatizer_cached.get_cache_info()
    hit_rate_unique = cache_info_unique.hits / (cache_info_unique.hits + cache_info_unique.misses) if cache_info_unique else 0

    print(f"\nUnique corpus (1000 unique words, no repetition):")
    print(f"  With cache:    {cached_time_unique:.4f} ms per call")
    print(f"  Without cache: {nocache_time_unique:.4f} ms per call")
    print(f"  Overhead:      {cached_time_unique / nocache_time_unique:.2f}x")
    print(f"  Cache hit rate: {hit_rate_unique:.1%}")

    # 5. Full Pipeline Benchmark
    print("\n5. Complete Processing Pipeline")
    print("-" * 70)

    pipeline = durak.Pipeline(
        ["clean", "tokenize", "remove_stopwords", "normalize"]
    )

    pipeline_time = benchmark(pipeline, large_text, iterations=100)
    print(f"Full pipeline: {pipeline_time:.4f} ms per call")

    print("\n" + "=" * 70)
    print("Benchmark complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
