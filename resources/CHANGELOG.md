# Resource Changelog

All notable changes to embedded resources are documented here.

This file tracks versions of linguistic resources embedded in Durak's binary,
enabling research reproducibility and impact assessment.

## Format

Each entry includes:
- **Version**: Semantic versioning for each resource
- **Date**: When the change was made
- **Changes**: What was added, removed, or modified
- **Impact**: Expected effect on preprocessing results

---

## [1.0.0] - 2026-01-26

### Initial Release

**Stopwords (Base)**
- **Count**: 118 words
- **Source**: Curated by Durak team, based on Turkish linguistic standards
- **Coverage**: Function words, pronouns, auxiliary verbs, common particles
- **Checksum**: `361908bbb0a44efc7dcb2dfb600d13a64d3982623701bd4057e0af69ca6d0b04`

**Stopwords (Social Media)**
- **Count**: 11 words
- **Source**: Social media corpus analysis
- **Coverage**: Platform-specific abbreviations, slang stopwords
- **Checksum**: `1469b2b0cf2a83dfe18eb6e9d7043e639f301b5a03473fa22f9d39f326ebc5d4`

**Detached Suffixes**
- **Count**: 14 suffixes
- **Source**: Turkish grammar rules (TDK standards)
- **Coverage**: Case markers, possessives, question particles
- **Examples**: `'le`, `'den`, `'nin`, `'mi`
- **Checksum**: `b4d672bec0fca3ac87835a19095698c7080fff7bf96bbf67b3e4e1aa6bbbaea7`

**Apostrophes**
- **Count**: 2 rules
- **Source**: Turkish orthography standards
- **Purpose**: Proper name apostrophe handling
- **Checksum**: `6166a0447c04ffdfad71f7882ef83a916e3debc51ab8639392603f50106dea05`

**Lemma Suffixes**
- **Count**: 30 suffixes
- **Source**: Turkish morphology rules
- **Purpose**: Heuristic lemmatization suffix stripping
- **Checksum**: `2e5aeb7f0aeb3608fdd00530bba8f7ad827bde91ee0044688e3d1d80936be8bc`

---

## Future Changes

### [1.1.0] - Planned

**Stopwords (Base)** - Potential additions based on user feedback:
- Social media abbreviations (`bi`, `bşy`, etc.)
- Common interjections
- **Impact**: May reduce token counts by ~1-2% on informal text

**Note**: Any resource change will bump the minor version and be documented here before release.

---

## How to Use This File

### For Researchers
When citing Durak in papers, include the resource version:
```bibtex
@software{durak2026,
  title = {Durak: Turkish NLP Toolkit},
  author = {Karagöz, Fatih Burak},
  version = {0.4.0},
  year = {2026},
  note = {Resources v1.0.0}
}
```

### For Reproducibility
To verify you're using the same resources as a previous experiment:
```python
from durak import get_resource_info
resources = get_resource_info()
assert resources['stopwords_base']['checksum'] == '361908bbb0a4...'
```

### For Impact Assessment
When upgrading Durak versions, check this file to see if resource changes
might affect your preprocessing pipeline.
