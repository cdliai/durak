# Durak

[![PyPI](https://img.shields.io/pypi/v/durak-nlp.svg)](https://pypi.org/project/durak-nlp/)
[![Python Versions](https://img.shields.io/pypi/pyversions/durak-nlp.svg)](https://pypi.org/project/durak-nlp/)
[![Tests](https://github.com/fbkaragoz/durak/actions/workflows/tests.yml/badge.svg)](https://github.com/fbkaragoz/durak/actions/workflows/tests.yml)
[![License](https://img.shields.io/badge/license-Durak%201.2-blue.svg)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.17477942.svg)](https://doi.org/10.5281/zenodo.17477942)

<p align="center">
  <img src="https://raw.githubusercontent.com/fbkaragoz/durak/main/docs/durak.svg" alt="Durak logo" width="200" />
</p>

**Durak** is a high-performance Turkish NLP toolkit built on a **"Rust Core, Python Interface"** architecture. Heavy lifting (normalization, tokenization, lemmatization) runs in compiled Rust, releasing the GIL for true parallelism, while providing a flexible, PyTorch-like API for Python researchers.

## Why Durak?

- **Rust-Powered**: Blazing fast text processing with zero-overhead resource embedding
- **True Parallelism**: GIL-released operations for multi-core batch processing
- **Zero-Dependency Distribution**: Resources compiled directly into binary
- **Research-Ready**: Type-safe, reproducible, easy to integrate

## Architecture

```
┌──────────────────────────────────────┐
│   Python Interface (python/durak/)   │  ← Your code here
│   Pipeline • StopwordManager • API   │
├──────────────────────────────────────┤
│   Rust Core (src/lib.rs)             │  ← Performance critical
│   Tokenization • Normalization       │
│   Embedded Resources (include_str!)  │
└──────────────────────────────────────┘
```

See [ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed design documentation.

## Quickstart

### Installation

```bash
pip install durak-nlp
```

### Minimal Pipeline

```python
from durak import process_text

entries = [
    "Türkiye'de NLP zor. Durak kolaylaştırır.",
    "Ankara ' da kaldım.",
]

tokens = [
    process_text(
        entry,
        remove_stopwords=True,
        rejoin_suffixes=True,  # glue detached suffixes before filtering
    )
    for entry in entries
]

print(tokens[0])
# ["türkiye'de", "nlp", "zor", ".", "durak", "kolaylaştırır", "."]

print(tokens[1])
# ["ankara'da", "kaldım", "."]
```

The pipeline executes: **clean → tokenize → rejoin detached suffixes → remove stopwords**

### Build Blocks à la Carte

```python
from durak import (
    StopwordManager,
    attach_detached_suffixes,
    clean_text,
    remove_stopwords,
    tokenize,
)

text = "İstanbul ' a vapurla geçtik."
cleaned = clean_text(text)
tokens = tokenize(cleaned)
tokens = attach_detached_suffixes(tokens)

# Custom stopword management
manager = StopwordManager(additions=["vapurla"], keep=["istanbul'a"])
filtered = remove_stopwords(tokens, manager=manager)

print(filtered)
# ["istanbul'a", "geçtik", "."]
```

### Accessing the Rust Core

```python
from durak import _durak_core

# High-performance functions (5-10x faster than Python)
normalized = _durak_core.fast_normalize("İSTANBUL")  # "istanbul"
tokens = _durak_core.tokenize_with_offsets("Merhaba dünya!")

# NER-ready tokenization with offset mapping (Issue #7)
text = "Ahmet İstanbul'a gitti."
tokens = _durak_core.tokenize_normalized(text)
for token in tokens:
    original = text[token.start:token.end]
    print(f"{token.text:15} → {original:15} [{token.start}:{token.end}]")
# Output:
# ahmet           → Ahmet           [0:5]
# istanbul'a      → İstanbul'a      [6:16]
# gitti           → gitti           [17:22]
# .               → .               [22:23]

# Embedded resources (no file I/O!)
stopwords = _durak_core.get_stopwords_base()  # 100-1000x faster loading
suffixes = _durak_core.get_detached_suffixes()
```

## Features

- **Unicode-aware cleaning**: Turkish-specific normalization (İ/ı, I/i handling)
- **Configurable stopword management**: Keep-lists, custom additions, domain-specific sets
- **Regex-based tokenizer**: Preserves Turkish morphology (clitics, suffixes, apostrophes)
- **Offset tracking**: Character-accurate positions for NER and span tasks
- **Embedded resources**: Zero file I/O, compiled directly into binary
- **Type-safe**: Complete `.pyi` stubs for IDE support and static analysis

## Development Setup

### Building from Source

```bash
# Clone the repository
git clone https://github.com/fbkaragoz/durak.git
cd durak

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build and install with Rust extension
pip install maturin
maturin develop  # or: maturin develop --release for optimized build

# Install dev dependencies
pip install -e .[dev]
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=durak --cov-report=html

# Type checking
mypy python

# Linting
ruff check .
```

### Project Structure

```
durak/
├── src/                  # Rust source (engine)
│   └── lib.rs
├── python/               # Python source (interface)
│   └── durak/
├── resources/            # Static data files
│   └── tr/               # Turkish resources
├── tests/                # Integration tests
├── benchmarks/           # Performance benchmarks
├── examples/             # Usage examples
└── docs/                 # Documentation
```

## Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)**: Design principles and component architecture
- **[Examples](examples/)**: Basic and advanced usage demonstrations
- **[Benchmarks](benchmarks/)**: Performance comparison and optimization tips
- **[API Design Docs](docs/design/)**: Detailed component specifications
- **[Changelog](CHANGELOG.md)**: Version history and migration guides
- **[Roadmap](docs/ROADMAP.md)**: Future enhancements and planned features

## Community & Support

- **Code of Conduct**: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
- **Contributing**: [CONTRIBUTING.md](CONTRIBUTING.md)
- **Security**: [SECURITY.md](SECURITY.md)
- **Citation**: [CITATION.cff](CITATION.cff)
- **Issues**: [GitHub Issues](https://github.com/fbkaragoz/durak/issues)

**Topics**: `turkish-nlp`, `nlp`, `rust`, `pyo3`, `maturin`, `tokenization`, `lemmatization`, `text-processing`

## Performance

Rust-accelerated functions provide significant speedups:

- **Normalization**: 5-10x faster than pure Python
- **Tokenization**: 3-5x faster with offset tracking
- **Resource Loading**: 100-1000x faster (embedded, no file I/O)
- **Full Pipeline**: 2-4x overall speedup

Run `python benchmarks/benchmark_rust_vs_python.py` to measure on your system.

## License

Durak is distributed under the [Durak License v1.2](LICENSE). Commercial or institutional use requires explicit written permission from the author.

---

**Homepage**: [karagoz.io](https://karagoz.io)
**Repository**: [github.com/fbkaragoz/durak](https://github.com/fbkaragoz/durak)
