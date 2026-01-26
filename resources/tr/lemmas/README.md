# Turkish Lemma Dictionary

## Overview

This directory contains lemma dictionaries for Turkish language processing. The dictionary maps inflected word forms to their base lemmas (dictionary forms).

## Format

**File:** `turkish_lemma_dict.txt`  
**Format:** Tab-separated values (TSV)
```
inflected_form<TAB>lemma
```

Example:
```
kitaplar	kitap
evler	ev
geliyorum	gel
```

## Coverage

Current dictionary focuses on high-frequency words across common domains:
- Nouns with plural suffixes (-lar, -ler)
- Verbs with common tense/aspect/person markers
- Adjectives and adverbs with derivational suffixes
- Pronouns and determiners

## Sources

- Hand-curated high-frequency Turkish words
- Based on Turkish morphophonological rules (vowel harmony, consonant alternation)
- Validated against Turkish National Corpus frequency data

## License

CC0 1.0 Universal (Public Domain Dedication)

This work is curated for the Durak project and is freely available for research and commercial use.

## Future Extensions

- Expand to 10K+ entries using TRMorph/Zemberek data
- Add morphological feature annotations
- Include pronunciation variants
