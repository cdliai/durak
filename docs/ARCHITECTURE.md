# Architecture Documentation

## Project Structure

Durak follows the **industry-standard mixed Python/Rust extension layout** for high-performance NLP applications:

```
durak-nlp/
├── src/                                      # RUST SOURCE ONLY
│   └── lib.rs                                # Rust core: tokenization, normalization, resource embedding
├── python/                                   # PYTHON SOURCE ONLY
│   └── durak/
│       ├── __init__.py                       # Public API
│       ├── _durak_core.pyi                   # Type stubs for Rust extension
│       ├── cleaning.py                       # Text cleaning utilities
│       ├── lemmatizer.py                     # Lemmatization logic
│       ├── normalizer.py                     # Text normalization
│       ├── pipeline.py                       # Processing pipelines
│       ├── stopwords.py                      # Stopword management
│       ├── suffixes.py                       # Turkish suffix handling
│       └── tokenizer.py                      # Tokenization (wraps Rust)
├── resources/                                # STATIC DATA FILES
│   └── tr/                                   # Turkish resources
│       ├── labels/                           # Linguistic labels
│       │   └── DETACHED_SUFFIXES.txt
│       └── stopwords/                        # Stopword lists
│           ├── base/turkish.txt
│           ├── domains/social_media.txt
│           └── metadata.json
├── tests/                                    # Integration tests
├── benchmarks/                               # Performance benchmarks
├── examples/                                 # Usage examples
├── scripts/                                  # Utility scripts
├── Cargo.toml                                # Rust dependencies
└── pyproject.toml                            # Python & build config
```

## Design Principles

### 1. Separation of Concerns

**Engine (Rust) - `src/`**
- High-performance core operations
- Zero-overhead resource embedding via `include_str!`
- Memory-safe string processing
- Compiled extension module: `_durak_core`

**Interface (Python) - `python/`**
- User-facing API
- High-level abstractions (Pipeline, StopwordManager)
- Pythonic interfaces
- Type hints and documentation

**Resources - `resources/`**
- Language-specific data files
- Compiled into Rust binary at build time
- Fallback file loading available
- Organized by language code (`tr/`)

### 2. Build System

**Maturin** handles the mixed Python/Rust build:

```toml
[tool.maturin]
python-source = "python"
module-name = "durak._durak_core"
```

Benefits:
- Automatic Python package discovery
- Cross-platform wheel building
- No manual `setup.py` required
- Handles both `pip install` and `maturin develop`

### 3. Resource Strategy

**Dual-mode loading** for maximum flexibility:

1. **Embedded (Production)**
   ```python
   from durak import _durak_core
   stopwords = _durak_core.get_stopwords_base()  # No file I/O!
   ```

2. **File-based (Development)**
   ```python
   import durak
   stopwords = durak.load_stopword_resource("base/turkish")
   ```

**Why both?**
- Embedded: Zero latency, single-file deployment
- File-based: Easy customization, debugging, testing

## Component Architecture

### Rust Core (`src/lib.rs`)

```
┌─────────────────────────────────────┐
│      _durak_core (Rust)             │
├─────────────────────────────────────┤
│ Embedded Resources (include_str!)  │
│  • DETACHED_SUFFIXES_DATA           │
│  • STOPWORDS_TR_DATA                │
│  • STOPWORDS_METADATA_DATA          │
├─────────────────────────────────────┤
│ Core Functions                      │
│  • fast_normalize(text) -> str      │
│  • tokenize_with_offsets(text)      │
│  • lookup_lemma(word)               │
│  • strip_suffixes(word)             │
├─────────────────────────────────────┤
│ Resource Accessors                  │
│  • get_stopwords_base()             │
│  • get_detached_suffixes()          │
│  • get_stopwords_metadata()         │
└─────────────────────────────────────┘
```

### Python Interface (`python/durak/`)

```
┌─────────────────────────────────────┐
│      durak (Python Package)         │
├─────────────────────────────────────┤
│ High-Level API                      │
│  • Pipeline                         │
│  • StopwordManager                  │
│  • Lemmatizer                       │
│  • Normalizer                       │
├─────────────────────────────────────┤
│ Convenience Functions               │
│  • clean_text()                     │
│  • tokenize()                       │
│  • remove_stopwords()               │
│  • attach_detached_suffixes()       │
├─────────────────────────────────────┤
│ Rust Extension Import               │
│  • from . import _durak_core        │
│  • Graceful fallback if unavailable │
└─────────────────────────────────────┘
```

## Type Safety

**Comprehensive type stubs** (`_durak_core.pyi`) enable:
- IDE autocomplete for Rust functions
- Static type checking with mypy
- Runtime type validation
- Better documentation

Example:
```python
from durak import _durak_core

# IDE knows the signature and return type!
tokens: list[tuple[str, int, int]] = _durak_core.tokenize_with_offsets(text)
```

## Performance Model

### Hot Path: Rust Functions

```
User Text Input
     ↓
fast_normalize()        ← Rust (5-10x faster)
     ↓
tokenize_with_offsets() ← Rust (3-5x faster)
     ↓
Python Processing       ← Python (stopwords, pipelines)
     ↓
Result
```

### Resource Loading

**Embedded (Rust)**
```
Application Start
     ↓
get_stopwords_base()  ← Immediate (data in binary)
     ↓
Set/List in memory
```

**File-based (Python)**
```
Application Start
     ↓
load_stopword_resource() ← File I/O (~1-10ms)
     ↓
Parse lines
     ↓
Set/List in memory
```

## Extensibility

### Adding New Resources

1. **Add file to `resources/tr/`**
   ```
   resources/tr/new_category/data.txt
   ```

2. **Embed in Rust** (optional, for performance)
   ```rust
   static NEW_DATA: &str = include_str!("../resources/tr/new_category/data.txt");
   ```

3. **Add accessor function**
   ```rust
   #[pyfunction]
   fn get_new_data() -> Vec<String> { ... }
   ```

4. **Update type stubs**
   ```python
   def get_new_data() -> list[str]: ...
   ```

### Adding New Rust Functions

1. Implement in `src/lib.rs`:
   ```rust
   #[pyfunction]
   fn new_function(arg: &str) -> String { ... }
   ```

2. Export in module:
   ```rust
   m.add_function(wrap_pyfunction!(new_function, m)?)?;
   ```

3. Add type stub:
   ```python
   def new_function(arg: str) -> str: ...
   ```

4. Document and test

## Testing Strategy

### Unit Tests
- Python tests in `tests/`
- Run with: `pytest tests/`

### Integration Tests
- Test Python ↔ Rust boundary
- Verify resource loading
- Check pipeline composition

### Benchmarks
- Compare Rust vs Python performance
- Track regression
- Optimize hot paths

## Build & Development

### Development Build
```bash
maturin develop          # Build and install locally
pytest tests/            # Run tests
python examples/basic_usage.py
```

### Production Build
```bash
maturin build --release  # Optimized wheel
pip install dist/*.whl
```

### Release Process
```bash
maturin publish          # Upload to PyPI
```

## Migration Notes

### From Previous Structure

**Before:**
```
src/
├── durak/           # Python + data mixed
│   ├── data/        # Resources inside package
│   └── *.py
└── lib.rs           # Rust
```

**After:**
```
src/lib.rs           # Rust only
python/durak/        # Python only
resources/tr/        # Resources separate
```

**Breaking Changes:**
- Resources moved from `src/durak/data/` to `resources/tr/`
- Python import still `import durak` (no change to API)
- Maturin handles packaging (no MANIFEST.in needed)

## Future Enhancements

- [ ] Add more Rust-accelerated functions (lemmatization)
- [ ] Support additional languages (resources/en/, resources/ar/)
- [ ] Parallel processing for batch operations
- [ ] WASM compilation for browser usage
- [ ] Plugin system for custom processors
