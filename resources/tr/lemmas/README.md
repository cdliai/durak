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

**Dictionary Size:** 1,362 inflected forms → base lemmas

Current dictionary focuses on high-frequency words across common domains:
- **Nouns** with case/plural suffixes (nominative, accusative, dative, locative, ablative, genitive)
- **Verbs** with common tense/aspect/person markers (present continuous, past, future, aorist, infinitive)
- **High-frequency vocabulary** (top ~50 nouns + ~40 verbs)
- Covers ~83% of test cases for high-frequency Turkish text

**Expanded coverage (v0.4.0):**
- ✅ 399 → 1,362 entries (3.4x increase)
- ✅ Systematic inflection generation for vowel harmony classes
- ✅ Front/back vowel harmony patterns
- ⚠️ Some edge cases remain (consonant softening, irregular verbs)

## Sources

- Hand-curated high-frequency Turkish words (top 100 most common)
- Programmatically generated inflections following Turkish morphophonological rules
- Vowel harmony mapping (front: e/i/ü, back: a/ı/u)
- Based on Turkish National Corpus frequency patterns

## License

CC0 1.0 Universal (Public Domain Dedication)

This work is curated for the Durak project and is freely available for research and commercial use.

## Future Extensions

- Expand to 10K+ entries using TRMorph/Zemberek data
- Add morphological feature annotations
- Include pronunciation variants
