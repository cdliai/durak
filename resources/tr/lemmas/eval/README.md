# Turkish Lemmatization Evaluation Test Sets

This directory contains gold-standard test sets for evaluating lemmatization quality.

## Files

### `gold_standard.tsv`
Hand-curated test set with 73+ Turkish word-lemma pairs covering:
- **Nouns**: plural forms, case markers, possessives (ev → evler, kitabı, evim)
- **Verbs**: present/past/future tense conjugations (gel → geliyorum, geldim, gelecek)
- **Pronouns**: personal pronouns with cases (ben → beni, bana, bende)
- **Edge cases**: short words, unknown words, protection rules

**Format:**
```tsv
# Comment lines start with #
inflected<TAB>lemma<TAB>source
kitaplar	kitap	test
geliyorum	gel	test
```

**Sources:**
- `test` = Extracted from unit tests
- `dict` = Validated against dictionary
- `manual` = Hand-curated

## Usage

### Run Evaluation

```bash
# Compare all strategies
python scripts/evaluate_lemmatizer.py --all

# Evaluate single strategy
python scripts/evaluate_lemmatizer.py --strategy lookup

# Show detailed errors
python scripts/evaluate_lemmatizer.py --all --show-errors

# Save results as baseline for CI
python scripts/evaluate_lemmatizer.py --all --save-baseline

# Check for regressions (exits with code 1 if >5% drop)
python scripts/evaluate_lemmatizer.py --all --check-regression
```

### Current Baseline (v0.4.0)

| Strategy   | Accuracy | Coverage Notes                              |
|------------|----------|---------------------------------------------|
| **lookup**     | 97.3%    | High precision for dictionary-covered words |
| **heuristic**  | 20.5%    | Lower precision, better OOV handling        |
| **hybrid**     | 97.3%    | Combines both (default, recommended)        |

## Choosing a Strategy

### When to use `lookup`:
- Formal/standard Turkish text (news, documents)
- Need high precision
- Corpus is mostly in-vocabulary

### When to use `heuristic`:
- OOV-heavy domains (social media, slang, misspellings)
- Need better recall on unknown words
- Can tolerate lower precision

### When to use `hybrid` (default):
- General-purpose NLP tasks
- Balanced precision/recall trade-off
- Most research applications

## Extending the Test Set

To add new test cases:

1. **Add entries to `gold_standard.tsv`:**
   ```tsv
   yemeğe	yemek	manual
   gördüm	gör	manual
   ```

2. **Maintain format:** `inflected<TAB>lemma<TAB>source`

3. **Run validation:**
   ```bash
   python scripts/evaluate_lemmatizer.py --all --show-errors
   ```

4. **Update baseline if accuracy improves:**
   ```bash
   python scripts/evaluate_lemmatizer.py --all --save-baseline
   ```

## Provenance & Citation

Test cases are derived from:
- Durak unit tests (`tests/test_lemmatizer.py`)
- Manual curation by Turkish NLP researchers
- Validated against Turkish morphology resources (TRMorph, Zemberek)

**License:** CC BY 4.0 (attribution required)

## Future Work

- [ ] Add domain-specific test sets (social media, news, literature)
- [ ] Expand to 200+ test cases for better coverage
- [ ] Add morphological feature annotations (POS tags, case markers)
- [ ] Cross-validate against TRMorph gold standard
- [ ] Add inter-annotator agreement metrics for manual curation
