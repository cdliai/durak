# Technical Reference

## Architecture

Durak uses a layered architecture:

```
┌─────────────────────────────────────┐
│ Python Interface (python/durak/)    │
│ - TextProcessor                     │
│ - Pipeline                          │
│ - Stats module                      │
├─────────────────────────────────────┤
│ Rust Core (src/lib.rs)              │
│ - fast_normalize()                  │
│ - tokenize_with_offsets()           │
│ - lookup_lemma()                    │
└─────────────────────────────────────┘
```

Python layer provides high-level APIs. Rust layer provides performance-critical operations. Both layers operate independently.

## Module Specifications

### TextProcessor (processor.py)

**Purpose:** High-level pipeline orchestration.

**Configuration (ProcessorConfig):**
- `lowercase: bool` - Convert to lowercase (default: True)
- `remove_stopwords: bool` - Filter stopwords (default: False)
- `lemmatize: bool` - Apply lemmatization (default: False)
- `attach_suffixes: bool` - Reattach detached suffixes (default: False)
- `remove_punctuation: bool` - Remove punctuation tokens (default: False)
- `emoji_mode: str` - One of "keep", "remove", "extract" (default: "keep")

**Processing Pipeline:**
1. clean_text() - Normalize, strip HTML, handle emojis
2. tokenize() - Regex-based tokenization
3. attach_detached_suffixes() - If configured
4. Lemmatizer() - If configured
5. remove_stopwords() - If configured

**Output (ProcessingResult):**
- `tokens: list[str]` - Processed tokens
- `lemmas: list[str] | None` - Lemmas if lemmatization enabled
- `emojis: list[str] | None` - Extracted emojis if mode="extract"
- `metadata: dict` - Token count and flags

### Stats Module (stats/)

**FrequencyCounter:**
- Counts unigrams, bigrams, or trigrams
- Supports stopword filtering
- Supports minimum length thresholds
- Exports to TSV format

**ngrams():**
- Generates n-grams from token sequence
- Optional left/right padding
- Returns list of tuples

## Performance Characteristics

Measured on 12 Turkish test documents (2,242 characters total):

| Configuration | Avg Time | Throughput |
|--------------|----------|------------|
| Basic (clean + tokenize) | 0.044 ms | 751,738 tok/s |
| +Stopwords | 0.053 ms | 539,658 tok/s |
| +Suffixes | 0.055 ms | 584,417 tok/s |
| Full pipeline | 0.068 ms | 284,322 tok/s |

**Component Breakdown:**
- normalize_case: 0.0001 ms (fastest)
- tokenize: 0.0040 ms
- attach_suffixes: 0.0013 ms
- clean_text: 0.036-0.043 ms (slowest)
- remove_stopwords: 0.0192 ms

## Rust Extension Integration

**Lazy Loading Pattern:**
```python
def _get_rust_function(name: str):
    from durak import _durak_core
    if _durak_core is None:
        return fallback_function
    return getattr(_durak_core, name)
```

This pattern allows Python-only development without building Rust extension.

**Functions with Rust Acceleration:**
- `fast_normalize()` - Turkish I/ı handling
- `tokenize_with_offsets()` - Tokenization with character positions
- `lookup_lemma()` - Dictionary-based lemmatization
- `strip_suffixes()` - Heuristic suffix stripping

**Expected Speedup (when Rust available):**
- Normalization: 5-10x
- Tokenization: 3-5x
- Resource loading: 100-1000x (embedded vs file)
- Full pipeline: 2-4x

## Error Handling

**Exception Hierarchy:**
```
DurakError
├── ConfigurationError
├── ResourceError
├── RustExtensionError
├── LemmatizerError
├── NormalizerError
├── PipelineError
├── TokenizationError
└── StopwordError
```

All exceptions inherit from `DurakError` for single-clause catching.

## Resource Loading Strategy

**Dual-mode loading:**

1. **Embedded (Production)**
   - Resources compiled into Rust binary via `include_str!`
   - Zero file I/O, immediate loading
   - Accessed via `_durak_core.get_*()` functions

2. **File-based (Development)**
   - Resources loaded from `resources/tr/` directory
   - ~1-10ms file I/O overhead
   - Allows dynamic modification

## Testing Structure

**Test Categories:**

1. **Unit Tests** (`tests/`)
   - Module-level functionality
   - Fast execution (<1s total)
   - 99 tests passing

2. **Integration Tests** (`test_data/`)
   - End-to-end pipeline testing
   - 12 Turkish document categories
   - 48 test cases (4 configurations x 12 documents)

3. **Property Tests** (`tests/test_properties.py`)
   - Hypothesis-based random testing
   - Currently requires Rust extension

4. **Benchmarks** (`test_data/run_comprehensive_benchmark.py`)
   - Performance measurement
   - Regression detection
   - Saves results to JSON

## Type Safety

All public APIs have complete type annotations. Type stubs provided for Rust extension (`_durak_core.pyi`).

Run type checking:
```bash
mypy python/durak
```

## Dependencies

**Runtime:**
- Python >= 3.9
- click >= 8.0.0 (CLI only)

**Development:**
- maturin (Rust building)
- pytest, hypothesis (testing)
- mypy (type checking)
- ruff, black (linting/formatting)

**Optional (for full functionality):**
- Rust toolchain (for building extension)

## Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Python package configuration, tool settings |
| `Cargo.toml` | Rust package configuration |
| `resources/metadata.json` | Embedded resource metadata |
| `resources/tr/stopwords/metadata.json` | Stopword resource definitions |

## API Stability

Public API follows semantic versioning:
- Patch (0.4.x): Bug fixes only
- Minor (0.x.0): New features, backward compatible
- Major (x.0.0): Breaking changes

Current version: 0.4.0-dev
