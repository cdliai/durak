# Benchmarks

Performance benchmarks for the Durak NLP toolkit.

## Running Benchmarks

### Rust vs Python Performance

Compare Rust-accelerated functions against pure Python implementations:

```bash
python benchmarks/benchmark_rust_vs_python.py
```

### Dataset Quality + Throughput Benchmark

Run a real corpus benchmark on Hugging Face datasets:

```bash
python benchmarks/benchmark_dataset_quality.py \
  --dataset fatihburakkaragoz/old-nogay-turkish-ocr-corpus \
  --splits train validation test
```

Optional flags:

```bash
python benchmarks/benchmark_dataset_quality.py \
  --dataset <hf_dataset_id> \
  --text-column <column_name> \
  --max-rows-per-split <n>
```

This script checks:
- Character-offset mapping correctness for normalized token offsets
- Token shape parity (Python regex baseline vs Rust implementation)
- Throughput and error ratio per split

This benchmark measures:
- Text normalization (Turkish character handling)
- Tokenization with offsets
- Resource loading (embedded vs file-based)
- Full pipeline processing

## Expected Results

With Rust extension enabled:
- **Normalization**: 5-10x speedup
- **Tokenization**: 3-5x speedup
- **Resource Loading**: 100-1000x speedup (no file I/O)
- **Full Pipeline**: 2-4x speedup overall

## Writing Custom Benchmarks

Template for new benchmarks:

```python
import time
import durak

def benchmark(func, *args, iterations=10000):
    """Run a benchmark and return average execution time."""
    start = time.perf_counter()
    for _ in range(iterations):
        func(*args)
    end = time.perf_counter()
    return (end - start) / iterations * 1000

# Your benchmark code here
result_ms = benchmark(my_function, test_data)
print(f"Average: {result_ms:.4f} ms per call")
```

## Performance Tips

1. **Use Rust functions directly** for hot paths:
   ```python
   from durak import _durak_core
   normalized = _durak_core.fast_normalize(text)
   ```

2. **Batch processing** for large datasets:
   ```python
   tokens = [_durak_core.tokenize_with_offsets(t) for t in texts]
   ```

3. **Embedded resources** avoid file I/O:
   ```python
   stopwords = set(_durak_core.get_stopwords_base())
   ```

4. **Pre-compile pipelines** outside loops:
   ```python
   pipeline = durak.Pipeline(...)
   results = [pipeline(text) for text in texts]
   ```
