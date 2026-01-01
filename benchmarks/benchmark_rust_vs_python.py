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

    # 4. Full Pipeline Benchmark
    print("\n4. Complete Processing Pipeline")
    print("-" * 70)

    # Use process_text instead of Pipeline for this benchmark
    # Pipeline expects callable objects, not string names
    def process_pipeline(text):
        return durak.process_text(text, remove_stopwords=True)

    pipeline_time = benchmark(process_pipeline, large_text, iterations=100)
    print(f"Full pipeline: {pipeline_time:.4f} ms per call")

    print("\n" + "=" * 70)
    print("Benchmark complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
