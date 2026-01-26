"""
Durak Reproducibility & Build Information API

This module provides functions to query embedded resource versions, checksums,
and build metadata for research reproducibility and provenance tracking.

Example:
    >>> from durak import get_build_info, get_resource_info, print_reproducibility_report
    >>> 
    >>> # Get Durak version and build date
    >>> build = get_build_info()
    >>> print(build['durak_version'])
    '0.4.0'
    >>> 
    >>> # Get resource versions and checksums
    >>> resources = get_resource_info()
    >>> print(resources['stopwords_base']['item_count'])
    '118'
    >>> 
    >>> # Print full reproducibility report
    >>> print_reproducibility_report()
"""

from typing import Dict
from . import _durak_core


def get_build_info() -> Dict[str, str]:
    """Get Durak build information for reproducibility.
    
    Returns build metadata including package version, build date, and
    package name. This information can be used to document exact Durak
    versions in research papers and experiment logs.
    
    Returns:
        dict: Build metadata with keys:
            - durak_version: Semantic version (e.g., '0.4.0')
            - build_date: ISO 8601 timestamp of build
            - package_name: Package name ('_durak_core')
    
    Example:
        >>> from durak import get_build_info
        >>> info = get_build_info()
        >>> print(f"Durak v{info['durak_version']}")
        Durak v0.4.0
        >>> print(f"Built: {info['build_date']}")
        Built: 2026-01-26T08:30:51.849239Z
    """
    return _durak_core.get_build_info()


def get_resource_info() -> Dict[str, Dict[str, str]]:
    """Get embedded resource versions and checksums.
    
    Returns metadata for all linguistic resources embedded in the Durak binary,
    including stopwords, suffixes, and morphology rules. Each resource includes:
    - Version (semantic versioning)
    - SHA256 checksum (for exact matching)
    - Item count (number of words/rules)
    - Source and last update date
    
    This is critical for:
    - Research reproducibility (exact resource versions in papers)
    - Debugging (which stopword list was used?)
    - Impact assessment (how did resource changes affect results?)
    - Regulatory compliance (data provenance tracking)
    
    Returns:
        dict: Mapping of resource names to metadata dicts.
            Resource names: stopwords_base, stopwords_social_media,
                          detached_suffixes, apostrophes, lemma_suffixes
            
            Each metadata dict contains:
            - name: Human-readable name
            - version: Semantic version (e.g., '1.0.0')
            - source: Where the resource came from
            - checksum: SHA256 hash (64 hex chars)
            - item_count: Number of items (as string)
            - last_updated: ISO 8601 date
    
    Example:
        >>> from durak import get_resource_info
        >>> resources = get_resource_info()
        >>> 
        >>> # Check stopwords version
        >>> sw = resources['stopwords_base']
        >>> print(f"{sw['name']}: v{sw['version']}")
        Turkish Stopwords (Base): v1.0.0
        >>> print(f"Items: {sw['item_count']}, Checksum: {sw['checksum'][:12]}...")
        Items: 118, Checksum: 361908bbb0a4...
        >>> 
        >>> # Verify reproducibility
        >>> expected_checksum = '361908bbb0a44efc7dcb2dfb600d13a64d3982623701bd4057e0af69ca6d0b04'
        >>> assert resources['stopwords_base']['checksum'] == expected_checksum
    """
    return _durak_core.get_resource_info()


def print_reproducibility_report() -> None:
    """Print full reproducibility report.
    
    Outputs a formatted report of Durak build information and all embedded
    resource versions. Use this to document preprocessing configuration in
    papers, experiment logs, or production deployment records.
    
    The report includes:
    - Durak version and build date
    - All embedded resources with versions, checksums, and item counts
    
    Example:
        >>> from durak import print_reproducibility_report
        >>> print_reproducibility_report()
        
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
    """
    build_info = get_build_info()
    resource_info = get_resource_info()
    
    print()
    print("=" * 52)
    print("Durak Reproducibility Report")
    print("=" * 52)
    
    print("\nBuild Information:")
    print("-" * 50)
    for key, value in sorted(build_info.items()):
        print(f"  {key:20}: {value}")
    
    print("\nEmbedded Resources:")
    print("-" * 50)
    
    for resource_name in sorted(resource_info.keys()):
        info = resource_info[resource_name]
        print(f"\n{resource_name}:")
        for key, value in sorted(info.items()):
            # Truncate checksum for readability
            if key == 'checksum' and len(value) > 20:
                display_value = value[:16] + "..."
            else:
                display_value = value
            print(f"  {key:20}: {display_value}")
    
    print()


def get_bibtex_citation() -> str:
    """Get BibTeX citation with exact version information.
    
    Generates a BibTeX entry for citing Durak in academic papers,
    including the exact version and resource metadata for reproducibility.
    
    Returns:
        str: BibTeX entry with version and resource information
    
    Example:
        >>> from durak import get_bibtex_citation
        >>> print(get_bibtex_citation())
        @software{durak2026,
          title = {Durak: Turkish NLP Toolkit},
          author = {Karagöz, Fatih Burak},
          version = {0.4.0},
          year = {2026},
          url = {https://github.com/cdliai/durak},
          note = {Stopwords v1.0.0 (118 items, SHA256: 361908bbb0a4...)}
        }
        
        >>> # Save to file for experiment documentation
        >>> with open("preprocessing_metadata.bib", "w") as f:
        ...     f.write(get_bibtex_citation())
    """
    from datetime import datetime
    
    build_info = get_build_info()
    resource_info = get_resource_info()
    
    # Get stopwords info for the citation note
    stopwords = resource_info.get('stopwords_base', {})
    version = build_info.get('durak_version', '0.0.0')
    year = datetime.now().year
    
    return f"""@software{{durak{year},
  title = {{Durak: Turkish NLP Toolkit}},
  author = {{Karagöz, Fatih Burak}},
  version = {{{version}}},
  year = {{{year}}},
  url = {{https://github.com/cdliai/durak}},
  note = {{Stopwords v{stopwords.get('version', '1.0.0')} ({stopwords.get('item_count', '0')} items, SHA256: {stopwords.get('checksum', '')[:12]}...)}}
}}"""


__all__ = [
    'get_build_info',
    'get_resource_info',
    'print_reproducibility_report',
    'get_bibtex_citation',
]
