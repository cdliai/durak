# Durak Project Learnings

## Date: 2026-02-02

### PR #140: Add pre-commit hooks for automated code quality checks

**Issue:** #122 - Add pre-commit hooks for automated code quality checks

**What I did:**
- Created `.pre-commit-config.yaml` with comprehensive hooks:
  - Black (Python formatting)
  - Ruff (linting + import sorting with auto-fix)
  - MyPy (type checking)
  - Rust fmt (Rust formatting)
  - Clippy (Rust linting)
  - Pre-commit hooks (trailing whitespace, merge conflicts, YAML/TOML validation, etc.)
- Updated `CONTRIBUTING.md` with pre-commit setup instructions

**Key learnings:**
1. Pre-commit hooks run automatically on `git commit` before the commit is finalized
2. Hooks can be run manually on all files with `pre-commit run --all-files`
3. The hooks are configured to only run on relevant directories (python/, tests/, src/) for performance
4. Ruff's `--fix` flag automatically fixes many linting issues
5. Rust fmt uses `-- --check` to only check formatting, not modify files
6. Clippy uses `-D warnings` to treat all warnings as errors

**Notes on file structure:**
- Python source: `python/durak/`
- Rust source: `src/`
- Tests: `tests/`
- Resources: `resources/tr/`

---

### Issue #120 Status: Already Fixed

Issue #120 (CONTRIBUTING.md has incorrect mypy command) was already fixed in commit `741f044` by Rabia Sarfaraz on Jan 28, 2026.

The fix changed `mypy src` to `mypy python` in CONTRIBUTING.md line 34.

---

### Branch: fix/110-eliminate-duplicate-suffix-lists

There's existing work on this branch that adds Python bindings for:
- `strip_suffixes_validated()`
- `check_vowel_harmony_py()`
- `get_vowel_class_py()`
- `validate_suffix_order_py()`

This addresses issue #117: Expose vowel harmony and morphotactics validation functions in Python API.

The work includes:
- Rust code in `src/lib.rs` with Python bindings
- Python exports in `python/durak/__init__.py`
- Type stubs in `python/durak/_durak_core.pyi`

**Status:** Incomplete, needs testing and possible fixes.

---

### Issue #117 Details: Expose vowel harmony and morphotactics validation

The Rust core has powerful morphological validation modules:
- `src/vowel_harmony.rs`: Front/back and rounded/unrounded vowel harmony checking
- `src/morphotactics.rs`: Suffix ordering constraints validation

These are used internally by `strip_suffixes()` but not exposed in the Python API.

**Use cases:**
1. Advanced lemmatization debugging
2. Morphological analysis tools
3. Educational/research applications
4. Custom preprocessing pipelines

**Current progress:**
- Functions added to Rust with PyO3 bindings
- Python exports added to `__init__.py`
- Type stubs added to `.pyi` file
- Tests exist in `tests/test_vowel_harmony.py`

**Next steps for #117:**
1. Build the Rust extension with `maturin develop --release`
2. Run tests to verify functionality
3. Check for any missing implementations or bugs
4. Submit PR for review

---

### Other Good First Issues to Consider:

- #87: Add Unit Tests for Normalizer Module
- #91: Make Normalizer Configuration Actually Work
- #110: Eliminate Duplicate Suffix Lists in Rust Core (DRY Violation)
- #113: Add Criterion Rust Benchmarks for Performance Tracking

---

### Development Environment Notes:

To build and test Durak:
```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Build and install with Rust extension
pip install maturin
maturin develop --release

# Install dev dependencies
pip install -e .[dev]

# Run tests
pytest

# Type checking
mypy python

# Linting
ruff check .
```

**Note:** Maturin was not installed on the system during this session, which prevented building the Rust extension.
