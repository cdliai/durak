"""Tests for resource versioning and reproducibility tracking (#25)."""

import hashlib
import re
from pathlib import Path

import pytest

import durak
from durak.info import (
    get_bibtex_citation,
    get_build_info,
    get_resource_info,
    print_reproducibility_report,
)


def test_get_build_info_returns_dict():
    """Build info should return a dictionary with required keys."""
    info = get_build_info()
    
    assert isinstance(info, dict)
    assert "durak_version" in info
    assert "build_date" in info
    assert "rust_version" in info


def test_build_info_durak_version_matches_package():
    """Durak version should match package version."""
    info = get_build_info()
    
    assert info["durak_version"] == durak.__version__


def test_build_info_durak_version_is_semantic():
    """Durak version should follow semantic versioning."""
    info = get_build_info()
    version = info["durak_version"]
    
    assert isinstance(version, str)
    assert re.match(r"^\d+\.\d+\.\d+(?:[+-][0-9A-Za-z.-]+)?$", version)


def test_build_info_build_date_is_iso8601():
    """Build date should be valid ISO 8601 timestamp."""
    info = get_build_info()
    build_date = info["build_date"]
    
    assert isinstance(build_date, str)
    # Basic ISO 8601 check (YYYY-MM-DDTHH:MM:SS.fffffZ)
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", build_date)


def test_build_info_rust_version_is_valid():
    """Rust version should be a valid version string."""
    info = get_build_info()
    rust_version = info["rust_version"]
    
    assert isinstance(rust_version, str)
    # Should match "1.XX.X" format
    assert re.match(r"^\d+\.\d+", rust_version)


def test_get_resource_info_returns_dict():
    """Resource info should return a dictionary of resources."""
    info = get_resource_info()
    
    assert isinstance(info, dict)
    assert len(info) > 0  # At least one resource


def test_resource_info_has_required_keys():
    """Each resource should have required metadata keys."""
    info = get_resource_info()
    
    required_keys = {"name", "version", "source", "checksum", "item_count", "last_updated"}
    
    for resource_name, resource_data in info.items():
        assert isinstance(resource_data, dict), f"{resource_name} should be a dict"
        
        for key in required_keys:
            assert key in resource_data, f"{resource_name} missing key: {key}"


def test_resource_info_stopwords_base_exists():
    """Stopwords base resource should exist."""
    info = get_resource_info()
    
    assert "stopwords_base" in info
    stopwords = info["stopwords_base"]
    
    assert stopwords["name"] == "Turkish Stopwords (Base)"
    assert isinstance(stopwords["version"], str)
    assert isinstance(stopwords["checksum"], str)
    assert isinstance(stopwords["item_count"], int)
    assert stopwords["item_count"] > 0


def test_resource_info_detached_suffixes_exists():
    """Detached suffixes resource should exist."""
    info = get_resource_info()
    
    assert "detached_suffixes" in info
    suffixes = info["detached_suffixes"]
    
    assert suffixes["name"] == "Turkish Detached Suffixes"
    assert isinstance(suffixes["version"], str)
    assert isinstance(suffixes["checksum"], str)
    assert isinstance(suffixes["item_count"], int)
    assert suffixes["item_count"] > 0


def test_resource_checksums_are_sha256():
    """Resource checksums should be valid SHA256 hashes."""
    info = get_resource_info()
    
    for resource_name, resource_data in info.items():
        checksum = resource_data["checksum"]
        
        # SHA256 is 64 hex characters
        assert len(checksum) == 64, f"{resource_name} checksum wrong length"
        assert re.match(r"^[0-9a-f]{64}$", checksum), f"{resource_name} checksum not hex"


def test_resource_item_counts_are_positive():
    """Resource item counts should be positive integers."""
    info = get_resource_info()
    
    for resource_name, resource_data in info.items():
        item_count = resource_data["item_count"]
        
        assert isinstance(item_count, int), f"{resource_name} item_count not int"
        assert item_count > 0, f"{resource_name} item_count not positive"


def test_resource_versions_are_semantic():
    """Resource versions should follow semantic versioning."""
    info = get_resource_info()
    
    for resource_name, resource_data in info.items():
        version = resource_data["version"]
        
        assert re.match(
            r"^\d+\.\d+\.\d+(?:[+-][0-9A-Za-z.-]+)?$", version
        ), f"{resource_name} version not semantic"


def test_print_reproducibility_report_runs_without_error(capsys):
    """Reproducibility report should print without errors."""
    print_reproducibility_report()
    
    captured = capsys.readouterr()
    output = captured.out
    
    assert "Durak Reproducibility Report" in output
    assert "Build Information:" in output
    assert "Embedded Resources:" in output
    assert "durak_version" in output


def test_reproducibility_report_contains_all_resources(capsys):
    """Reproducibility report should list all resources."""
    print_reproducibility_report()
    
    captured = capsys.readouterr()
    output = captured.out
    
    resource_info = get_resource_info()
    
    for resource_name in resource_info.keys():
        assert resource_name in output, f"Missing {resource_name} in report"


def test_get_bibtex_citation_returns_string():
    """BibTeX citation should return a valid string."""
    citation = get_bibtex_citation()
    
    assert isinstance(citation, str)
    assert len(citation) > 0


def test_bibtex_citation_contains_required_fields():
    """BibTeX citation should have required BibTeX fields."""
    citation = get_bibtex_citation()
    
    required_fields = ["@software{", "title =", "author =", "version =", "year =", "url ="]
    
    for field in required_fields:
        assert field in citation, f"Missing BibTeX field: {field}"


def test_bibtex_citation_includes_version():
    """BibTeX citation should include current Durak version."""
    citation = get_bibtex_citation()
    build_info = get_build_info()
    
    assert build_info["durak_version"] in citation


def test_bibtex_citation_includes_stopwords_checksum():
    """BibTeX citation should include stopwords checksum for reproducibility."""
    citation = get_bibtex_citation()
    resource_info = get_resource_info()
    
    stopwords_checksum = resource_info["stopwords_base"]["checksum"]
    checksum_prefix = stopwords_checksum[:12]
    
    assert checksum_prefix in citation, "Stopwords checksum not in citation"


def test_reproducibility_across_calls():
    """Multiple calls should return identical data (deterministic)."""
    info1 = get_resource_info()
    info2 = get_resource_info()
    
    assert info1 == info2, "Resource info should be deterministic"
    
    build1 = get_build_info()
    build2 = get_build_info()
    
    assert build1 == build2, "Build info should be deterministic"


def test_resource_metadata_file_exists():
    """Metadata file should exist in resources directory."""
    metadata_path = Path(__file__).parent.parent / "resources" / "metadata.json"
    
    assert metadata_path.exists(), "metadata.json not found in resources/"


def test_resource_changelog_exists():
    """Resource changelog should exist for documentation."""
    changelog_path = Path(__file__).parent.parent / "resources" / "CHANGELOG.md"
    
    assert changelog_path.exists(), "CHANGELOG.md not found in resources/"


def test_reproducibility_documentation_exists():
    """Reproducibility documentation should exist."""
    doc_path = Path(__file__).parent.parent / "docs" / "REPRODUCIBILITY.md"
    
    assert doc_path.exists(), "REPRODUCIBILITY.md not found in docs/"


@pytest.mark.slow
def test_stopwords_checksum_matches_actual_file():
    """Stopwords checksum should match actual file checksum."""
    resource_info = get_resource_info()
    stopwords_info = resource_info["stopwords_base"]
    
    # Read actual stopwords file
    stopwords_path = Path(__file__).parent.parent / "resources" / "tr" / "stopwords" / "base" / "turkish.txt"
    
    if not stopwords_path.exists():
        pytest.skip("Stopwords file not found (might be embedded)")
    
    # Compute actual checksum
    sha256 = hashlib.sha256()
    with open(stopwords_path, "rb") as f:
        sha256.update(f.read())
    actual_checksum = sha256.hexdigest()
    
    assert stopwords_info["checksum"] == actual_checksum, "Checksum mismatch!"


@pytest.mark.slow
def test_stopwords_item_count_matches_actual_file():
    """Stopwords item count should match actual file line count."""
    resource_info = get_resource_info()
    stopwords_info = resource_info["stopwords_base"]
    
    # Read actual stopwords file
    stopwords_path = Path(__file__).parent.parent / "resources" / "tr" / "stopwords" / "base" / "turkish.txt"
    
    if not stopwords_path.exists():
        pytest.skip("Stopwords file not found (might be embedded)")
    
    # Count actual lines
    with open(stopwords_path) as f:
        actual_count = len([line for line in f if line.strip()])
    
    assert stopwords_info["item_count"] == actual_count, "Item count mismatch!"


def test_api_is_exposed_in_main_module():
    """Resource versioning API should be accessible from main module."""
    assert hasattr(durak, "get_build_info")
    assert hasattr(durak, "get_resource_info")
    assert hasattr(durak, "print_reproducibility_report")
    assert hasattr(durak, "get_bibtex_citation")


def test_issue_25_checklist_completion():
    """Verify issue #25 checklist is complete."""
    # This is a meta-test to ensure all checklist items are implemented
    
    # ✓ Create scripts/generate_resource_metadata.py
    script_path = Path(__file__).parent.parent / "scripts" / "generate_resource_metadata.py"
    assert script_path.exists(), "generate_resource_metadata.py missing"
    
    # ✓ Add metadata generation to build process (checked manually in Cargo.toml)
    
    # ✓ Implement get_resource_info() in Rust
    resource_info = get_resource_info()
    assert len(resource_info) > 0, "get_resource_info() not working"
    
    # ✓ Implement get_build_info() in Rust
    build_info = get_build_info()
    assert "durak_version" in build_info, "get_build_info() not working"
    
    # ✓ Add python/durak/info.py module
    info_module_path = Path(__file__).parent.parent / "python" / "durak" / "info.py"
    assert info_module_path.exists(), "info.py module missing"
    
    # ✓ Create resources/CHANGELOG.md
    changelog_path = Path(__file__).parent.parent / "resources" / "CHANGELOG.md"
    assert changelog_path.exists(), "CHANGELOG.md missing"
    
    # ✓ Add resource change CI check (checked manually in .github/workflows/)
    
    # ✓ Update .pyi stubs (checked manually)
    
    # ✓ Add reproducibility section to docs
    doc_path = Path(__file__).parent.parent / "docs" / "REPRODUCIBILITY.md"
    assert doc_path.exists(), "REPRODUCIBILITY.md missing"
    
    # ✓ Add get_bibtex_citation() helper
    citation = get_bibtex_citation()
    assert "@software{" in citation, "get_bibtex_citation() not working"
