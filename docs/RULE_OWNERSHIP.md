# Durak Rule Ownership

This document defines canonical sources for linguistic rules and runtime resources.
If a rule appears in multiple places, this file defines which one is authoritative.

## Canonical Sources

- Suffix inventory (Rust lemmatization/morphotactics): `src/suffix_inventory.rs`
- Morphotactic slot validation logic: `src/morphotactics.rs` (fed by `src/suffix_inventory.rs`)
- Rust tokenization behavior: `src/lib.rs` (`tokenize_with_offsets`)
- Python tokenization fallback behavior: `python/durak/tokenizer.py` (`regex` strategy)
- Tokenizer parity gate (Rust vs Python): `tests/test_tokenizer_parity.py`
- Detached suffix resource: `resources/tr/labels/DETACHED_SUFFIXES.txt`
- Apostrophe resource: `resources/tr/config/apostrophes.txt`
- Stopword metadata and sets: `resources/tr/stopwords/metadata.json`
- Python resource loading gateway: `python/durak/resources_provider.py`

## Maintenance Rules

- Add or change suffix rules in `src/suffix_inventory.rs` first.
- Keep Python and Rust tokenization aligned; parity tests must pass before merge.
- Resource path changes must flow through `python/durak/resources_provider.py`.
- Do not add new hardcoded stopword/suffix path logic in feature modules.
