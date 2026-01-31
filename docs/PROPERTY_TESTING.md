# Property-Based Testing Guide

Durak uses [Hypothesis](https://hypothesis.readthedocs.io/) for property-based testing to ensure robustness across a wide range of Turkish text inputs.

## What is Property-Based Testing?

Unlike traditional unit tests that check specific examples, property-based tests verify **mathematical properties** that should hold for **all inputs**.

### Example: Traditional vs Property-Based

**Traditional test:**
```python
def test_normalize_case():
    assert normalize_case("İSTANBUL") == "istanbul"
    assert normalize_case("ANKARA") == "ankara"
```

**Property-based test:**
```python
@given(turkish_word())
def test_normalize_case_is_idempotent(word):
    """Normalizing twice should equal normalizing once."""
    normalized_once = normalize_case(word)
    normalized_twice = normalize_case(normalized_once)
    assert normalized_once == normalized_twice
```

The property test generates **hundreds of random Turkish words** and verifies the idempotence property holds for all of them.

## Why Property-Based Testing for Turkish NLP?

Turkish has unique challenges that make property testing especially valuable:

1. **Diacritic complexity**: İ/I vs i/ı conversion must be correct in all cases
2. **Apostrophe handling**: `İstanbul'a`, `Ankara'da` create complex token boundaries
3. **Unicode edge cases**: Zero-width characters, combining diacritics, RTL marks
4. **Morphological richness**: Agglutination creates extremely long, unpredictable words
5. **Capitalization rules**: Turkish-specific uppercase/lowercase conversions

Traditional unit tests can't cover the combinatorial space of these features.

## Text Generation Strategies

Durak provides specialized Hypothesis strategies in `tests/strategies.py`:

### Basic Strategies

```python
from tests.strategies import turkish_word, turkish_sentence

# Generate random Turkish words
turkish_word()  # "çalışmak", "görmek", "İstanbul", etc.

# Generate words with possessive/case markers
turkish_word_with_suffix()  # "İstanbul'a", "Ankara'dan", etc.

# Generate full sentences
turkish_sentence()  # "İstanbul'a gittik ve müze'yi gördük."
```

### Advanced Strategies

```python
# Unicode edge cases (zero-width chars, combining diacritics)
turkish_text_with_unicode_edge_cases()

# Lists of Turkish stopwords
turkish_stopword_list()
```

## Writing Property Tests

### 1. Import the Strategy

```python
from hypothesis import given
from tests.strategies import turkish_sentence
```

### 2. Define the Property

```python
@given(turkish_sentence())
def test_tokenize_always_returns_list(text):
    """Tokenization must always return a list."""
    tokens = tokenize(text)
    assert isinstance(tokens, list)
```

### 3. Run with Hypothesis

Hypothesis will:
- Generate 100-200 random examples (configurable with `@settings(max_examples=N)`)
- Run your test on each example
- If a failure occurs, **shrink** to find the minimal failing case
- Cache failures for regression testing

## Common Properties to Test

### Idempotence

Functions that should give the same result when applied twice:

```python
@given(turkish_sentence())
def test_normalize_is_idempotent(text):
    assert normalize_case(text) == normalize_case(normalize_case(text))
```

### Inverse Functions

Functions that should undo each other:

```python
@given(turkish_sentence())
def test_tokenize_rejoins(text):
    tokens = tokenize(text)
    rejoined = "".join(tokens)
    # Should preserve non-whitespace content
    assert set(rejoined.replace(" ", "")) == set(text.replace(" ", ""))
```

### Monotonicity

Functions that should never increase size:

```python
@given(turkish_word())
def test_normalization_not_expanding(word):
    assert len(normalize_case(word)) <= len(word)
```

### Consistency

Related functions should agree:

```python
@given(turkish_sentence())
def test_offset_consistency(text):
    tokens_with_offsets = tokenize_with_offsets(text)
    for token, start, end in tokens_with_offsets:
        # Offset must be valid
        assert 0 <= start < end <= len(text)
        # Extracted text should match token
        extracted = text[start:end]
        assert extracted.lower() == token.lower()
```

## Controlling Test Execution

### Number of Examples

```python
from hypothesis import settings

@given(turkish_sentence())
@settings(max_examples=500)  # Generate 500 random examples
def test_something(text):
    ...
```

### Filtering Invalid Inputs

```python
from hypothesis import assume

@given(turkish_sentence())
def test_non_empty_tokenization(text):
    assume(len(text.strip()) > 0)  # Skip empty strings
    tokens = tokenize(text)
    assert len(tokens) > 0
```

### Debugging Failures

When a property test fails, Hypothesis prints:
1. The **minimal failing example** (after shrinking)
2. The **random seed** to reproduce the failure

```
Falsifying example: test_something(text='İ')
You can reproduce this by running:
    pytest --hypothesis-seed=12345
```

## Running Property Tests

### Run all property tests:

```bash
pytest tests/test_properties.py -v
```

### Show Hypothesis statistics:

```bash
pytest tests/test_properties.py --hypothesis-show-statistics
```

Output:
```
  - 200 passing examples, 0 failing examples, 0 invalid examples
  - Typical runtimes: 0-1ms, ~ 50% in data generation
  - Stopped because settings.max_examples=200
```

### Run with more examples (stress test):

```bash
pytest tests/test_properties.py --hypothesis-profile=ci
```

## Best Practices

### ✅ Do:

- Test **mathematical properties**, not specific examples
- Use `assume()` to filter out invalid inputs
- Keep properties simple and focused (one property per test)
- Use meaningful assertion messages
- Combine traditional and property-based tests

### ❌ Don't:

- Test implementation details
- Make tests too complex (they become hard to debug)
- Over-constrain input generation (reduces coverage)
- Ignore failures (Hypothesis finds real edge cases!)

## Example: Real Bug Caught by Property Testing

**Property test:**
```python
@given(turkish_word())
def test_normalize_case_removes_uppercase(word):
    normalized = normalize_case(word)
    assert "İ" not in normalized
```

**Bug found:**
```
Falsifying example: test_normalize_case_removes_uppercase(word='İİİ')
AssertionError: 'İ' found in normalized output
```

**Root cause:** Normalization was using Python's `.lower()` instead of Turkish-aware lowercase conversion. Property testing caught it instantly!

## Resources

- [Hypothesis Documentation](https://hypothesis.readthedocs.io/)
- [Property-Based Testing Patterns](https://hypothesis.works/articles/what-is-property-based-testing/)
- [Hypothesis for Python Developers](https://hypothesis.works/articles/quickcheck-in-every-language/)

## Contributing

When adding new features to Durak:

1. **Add traditional unit tests** for specific examples
2. **Add property tests** for general behavior
3. **Document invariants** that your function guarantees

Property tests serve as **executable specifications** and protect against regressions.
