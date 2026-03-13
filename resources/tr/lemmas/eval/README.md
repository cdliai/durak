# Lemmatization Evaluation Test Sets

This directory contains gold-standard test sets for evaluating lemmatizer quality.

## Files

### `gold_standard.tsv`

Hand-curated test set with 152 entries covering:

- **Nouns** (63 entries): plural, case markers (accusative, dative, locative, ablative), possessive, genitive
- **Verbs** (85 entries): present continuous, past tense, future tense, infinitive, simple present
- **Pronouns** (included in noun cases)
- **Edge cases** (4 entries): short words, compound suffixes

**Format:**
```
inflected<TAB>lemma<TAB>source
```

**Sources:**
- `manual`: Hand-curated entries
- `dict`: From `turkish_lemma_dict.txt`
- `test`: From existing unit tests

## Usage

### Basic Evaluation

```python
from durak.lemmatizer import Lemmatizer
import pandas as pd

# Load test set
df = pd.read_csv("resources/tr/lemmas/eval/gold_standard.tsv", 
                 sep="\t", comment="#", 
                 names=["word", "lemma", "source"])

# Evaluate a strategy
lemmatizer = Lemmatizer(strategy="hybrid")
correct = sum(lemmatizer(row.word) == row.lemma for _, row in df.iterrows())
accuracy = correct / len(df)

print(f"Accuracy: {accuracy:.2%} ({correct}/{len(df)})")
```

### Strategy Comparison

```bash
python scripts/evaluate_lemmatizer.py
```

## Expansion

Future test sets to add:

- `domain_news.tsv`: Formal news corpus (high dictionary coverage expected)
- `domain_social_media.tsv`: Informal text (OOV-heavy, slang, misspellings)
- `domain_technical.tsv`: Technical/scientific terms
- `edge_cases.tsv`: Adversarial examples (apostrophes, rare patterns)

## Provenance

- **Gold standard**: Curated by cdliai team (Jan 2026)
- **Dictionary entries**: From `turkish_lemma_dict.txt` (v0.5.0+)
- **Test cases**: From `tests/test_lemmatizer.py` regression tests

## Citation

If using these test sets in research:

```bibtex
@software{durak_lemma_eval,
  title = {Durak Turkish NLP Lemmatization Evaluation Sets},
  author = {{CDLI AI}},
  year = {2026},
  url = {https://github.com/cdliai/durak}
}
```
