# Ottoman Turkish Resources

This directory contains language resources for processing historical Ottoman Turkish texts.

## Files

- `stopwords_ottoman.json` - Common stopwords in Ottoman Turkish
- `suffixes_ottoman.json` - Morphological suffixes

## Usage

```python
from durak.ottoman import OttomanProcessor, OttomanConfig

# Use default Ottoman resources
processor = OttomanProcessor()

# Use custom resources
config = OttomanConfig(
    custom_stopwords="path/to/custom_stopwords.json",
    custom_suffixes="path/to/custom_suffixes.json",
)
processor = OttomanProcessor(config)
```

## Resource Format

### Stopwords JSON
```json
{
  "name": "Resource Name",
  "version": "1.0.0",
  "stopwords": ["word1", "word2", ...]
}
```

### Suffixes JSON
```json
{
  "name": "Resource Name",
  "version": "1.0.0",
  "suffixes": ["suffix1", "suffix2", ...]
}
```

## Customization for Ottoman Miner

Ottoman Miner can provide its own resources:

```python
processor = create_ottoman_processor(
    custom_stopwords="ottoman_miner/stopwords.json",
    custom_suffixes="ottoman_miner/suffixes.json",
)
```

This allows domain-specific customization (e.g., legal documents, financial records).
