# Changelog

All notable changes to Durak will be documented here. This project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

- Added unit tests for Normalizer class covering Turkish I/ı handling and Rust fallback.
- Planned enhancements to lemmatization adapters and pipeline orchestration.

## [0.4.0] - 2025-12-23

### Major Refactoring: Industry-Standard Architecture

This release represents a complete architectural overhaul to industry-standard Python extension structure, separating Rust (Engine) from Python (Interface) with embedded resources.

#### Added

- **Embedded Resource System**: Resources compiled directly into Rust binary using `include_str!`
  - `get_stopwords_base()`: Load base Turkish stopwords (100-1000x faster, zero file I/O)
  - `get_stopwords_metadata()`: Embedded metadata JSON
  - `get_stopwords_social_media()`: Domain-specific stopwords
  - `get_detached_suffixes()`: Turkish suffix list
- **Type Stubs**: Complete `.pyi` type hints for Rust extension (`python/durak/_durak_core.pyi`)
  - Full IDE autocomplete support
  - Static type checking with mypy
  - Comprehensive docstrings with examples
- **Documentation**:
  - `ARCHITECTURE.md`: Complete architectural design documentation
  - `BEST_PRACTICES.md`: Performance optimization and extension patterns
  - `benchmarks/`: Performance comparison framework
  - `examples/`: Basic and advanced usage demonstrations
- **Configuration Resources**: Externalized hard-coded values
  - `resources/tr/config/apostrophes.txt`: Turkish apostrophe characters
  - `resources/tr/config/lemma_suffixes.txt`: Documented suffix list

#### Changed

- **Project Structure**: Migrated to industry-standard mixed Python/Rust layout
  - `src/`: Rust source only (`lib.rs`)
  - `python/`: Python source only (`durak/` package)
  - `resources/`: Static data files (embedded at compile time)
  - `benchmarks/`: Performance testing
  - `examples/`: Usage examples
  - `scripts/`: Utility scripts (moved from `src/scripts/`)
- **Build Configuration**:
  - Updated `pyproject.toml`: `python-source = "python"` (was `"src"`)
  - Updated pytest: `pythonpath = "python"` (was `"src"`)
  - Removed `MANIFEST.in` (Maturin handles packaging automatically)
  - Removed `Makefile` (replaced by maturin commands)
- **Resource Loading**: Dual-mode strategy
  - **Production**: Embedded resources (no file I/O)
  - **Development**: File-based loading from `resources/tr/`
- **Documentation**: Updated all docs for new structure
  - README.md: Added architecture diagram, Rust usage examples, performance metrics
  - docs/design/: Updated paths (`data/` → `resources/tr/`)
  - ROADMAP.md: Marked completed milestones, updated file paths

#### Performance

- **Normalization**: 5-10x faster (Rust `fast_normalize`)
- **Tokenization**: 3-5x faster with offset tracking
- **Resource Loading**: 100-1000x faster (embedded, zero I/O)
- **Full Pipeline**: 2-4x overall speedup

#### Migration Guide

**Old structure (v0.3.0)**:

```
src/
├── durak/           # Python + data mixed
│   ├── data/        # Resources inside package
│   └── *.py
└── lib.rs           # Rust
```

**New structure (v0.4.0)**:

```
src/lib.rs           # Rust only
python/durak/        # Python only
resources/tr/        # Resources (embedded)
```

**No breaking changes to public API** - all imports remain the same:

```python
import durak  # Still works!
from durak import process_text, StopwordManager  # No changes needed
```

**New features**:

```python
# Access embedded resources
from durak import _durak_core
stopwords = _durak_core.get_stopwords_base()  # Fast!
```

#### Development

- Run tests: `pytest` (no changes)
- Build with Rust: `maturin develop` or `maturin develop --release`
- Type checking: `mypy python` (was `mypy src`)

## [0.3.0] - 2025-12-23

### Added

- **Rust Core Engine ("Iron Core")**: Migrated performance-critical linguistic logic to Rust via PyO3/Maturin for significant speed improvements.
- **`Pipeline` class**: A modular, PyTorch-style component chaining system for building custom NLP pipelines.
- **`Normalizer` class**: Rust-backed Turkish text normalization with proper handling of İ/ı case transformations.
- **`Lemmatizer` class**: Multi-tier lemmatization with dictionary lookup and heuristic suffix stripping strategies.
- **`tokenize_with_offsets()`**: Character-accurate offset mapping for NER and span-based tasks.
- **Improved Tokenizer**: Rust-backed regex tokenization with configurable punctuation handling.

### Changed

- **License**: Switched to MIT license for broader compatibility.
- **Build System**: Now uses Maturin for building Rust+Python hybrid packages.
- **CI/CD**: Updated GitHub Actions workflows with proper Rust toolchain support and trusted publishing.

### Fixed

- Fixed GitHub Actions workflow using incorrect action name (`rust-action` → `rust-toolchain`).
- Fixed line-too-long linting errors in suffix handling.
- Fixed mypy type errors for optional Rust extension imports.

## [0.2.4] - 2025-10-30

### Fixed

- Synced packaged stopword data with the expanded list so reattached tokens like "var" and "bi" are filtered consistently across installs.
- Added regression coverage ensuring stopword removal runs after suffix reattachment in the pipeline.
- Augmented the base stopword list with conversational tokens such as "öyle" highlighted by renewed corpus analysis.

### Changed

- Clarified README quickstart with explicit pipeline order, suffix reattachment guidance, and modular usage examples.

## [0.2.3] - 2025-10-29

### Added

- Introduced optional suffix reattachment in `process_text` (`rejoin_suffixes`) and exposed `attach_detached_suffixes` for manual pipelines to stabilise noisy corpora.

### Changed

- Expanded the base Turkish stopword list with apostrophe-prefixed and suffix-oriented variants to better capture colloquial usage.

## [0.2.2] - 2025-10-29

### Fixed

- Fixed CITATION.cff format for Zenodo DOI generation
- Added required `type: software` field
- Changed license format to "Other" for custom licenses
- Added keywords for better discoverability
- Standardized citation metadata structure

## [0.2.0] - 2025-10-29

- Promoted stopword utilities to the top-level API, including `remove_stopwords`,
  new `is_stopword` and `list_stopwords` helpers, and clearer metadata resource naming.
- Added `process_text` for an end-to-end clean → tokenize → stopword removal pipeline,
  plus `tokenize(..., strip_punct=True)` for punctuation-free token streams.
- Documented usage examples in key docstrings and README quickstart for faster adoption.
- Updated licensing to Durak License v1.2 and bumped package metadata to version 0.2.0.

## [0.1.0] - 2025-10-19

- Initial public release of the Durak NLP toolkit.
- Added text cleaning utilities with Turkish-specific heuristics.
- Shipped configurable stopword management and serialization helpers.
- Introduced regex-based tokenizer, sentence splitting, and corpus validator integration.
- Provided development tooling (pytest, ruff, mypy configs) and packaging metadata for TestPyPI/PyPI releases.

[Unreleased]: https://github.com/fbkaragoz/durak/compare/v0.4.0...HEAD
[0.4.0]: https://github.com/fbkaragoz/durak/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/fbkaragoz/durak/compare/v0.2.4...v0.3.0
[0.2.4]: https://github.com/fbkaragoz/durak/compare/v0.2.3...v0.2.4
[0.2.3]: https://github.com/fbkaragoz/durak/compare/v0.2.2...v0.2.3
[0.2.0]: https://github.com/fbkaragoz/durak/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/fbkaragoz/durak/releases/tag/v0.1.0
