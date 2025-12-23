# Best Practices Guide

This guide provides recommendations for using and extending Durak effectively.

## 🎯 General Principles

### 1. Resource Management

**✅ DO**: Use embedded Rust resources for production

```python
from durak import _durak_core

# Fast, no file I/O
stopwords = set(_durak_core.get_stopwords_base())
suffixes = _durak_core.get_detached_suffixes()
```

**❌ DON'T**: Load from files in hot paths

```python
# Slower, file I/O overhead
from durak import load_stopword_resource
stopwords = load_stopword_resource("base/turkish")  # OK for development, not production loops
```

**When to use file-based loading:**
- Development and debugging
- Custom resource files not yet embedded
- Dynamic resource updates
- Testing with modified resources

### 2. Performance Optimization

**✅ DO**: Use Rust functions directly for performance-critical code

```python
from durak import _durak_core

# 5-10x faster
normalized = _durak_core.fast_normalize(text)
tokens = _durak_core.tokenize_with_offsets(text)
```

**✅ DO**: Batch process when possible

```python
from durak import _durak_core

# Process all texts before filtering
normalized_texts = [_durak_core.fast_normalize(t) for t in texts]
tokenized = [_durak_core.tokenize_with_offsets(t) for t in normalized_texts]
```

**❌ DON'T**: Mix Python/Rust unnecessarily in loops

```python
# Inefficient: context switching overhead
for text in texts:
    cleaned = durak.clean_text(text)  # Python
    normalized = _durak_core.fast_normalize(cleaned)  # Rust
    # Better: do all cleaning in one layer, then all normalization
```

### 3. Pipeline Design

**✅ DO**: Create reusable pipeline objects

```python
from durak import StopwordManager, Pipeline, Normalizer

# Create once, reuse many times
stopword_mgr = StopwordManager(additions=["custom"], keep=["important"])
normalizer = Normalizer()

pipeline = Pipeline([
    normalizer,
    lambda tokens: [t for t in tokens if not stopword_mgr.is_stopword(t)]
])

# Reuse efficiently
results = [pipeline(text) for text in texts]
```

**❌ DON'T**: Recreate expensive objects in loops

```python
# Bad: recreates manager every iteration
for text in texts:
    mgr = StopwordManager(additions=["custom"])  # Expensive!
    tokens = process_text(text)
    filtered = [t for t in tokens if not mgr.is_stopword(t)]
```

## 📝 Configuration Management

### Externalizing Hard-Coded Values

**✅ DO**: Use resource files for configuration

```python
# resources/tr/config/custom_apostrophes.txt
# resources/tr/config/domain_stopwords.txt

from pathlib import Path

config_dir = Path("resources/tr/config")
apostrophes = (config_dir / "custom_apostrophes.txt").read_text().strip().split("\n")
```

**Best practice for new configurations:**

1. Add resource file under `resources/tr/config/`
2. Embed in Rust if needed frequently (see next section)
3. Load once at module initialization
4. Cache in module-level variable

### Adding New Embedded Resources

**To add new resources to Rust binary:**

1. **Add file** to `resources/tr/`
2. **Embed in Rust** (`src/lib.rs`):
   ```rust
   static MY_DATA: &str = include_str!("../resources/tr/config/mydata.txt");
   ```

3. **Create accessor function**:
   ```rust
   #[pyfunction]
   fn get_my_data() -> Vec<String> {
       MY_DATA.lines().map(|s| s.trim().to_string()).collect()
   }
   ```

4. **Export in module**:
   ```rust
   m.add_function(wrap_pyfunction!(get_my_data, m)?)?;
   ```

5. **Add type stub** (`python/durak/_durak_core.pyi`):
   ```python
   def get_my_data() -> list[str]: ...
   ```

6. **Rebuild**: `maturin develop --release`

## 🔧 Extension Patterns

### Custom Stopword Management

**✅ DO**: Use domain-specific stopword files

```python
# resources/tr/stopwords/domains/medical.txt
# resources/tr/stopwords/domains/legal.txt

manager = StopwordManager.from_resources([
    "base/turkish",
    "domains/medical",  # Domain-specific
], keep=["hasta", "doktor"])  # Keep domain terms
```

**✅ DO**: Export and version stopword sets

```python
manager = StopwordManager(additions=["term1", "term2"])
manager.export("my_project_stopwords_v1.txt")

# Later, load exact same set
from durak import load_stopwords
stopwords = load_stopwords("my_project_stopwords_v1.txt")
```

### Morphological Analysis

**Current limitation**: Basic suffix stripping only

**Recommended approach for production:**

```python
# For simple cases: use built-in
from durak import _durak_core
stripped = _durak_core.strip_suffixes("kitaplardan")  # "kitap"

# For complex morphology: use external tools
# Option 1: Zemberek (Java-based, most accurate for Turkish)
# Option 2: spaCy tr_core_news_lg
# Option 3: Stanza Turkish model

# Then integrate with Durak pipeline:
import durak
from durak import Pipeline

pipeline = Pipeline([
    lambda text: durak.clean_text(text),
    lambda text: durak.tokenize(text),
    lambda tokens: your_lemmatizer.lemmatize(tokens),  # External tool
    lambda tokens: durak.remove_stopwords(tokens),
])
```

### Suffix Configuration

**Current state**: Rust suffixes are hard-coded for demo purposes

**To customize suffix stripping:**

1. **Edit** `resources/tr/config/lemma_suffixes.txt`
2. **Load in Python**:
   ```python
   from pathlib import Path

   suffix_file = Path("resources/tr/config/lemma_suffixes.txt")
   custom_suffixes = [
       line.strip()
       for line in suffix_file.read_text().splitlines()
       if line.strip() and not line.startswith("#")
   ]

   # Use with Python-based stripping
   def strip_custom(word: str, suffixes: list[str]) -> str:
       for suffix in sorted(suffixes, key=len, reverse=True):
           if word.endswith(suffix) and len(word) > len(suffix) + 2:
               return word[:-len(suffix)]
       return word

   lemma = strip_custom("kitaplardan", custom_suffixes)
   ```

3. **For production**: Implement proper morphological analysis with vowel harmony

## 🧪 Testing Best Practices

### Unit Tests

**✅ DO**: Test with realistic Turkish text

```python
def test_preserves_diacritics():
    text = "İstanbul'dan Türkiye'ye"
    tokens = durak.tokenize(text)
    assert "İstanbul'dan" in tokens  # Preserves İ
    assert "Türkiye'ye" in tokens    # Preserves ü
```

**✅ DO**: Test edge cases

```python
def test_apostrophe_variants():
    # Both straight and curly apostrophes
    assert durak.tokenize("Ankara'da") == ["Ankara", "'", "da"]
    assert durak.tokenize("Ankara'da") == ["Ankara", "'", "da"]  # Curly
```

### Performance Testing

**✅ DO**: Benchmark critical paths

```python
import time

def benchmark(func, *args, iterations=1000):
    start = time.perf_counter()
    for _ in range(iterations):
        func(*args)
    return (time.perf_counter() - start) / iterations * 1000

# Measure
py_time = benchmark(durak.normalize_case, text)
rust_time = benchmark(_durak_core.fast_normalize, text)
print(f"Speedup: {py_time / rust_time:.2f}x")
```

## 🚀 Deployment

### Production Checklist

- [ ] Use `maturin build --release` for optimized builds
- [ ] Verify embedded resources with `_durak_core.get_*()` functions
- [ ] Pre-load stopword managers at application startup
- [ ] Use Rust functions for hot paths
- [ ] Enable logging for resource loading issues
- [ ] Version-lock dependencies in production
- [ ] Test with production-like data volumes

### Distribution

**For PyPI releases:**

```bash
# Build optimized wheel
maturin build --release

# All resources are embedded in the wheel
# No need to ship separate data files
pip install durak-nlp  # Just works!
```

**For custom deployments:**

```bash
# Development mode (editable install)
maturin develop

# Production mode (optimized)
maturin develop --release
```

## 📊 Monitoring

### Resource Loading

```python
import logging

logging.basicConfig(level=logging.INFO)

# Monitor resource loading
try:
    from durak import _durak_core
    stopwords = _durak_core.get_stopwords_base()
    logging.info(f"Loaded {len(stopwords)} stopwords from embedded resources")
except ImportError:
    logging.warning("Rust extension not available, using file-based loading")
    stopwords = durak.load_stopword_resource("base/turkish")
```

### Performance Metrics

```python
import time
from functools import wraps

def log_performance(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        logging.info(f"{func.__name__}: {elapsed:.2f}ms")
        return result
    return wrapper

@log_performance
def process_corpus(texts):
    return [durak.process_text(t, remove_stopwords=True) for t in texts]
```

## 🔐 Security

### Input Validation

**✅ DO**: Validate external resources

```python
from pathlib import Path

def load_safe_stopwords(path: Path | str) -> set[str]:
    path = Path(path).resolve()

    # Ensure path is within allowed directory
    if not str(path).startswith(str(Path("resources/tr").resolve())):
        raise ValueError(f"Path outside resources directory: {path}")

    if not path.exists():
        raise FileNotFoundError(f"Resource not found: {path}")

    return durak.load_stopwords(path)
```

**✅ DO**: Sanitize user input before processing

```python
def process_user_text(text: str) -> list[str]:
    # Limit length
    if len(text) > 1_000_000:
        raise ValueError("Text too long")

    # Basic sanitization
    text = text.strip()

    # Process safely
    return durak.process_text(text, remove_stopwords=True)
```

## 📚 Further Reading

- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and component architecture
- [examples/](examples/) - Working code examples
- [benchmarks/](benchmarks/) - Performance measurement tools
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute improvements

---

**Questions or suggestions?** Open an issue at [github.com/fbkaragoz/durak/issues](https://github.com/fbkaragoz/durak/issues)
