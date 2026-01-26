# Tokenization Guide

This guide covers Durak's tokenization APIs, including offset mapping for downstream tasks like Named Entity Recognition (NER).

## Overview

Durak provides multiple tokenization functions optimized for different use cases:

- **`tokenize()`**: High-level Python tokenization
- **`tokenize_with_offsets()`**: Returns raw tokens with character offsets
- **`tokenize_with_normalized_offsets()`**: Returns normalized tokens with offsets pointing to original text ⭐ **NER-friendly**

## Basic Usage

### Simple Tokenization

```python
from durak import tokenize

text = "İstanbul'a gittim."
tokens = tokenize(text)
# ['İstanbul', "'", 'a', 'gittim', '.']
```

### Tokenization with Offsets

```python
from durak import tokenize_with_offsets

text = "Ali gel."
tokens = tokenize_with_offsets(text)
# [('Ali', 0, 3), ('gel', 4, 7), ('.', 7, 8)]

# Verify offsets
for token, start, end in tokens:
    assert text[start:end] == token
```

## NER-Friendly Tokenization

### The Problem

When working with labeled data (e.g., NER annotations), labels typically reference the **original** text positions. However, standard NLP pipelines normalize text before tokenization:

```python
text = "İstanbul güzel."  # Original
normalized = text.lower()  # "istanbul güzel."
tokens = tokenize_with_offsets(normalized)
# Offsets now point to normalized text, not original!
```

This breaks alignment with your labels, which reference character positions in the original text.

### The Solution: `tokenize_with_normalized_offsets()`

This function tokenizes the **original** text but returns **normalized** tokens, with offsets still pointing to the original:

```python
from durak import tokenize_with_normalized_offsets

text = "İstanbul'a gittim."
tokens = tokenize_with_normalized_offsets(text)
# [('istanbul'a', 0, 10), ('gittim', 11, 17), ('.', 17, 18)]

# Tokens are normalized...
assert tokens[0][0] == "istanbul'a"  # lowercase

# ...but offsets reference original text
assert text[0:10] == "İstanbul'a"  # original case preserved
```

### NER Example

```python
from durak import tokenize_with_normalized_offsets

# Labeled data: entity annotations reference original text
text = "İstanbul güzel bir şehir."
entities = [
    {"text": "İstanbul", "start": 0, "end": 8, "label": "LOC"}
]

# Tokenize with normalized offsets
tokens = tokenize_with_normalized_offsets(text)

# Find entity tokens using original positions
for entity in entities:
    entity_tokens = [
        (tok, start, end) 
        for tok, start, end in tokens
        if start >= entity["start"] and end <= entity["end"]
    ]
    
    print(f"Entity: {entity['text']}")
    print(f"Tokens: {[tok for tok, _, _ in entity_tokens]}")
    # Entity: İstanbul
    # Tokens: ['istanbul']
```

## Turkish-Specific Considerations

### Case Normalization

Turkish has special case rules that require careful handling:

| Original | Lowercase | Uppercase |
|----------|-----------|-----------|
| İ        | i         | İ         |
| I        | ı         | I         |
| i        | i         | İ         |
| ı        | ı         | I         |

`tokenize_with_normalized_offsets()` correctly handles Turkish case folding via Durak's `fast_normalize()`:

```python
from durak import tokenize_with_normalized_offsets

# İ → i
text = "İZMİR"
tokens = tokenize_with_normalized_offsets(text)
assert tokens[0] == ("izmir", 0, 5)
assert text[0:5] == "İZMİR"

# I → ı
text = "IĞDIR"
tokens = tokenize_with_normalized_offsets(text)
assert tokens[0] == ("ığdır", 0, 5)
assert text[0:5] == "IĞDIR"
```

### Multi-Byte UTF-8

Turkish characters like `İ`, `ğ`, `ş` are multi-byte in UTF-8. Durak returns **character offsets**, not byte offsets:

```python
from durak import tokenize_with_normalized_offsets

text = "İğne"  # 4 chars, but 7 bytes in UTF-8
tokens = tokenize_with_normalized_offsets(text)
assert tokens[0] == ("iğne", 0, 4)  # Character offsets

# Slicing works correctly
assert text[0:4] == "İğne"
```

## Hugging Face Transformers Integration

Durak's offset mapping aligns with Hugging Face's `offset_mapping` convention, making it easy to build preprocessing pipelines:

```python
from durak import tokenize_with_normalized_offsets
from transformers import AutoTokenizer

# 1. Durak preprocessing with offset preservation
text = "İstanbul'da çalışıyorum."
durak_tokens = tokenize_with_normalized_offsets(text)

# 2. Pass to BERT tokenizer
tokenizer = AutoTokenizer.from_pretrained("dbmdz/bert-base-turkish-cased")
bert_tokens = tokenizer(
    [tok for tok, _, _ in durak_tokens],
    is_split_into_words=True,
    return_offsets_mapping=True
)

# 3. Map BERT subwords back to original text via Durak offsets
# (Implementation depends on your specific use case)
```

## Performance Considerations

- **Rust implementation**: All tokenization functions are implemented in Rust for maximum performance
- **Zero-copy where possible**: Offsets reference the original string without copying
- **Batch processing**: For large corpora, batch your texts before tokenizing

```python
from durak import tokenize_with_normalized_offsets

# Efficient batch processing
texts = ["İstanbul", "Ankara", "İzmir"]
all_tokens = [tokenize_with_normalized_offsets(text) for text in texts]
```

## API Reference

### `tokenize_with_offsets(text: str) -> list[tuple[str, int, int]]`

Returns raw tokens with character offsets pointing to the input text.

**Parameters:**
- `text`: Input text (will not be normalized)

**Returns:**
- List of `(token, start, end)` tuples where:
  - `token`: Raw token string (as it appears in text)
  - `start`: Character offset where token starts
  - `end`: Character offset where token ends

**Example:**
```python
tokens = tokenize_with_offsets("Ali gel.")
# [('Ali', 0, 3), ('gel', 4, 7), ('.', 7, 8)]
```

### `tokenize_with_normalized_offsets(text: str) -> list[tuple[str, int, int]]`

Returns normalized tokens with character offsets pointing to the **original** text.

**Parameters:**
- `text`: Input text (original, unnormalized)

**Returns:**
- List of `(token, start, end)` tuples where:
  - `token`: Normalized token string (lowercase, Turkish rules applied)
  - `start`: Character offset in **original** text where token starts
  - `end`: Character offset in **original** text where token ends

**Example:**
```python
tokens = tokenize_with_normalized_offsets("İstanbul'a gittim.")
# [('istanbul'a', 0, 10), ('gittim', 11, 17), ('.', 17, 18)]

# Tokens are normalized but offsets reference original
assert tokens[0][0] == "istanbul'a"  # normalized
assert text[0:10] == "İstanbul'a"   # original
```

## Best Practices

### ✅ DO: Use `tokenize_with_normalized_offsets()` for NER

```python
from durak import tokenize_with_normalized_offsets

# Labels reference original text
text = "İstanbul güzel."
entities = [{"text": "İstanbul", "start": 0, "end": 8}]

# Tokenize with normalized offsets
tokens = tokenize_with_normalized_offsets(text)

# Match entities using offsets
for entity in entities:
    matching_tokens = [
        tok for tok, start, end in tokens
        if start == entity["start"] and end == entity["end"]
    ]
```

### ✅ DO: Validate offsets in tests

```python
tokens = tokenize_with_normalized_offsets(text)
for token, start, end in tokens:
    # Offsets must point to valid slice
    assert text[start:end].lower() == token.lower()
```

### ❌ DON'T: Normalize text before using offset-based tokenization

```python
# BAD: Offsets won't match original
normalized = text.lower()
tokens = tokenize_with_offsets(normalized)

# GOOD: Tokenize original, get normalized tokens
tokens = tokenize_with_normalized_offsets(text)
```

## See Also

- [ARCHITECTURE.md](ARCHITECTURE.md): Durak's design principles
- [BEST_PRACTICES.md](BEST_PRACTICES.md): General usage guidelines
- [Issue #7](https://github.com/cdliai/durak/issues/7): Original feature request and discussion
