#!/usr/bin/env python3
"""
Generate resource metadata for reproducibility tracking.

This script computes checksums and counts items in embedded resources,
generating a metadata.json file that's embedded in the Rust binary.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path


def compute_checksum(file_path: Path) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        sha256.update(f.read())
    return sha256.hexdigest()


def count_items(file_path: Path) -> int:
    """Count non-empty lines in a text file."""
    with open(file_path, encoding='utf-8') as f:
        return len([
            line for line in f
            if line.strip() and not line.strip().startswith('#')
        ])


def generate_metadata():
    """Generate resource metadata JSON."""
    resources_dir = Path("resources/tr")
    
    # Read Cargo.toml for version
    cargo_toml = Path("Cargo.toml")
    version = "0.1.0"  # default
    if cargo_toml.exists():
        for line in cargo_toml.read_text().splitlines():
            if line.startswith("version ="):
                version = line.split('"')[1]
                break
    
    metadata = {
        "version": version,
        "build_date": datetime.utcnow().isoformat() + "Z",
        "resources": {}
    }
    
    # Turkish Stopwords (Base)
    stopwords_base = resources_dir / "stopwords/base/turkish.txt"
    if stopwords_base.exists():
        metadata["resources"]["stopwords_base"] = {
            "name": "Turkish Stopwords (Base)",
            "version": "1.0.0",
            "source": "Curated by Durak team",
            "checksum": compute_checksum(stopwords_base),
            "item_count": count_items(stopwords_base),
            "last_updated": "2026-01-26"
        }
    
    # Turkish Stopwords (Social Media)
    stopwords_social = resources_dir / "stopwords/domains/social_media.txt"
    if stopwords_social.exists():
        metadata["resources"]["stopwords_social_media"] = {
            "name": "Turkish Stopwords (Social Media)",
            "version": "1.0.0",
            "source": "Social media corpus analysis",
            "checksum": compute_checksum(stopwords_social),
            "item_count": count_items(stopwords_social),
            "last_updated": "2026-01-26"
        }
    
    # Detached Suffixes
    suffixes = resources_dir / "labels/DETACHED_SUFFIXES.txt"
    if suffixes.exists():
        metadata["resources"]["detached_suffixes"] = {
            "name": "Turkish Detached Suffixes",
            "version": "1.0.0",
            "source": "Turkish grammar rules",
            "checksum": compute_checksum(suffixes),
            "item_count": count_items(suffixes),
            "last_updated": "2026-01-26"
        }
    
    # Apostrophes
    apostrophes = resources_dir / "config/apostrophes.txt"
    if apostrophes.exists():
        metadata["resources"]["apostrophes"] = {
            "name": "Turkish Apostrophe Rules",
            "version": "1.0.0",
            "source": "Turkish orthography standards",
            "checksum": compute_checksum(apostrophes),
            "item_count": count_items(apostrophes),
            "last_updated": "2026-01-26"
        }
    
    # Lemma Suffixes
    lemma_suffixes = resources_dir / "config/lemma_suffixes.txt"
    if lemma_suffixes.exists():
        metadata["resources"]["lemma_suffixes"] = {
            "name": "Turkish Lemmatization Suffixes",
            "version": "1.0.0",
            "source": "Turkish morphology rules",
            "checksum": compute_checksum(lemma_suffixes),
            "item_count": count_items(lemma_suffixes),
            "last_updated": "2026-01-26"
        }
    
    # Write metadata
    output_path = Path("resources/metadata.json")
    with open(output_path, "w", encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Generated metadata for {len(metadata['resources'])} resources")
    print(f"✓ Written to {output_path}")
    
    # Print summary
    print("\nResource Summary:")
    for key, info in metadata["resources"].items():
        checksum_short = info['checksum'][:12]
        print(
            f"  {key:30} {info['item_count']:4} items  "
            f"SHA256:{checksum_short}..."
        )
    
    return metadata


if __name__ == "__main__":
    generate_metadata()
