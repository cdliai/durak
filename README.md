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

# Embedded resources (no file I/O!)
stopwords = _durak_core.get_stopwords_base()  # 100-1000x faster loading
suffixes = _durak_core.get_detached_suffixes()
```

## Features

- **Unicode-aware cleaning**: Turkish-specific normalization (İ/ı, I/i handling)
- **Emoji sentiment mapping**: Social media NLP with emoji-to-sentiment token conversion
- **Configurable stopword management**: Keep-lists, custom additions, domain-specific sets
- **Regex-based tokenizer**: Preserves Turkish morphology (clitics, suffixes, apostrophes)
- **Offset tracking**: Character-accurate positions for NER and span tasks
- **Embedded resources**: Zero file I/O, compiled directly into binary
- **Type-safe**: Complete `.pyi` stubs for IDE support and static analysis
- **Tiered lemmatization**: Dictionary lookup + heuristic fallback with performance metrics

## Emoji Sentiment Mapping

Durak provides emoji sentiment analysis for social media NLP tasks. Replace emojis with sentiment tokens or extract structured sentiment data for training and analysis.

### Basic Usage

```python
from durak import clean_text

# Replace emojis with sentiment labels
text = "Harika! 😊🔥"
cleaned = clean_text(text, emoji_mode="sentiment")
print(cleaned)  # "harika! [HAPPY] [HOT]"

# Extract structured sentiment data
text = "Çok mutlu 😊 ama yorgun 😢"
cleaned_text, sentiments = clean_text(text, emoji_mode="sentiment_extract")
print(sentiments)
# [
#   {"polarity": "positive", "intensity": 0.7, "label": "HAPPY"},
#   {"polarity": "negative", "intensity": 0.7, "label": "SAD"}
# ]
```

### Sentiment Formats

```python
# Label format (specific emotion)
clean_text("Test 😊", emoji_mode="sentiment", sentiment_format="label")
# "test [HAPPY]"

# Polarity format (positive/negative/neutral)
clean_text("Test 😊", emoji_mode="sentiment", sentiment_format="polarity")
# "test [POSITIVE]"
```

### Unknown Emoji Handling

```python
# Preserve unknown emojis
clean_text("Test 🦄", emoji_mode="sentiment", sentiment_unknown="preserve")
# "test 🦄"

# Remove unknown emojis
clean_text("Test 🦄", emoji_mode="sentiment", sentiment_unknown="remove")
# "test"

# Replace with [NEUTRAL]
clean_text("Test 🦄", emoji_mode="sentiment", sentiment_unknown="neutral")
# "test [NEUTRAL]"
```

### Use Cases

**Sentiment Analysis**
```python
# Aggregate emoji sentiment scores
text = "Harika gün! 🌞😍 Ama biraz üzgün 😢"
_, sentiments = clean_text(text, emoji_mode="sentiment_extract")

positive = sum(s["intensity"] for s in sentiments if s["polarity"] == "positive")
negative = sum(s["intensity"] for s in sentiments if s["polarity"] == "negative")
net_sentiment = positive - negative  # +1.0 (overall positive)
```

**Training Data Augmentation**
```python
# Preserve emoji signals as tokens for model training
corpus = [
    "Harika! 😊",
    "Berbat 😡"
]
augmented = [clean_text(text, emoji_mode="sentiment") for text in corpus]
# ["harika! [HAPPY]", "berbat [ANGRY]"]
```

**Emoji Dictionary**

Durak includes a curated emoji sentiment dictionary (`resources/tr/emoji_sentiment.json`) with 110+ common emojis:
- Polarity: positive, negative, neutral
- Intensity: 0.0-1.0 (sentiment strength)
- Label: HAPPY, SAD, ANGRY, etc.

See [examples/emoji_sentiment_analysis.py](examples/emoji_sentiment_analysis.py) for detailed examples.

## Lemmatization

Durak provides a high-performance lemmatizer with three strategies:

```python
from durak import Lemmatizer

# Strategy options: "lookup", "heuristic", "hybrid"
lemmatizer = Lemmatizer(strategy="hybrid")

lemmatizer("kitaplar")    # "kitap"
lemmatizer("geliyorum")   # "gel"
lemmatizer("evlerimde")   # "ev"
```

### Strategies

- **`lookup`**: Dictionary-only (fastest, high precision, fails on OOV words)
- **`heuristic`**: Suffix stripping (handles OOV, may over-strip)
- **`hybrid`**: Try lookup first, fallback to heuristic (recommended)

### Performance Metrics

Enable metrics to analyze lemmatization behavior:

```python
lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)

for word in large_corpus:
    lemma = lemmatizer(word)

print(lemmatizer.get_metrics())
# Lemmatizer Metrics:
#   Total Calls: 10,000
#   Lookup Hits: 7,234 (72.3%)
#   Heuristic Fallbacks: 2,766
#   Avg Call Time: 0.042ms
#   Lookup Time: 0.038s
#   Heuristic Time: 0.004s
```

**Metrics include:**
- Call counts (lookup hits/misses, heuristic fallbacks)
- Timing breakdown (per-strategy latency)
- Cache hit rate
- Average call time

**Use cases:**
- Compare strategies on your corpus
- Debug lemmatization issues
- Optimize production pipelines
- Report research performance

See [examples/lemmatizer_metrics.py](examples/lemmatizer_metrics.py) for strategy comparison examples.

### Root Validation

Control heuristic quality with root validation:

```python
lemmatizer = Lemmatizer(
    strategy="hybrid",
    validate_roots=True,        # Enable validation
    strict_validation=True,     # Require roots in dictionary
    min_root_length=3,          # Minimum 3 characters
)

lemmatizer("kitaplardan")  # Only strips if root ≥3 chars and valid
```

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
