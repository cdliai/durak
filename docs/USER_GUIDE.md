# User Guide

## Getting Started

Durak is a Turkish NLP toolkit designed for preprocessing and analysis. It handles Turkish-specific text processing requirements including proper noun apostrophes, suffix attachment, and the Turkish dotted/dotless I distinction.

### Installation

```bash
pip install durak-nlp
```

For development (includes Rust extension):
```bash
git clone https://github.com/fbkaragoz/durak.git
cd durak
maturin develop
```

## Basic Usage

### Processing Single Texts

The simplest way to process text:

```python
from durak import TextProcessor

processor = TextProcessor()
result = processor.process("Türkiye'de NLP zor!")
print(result.tokens)
# Output: ["türkiye'de", 'nlp', 'zor', '!']
```

### Configuration Options

Control what processing steps to apply:

```python
from durak import ProcessorConfig

# Remove stopwords
config = ProcessorConfig(remove_stopwords=True)
processor = TextProcessor(config)

result = processor.process("Bu bir test cümlesidir.")
print(result.tokens)
# Output: ['test', 'cümlesidir']
# Note: "bu" and "bir" are filtered as stopwords
```

### Handling Noisy Text

Social media and informal text often has spacing issues:

```python
# Detached suffixes (common in noisy text)
config = ProcessorConfig(attach_suffixes=True)
processor = TextProcessor(config)

result = processor.process("Ankara ' da kaldım.")
print(result.tokens)
# Output: ["ankara'da", 'kaldım']
# Note: suffix reattached to form proper token
```

### Emoji Handling

Three modes available:

```python
# Keep emojis (default)
config = ProcessorConfig(emoji_mode="keep")

# Remove emojis
config = ProcessorConfig(emoji_mode="remove")

# Extract emojis separately
config = ProcessorConfig(emoji_mode="extract")
result = processor.process("Harika! 🎉")
print(result.tokens)   # ['harika']
print(result.emojis)   # ['🎉']
```

## Batch Processing

Process multiple texts efficiently:

```python
texts = [
    "Birinci doküman.",
    "İkinci doküman.",
    "Üçüncü doküman.",
]

results = processor.process_batch(texts)
for result in results:
    print(result.tokens)
```

## Building Custom Pipelines

For more control, use the Pipeline class directly:

```python
from durak import Pipeline, clean_text, tokenize, remove_stopwords

pipeline = Pipeline([
    clean_text,
    tokenize,
    lambda tokens: remove_stopwords(tokens),
])

result = pipeline("Türkiye'de NLP zor!")
```

## Frequency Analysis

Count word frequencies across documents:

```python
from durak.stats import FrequencyCounter
from durak import TextProcessor

processor = TextProcessor()
counter = FrequencyCounter()

documents = ["Birinci.", "İkinci.", "Üçüncü."]
for doc in documents:
    result = processor.process(doc)
    counter.add(result.tokens)

# Most common words
print(counter.most_common(10))

# Export to file
counter.to_tsv("frequencies.tsv")
```

### N-gram Analysis

Analyze word sequences:

```python
from durak.stats import FrequencyCounter

# Bigram analysis
counter = FrequencyCounter(ngram_size=2)
counter.add(['kitap', 'okumak', 'güzel'])
counter.add(['kitap', 'yazmak', 'güzel'])

print(counter.most_common())
# Output: [(('kitap', 'okumak'), 1), (('kitap', 'yazmak'), 1), ...]
```

## Working with Lemmas

For lemmatization (requires Rust extension):

```python
from durak import Lemmatizer

lemmatizer = Lemmatizer(strategy="hybrid")
print(lemmatizer("kitaplar"))  # Output: "kitap"
print(lemmatizer("geliyorum"))  # Output: "gel"
```

Strategies:
- `lookup`: Dictionary only (fast, precise)
- `heuristic`: Suffix stripping (handles unknown words)
- `hybrid`: Dictionary first, fallback to heuristic (recommended)

## Common Use Cases

### Social Media Analysis

```python
config = ProcessorConfig(
    remove_stopwords=True,
    emoji_mode="extract",
    attach_suffixes=True,
)
processor = TextProcessor(config)

# Process tweet
tweet = "Hey @ahmet! Bu haber çok güzel 😊🎉"
result = processor.process(tweet)
print(result.tokens)   # ['haber', 'güzel']
print(result.emojis)   # ['😊', '🎉']
```

### Document Preprocessing

```python
config = ProcessorConfig(
    remove_stopwords=True,
    remove_punctuation=True,
    lowercase=True,
)
processor = TextProcessor(config)

# Clean document for machine learning
doc = "Türkiye'de NLP zor. Durak kolaylaştırır!"
result = processor.process(doc)
print(result.tokens)   # ["türkiye'de", 'nlp', 'zor', 'durak', 'kolaylaştırır']
```

### Corpus Statistics

```python
from durak.stats import FrequencyCounter

processor = TextProcessor()
counter = FrequencyCounter(
    filter_stopwords=True,
    ngram_size=1,
)

# Process corpus corpus = [...]  # List of documents
for doc in corpus:
    result = processor.process(doc)
    counter.add(result.tokens)

print(f"Unique tokens: {counter.unique_count}")
print(f"Total tokens: {counter.total_tokens}")
print(f"Most common: {counter.most_common(20)}")
```

## Tips and Best Practices

### Performance

For processing large datasets:

1. Create processor once, reuse many times:
```python
processor = TextProcessor(config)  # Create once
results = [processor.process(text) for text in large_corpus]
```

2. Use batch processing:
```python
results = processor.process_batch(texts)  # More efficient than loop
```

3. Build Rust extension for maximum speed:
```bash
maturin develop --release
```

### Text Quality

- Use `attach_suffixes=True` for social media or OCR text
- Use `emoji_mode="extract"` if emojis are features
- Use `remove_punctuation=True` for clean token streams
- Test with your specific text domain

### Error Handling

```python
from durak import TextProcessor, DurakError

processor = TextProcessor()

try:
    result = processor.process(text)
except DurakError as e:
    print(f"Processing failed: {e}")
```

## Troubleshooting

**Issue:** Import errors for Rust functions  
**Solution:** Rust extension not built. Either:
- Install from PyPI (pre-built wheels)
- Run `maturin develop` to build locally
- Code works without Rust, just slower

**Issue:** Turkish I not converting correctly  
**Solution:** This is handled automatically. Verify with:
```python
from durak import normalize_case
print(normalize_case("İSTANBUL"))  # Should print "istanbul"
print(normalize_case("IĞDIR"))     # Should print "ığdır"
```

**Issue:** Suffixes not attaching  
**Solution:** Ensure suffix is in the detached suffixes list:
```python
from durak import DEFAULT_DETACHED_SUFFIXES
print('da' in DEFAULT_DETACHED_SUFFIXES)  # Should be True
```

## Next Steps

- See `TECHNICAL_REFERENCE.md` for detailed API documentation
- See `examples/` directory for more code samples
- Run `python test_data/run_analytics.py` to see performance metrics
