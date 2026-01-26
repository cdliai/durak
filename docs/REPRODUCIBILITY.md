# Reproducibility & Resource Versioning

**Research reproducibility in NLP preprocessing**

Durak embeds linguistic resources (stopwords, suffixes, morphology rules) directly into the binary at build time. To ensure research reproducibility, we track exact resource versions, checksums, and item counts.

## Why This Matters

**The Problem:**
1. Paper uses Durak v0.3.0 → publishes results
2. Durak v0.4.0 updates stopword list (adds 50 words)
3. Researcher tries to reproduce → different results!
4. No way to know what changed 🤷

**The Solution:**
Every Durak binary includes:
- ✅ Exact resource versions (semantic versioning)
- ✅ SHA256 checksums for exact matching
- ✅ Item counts (number of stopwords/suffixes)
- ✅ Source information and last update dates

## Quick Start

### Get Build Information

```python
from durak import get_build_info

info = get_build_info()
print(f"Durak v{info['durak_version']}")
print(f"Built: {info['build_date']}")
```

**Output:**
```
Durak v0.4.0
Built: 2026-01-26T08:30:51.849239Z
```

### Get Resource Metadata

```python
from durak import get_resource_info

resources = get_resource_info()

# Check stopwords version
sw = resources['stopwords_base']
print(f"{sw['name']}: v{sw['version']}")
print(f"Items: {sw['item_count']}")
print(f"Checksum: {sw['checksum'][:12]}...")
```

**Output:**
```
Turkish Stopwords (Base): v1.0.0
Items: 118
Checksum: 361908bbb0a4...
```

### Print Full Report

```python
from durak import print_reproducibility_report

print_reproducibility_report()
```

**Output:**
```
====================================================
Durak Reproducibility Report
====================================================

Build Information:
--------------------------------------------------
  durak_version       : 0.4.0
  build_date          : 2026-01-26T08:30:51.849239Z
  package_name        : _durak_core

Embedded Resources:
--------------------------------------------------

stopwords_base:
  name                : Turkish Stopwords (Base)
  version             : 1.0.0
  source              : Curated by Durak team
  checksum            : 361908bbb0a44efc...
  item_count          : 118
  last_updated        : 2026-01-26

detached_suffixes:
  name                : Turkish Detached Suffixes
  version             : 1.0.0
  source              : Turkish grammar rules
  checksum            : b4d672bec0fca3ac...
  item_count          : 14
  last_updated        : 2026-01-26

... (additional resources)
```

## Use Cases

### 1. Academic Papers

Document exact preprocessing configuration:

```python
from durak import get_bibtex_citation, print_reproducibility_report

# In your experiment script
print_reproducibility_report()

# Save citation for paper
with open("preprocessing_metadata.bib", "w") as f:
    f.write(get_bibtex_citation())
```

**BibTeX Output:**
```bibtex
@software{durak2026,
  title = {Durak: Turkish NLP Toolkit},
  author = {Karagöz, Fatih Burak},
  version = {0.4.0},
  year = {2026},
  url = {https://github.com/cdliai/durak},
  note = {Stopwords v1.0.0 (118 items, SHA256: 361908bbb0a4...)}
}
```

### 2. Reproducibility Verification

Verify you're using the same resources as a previous experiment:

```python
from durak import get_resource_info

# Load expected checksums from previous experiment
expected = {
    "durak_version": "0.4.0",
    "stopwords_checksum": "361908bbb0a44efc7dcb2dfb600d13a64d3982623701bd4057e0af69ca6d0b04"
}

# Verify current environment matches
resources = get_resource_info()
actual_checksum = resources['stopwords_base']['checksum']

if actual_checksum != expected['stopwords_checksum']:
    raise ValueError(
        f"Stopword mismatch! Expected {expected['stopwords_checksum'][:12]}..., "
        f"got {actual_checksum[:12]}..."
    )
```

### 3. Model Provenance Tracking

Save exact preprocessing configuration with trained models:

```python
import json
from durak import get_build_info, get_resource_info

# Train your model
model = train_my_model(...)

# Save provenance metadata
metadata = {
    "model_version": "1.0.0",
    "durak_build": get_build_info(),
    "durak_resources": get_resource_info(),
    "training_date": datetime.now().isoformat()
}

with open("model_metadata.json", "w") as f:
    json.dump(metadata, f, indent=2)
```

### 4. Impact Assessment

Check what changed between versions:

```python
# When upgrading Durak versions
from durak import get_resource_info

# Current version
resources = get_resource_info()
current_sw = resources['stopwords_base']

print(f"Stopwords: v{current_sw['version']} ({current_sw['item_count']} items)")

# Compare with previous version's metadata
# If checksums differ, check resources/CHANGELOG.md for impact
```

## Resource Changelog

All resource changes are documented in [`resources/CHANGELOG.md`](../resources/CHANGELOG.md).

When upgrading Durak, check the changelog to see:
- What resources changed
- How many items were added/removed
- Expected impact on your pipeline

**Example entry:**
```markdown
## [1.1.0] - 2025-02-01

### Stopwords (Base)
- Added 15 social media abbreviations
- Removed 3 words based on user feedback (#25, #26)
- **Impact**: May change token counts by ~2% on social media corpora
```

## For Developers

### Generating Resource Metadata

Resource metadata is generated automatically at build time:

```bash
# Run metadata generator
python scripts/generate_resource_metadata.py

# Output: resources/metadata.json (embedded in binary)
```

### Metadata Format

`resources/metadata.json`:
```json
{
  "version": "0.4.0",
  "build_date": "2026-01-26T08:30:51.849239Z",
  "resources": {
    "stopwords_base": {
      "name": "Turkish Stopwords (Base)",
      "version": "1.0.0",
      "source": "Curated by Durak team",
      "checksum": "361908bbb0a44efc...",
      "item_count": 118,
      "last_updated": "2026-01-26"
    }
  }
}
```

### CI Checks

Pull requests that modify resources must:
1. Update `resources/CHANGELOG.md`
2. Bump resource version in metadata generator
3. Document impact in PR description

The CI pipeline will fail if resource files change without changelog updates.

## API Reference

### `get_build_info() -> Dict[str, str]`

Returns Durak build metadata:
- `durak_version`: Package version (e.g., '0.4.0')
- `build_date`: ISO 8601 build timestamp
- `package_name`: Package name ('_durak_core')

### `get_resource_info() -> Dict[str, Dict[str, str]]`

Returns embedded resource metadata for all resources:

**Resource keys:**
- `stopwords_base`: Base Turkish stopwords
- `stopwords_social_media`: Social media domain stopwords
- `detached_suffixes`: Turkish detached suffixes
- `apostrophes`: Apostrophe handling rules
- `lemma_suffixes`: Lemmatization suffix rules

**Metadata fields:**
- `name`: Human-readable name
- `version`: Semantic version (e.g., '1.0.0')
- `source`: Resource origin/curation method
- `checksum`: SHA256 hash (64 hex characters)
- `item_count`: Number of items (as string)
- `last_updated`: ISO 8601 date

### `print_reproducibility_report() -> None`

Prints formatted report of build info and all resources to stdout.

### `get_bibtex_citation() -> str`

Returns BibTeX entry with exact version and resource metadata for citing Durak in papers.

## Best Practices

### ✅ DO

- **Always document Durak version** in papers and reports
- **Save reproducibility report** with experiment results
- **Check resource changelog** when upgrading versions
- **Verify checksums** when reproducing previous experiments
- **Include resource versions** in model metadata

### ❌ DON'T

- **Don't assume resources are stable** across minor versions
- **Don't skip impact assessment** when resources change
- **Don't cite "Durak" generically** — always include version
- **Don't ignore checksum mismatches** in reproduction attempts

## Related Issues

- [#25: Resource Versioning and Reproducibility Tracking](https://github.com/cdliai/durak/issues/25) (this feature)
- [#7: Token-to-Original-Text Alignment](https://github.com/cdliai/durak/issues/7) - reproducibility for NER
- [#5: Corpus Regression Tests](https://github.com/cdliai/durak/issues/5) - version tracking for tests

---

**Questions or suggestions?** Open an issue on [GitHub](https://github.com/cdliai/durak/issues).
