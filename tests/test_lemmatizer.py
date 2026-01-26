import pytest
from durak.lemmatizer import Lemmatizer


def test_tier1_lookup():
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
        
    lemmatizer = Lemmatizer(strategy="lookup")
    # "kitaplar" is in our mock dict -> "kitap"
    assert lemmatizer("kitaplar") == "kitap"
    # "unknownword" -> returns as-is in lookup mode
    assert lemmatizer("unknownword") == "unknownword"

def test_tier2_heuristic():
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")

    lemmatizer = Lemmatizer(strategy="heuristic")
    # "masalar" -> "masa" (removes -lar)
    assert lemmatizer("masalar") == "masa"
    # "gelmeden" -> "gelme" (removes -den) -> probably "gel" in fuller implementation
    # With current naive implementation: gelmeden -> gelme
    assert lemmatizer("gelmeden").startswith("gel")

def test_hybrid_priority():
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
        
    lemmatizer = Lemmatizer(strategy="hybrid")
    # "gittim" is in dict -> "git"
    assert lemmatizer("gittim") == "git"
    
    # "arabalar" not in dict -> heuristic "araba"
    assert lemmatizer("arabalar") == "araba"

def test_protection_rule():
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")

    # Heuristic shouldn't strip too much
    # "kiler" ends with "ler" but "ki" is too short (<=2 chars + suffix len?)
    # implementation has > suffix.len() + 2
    # suffix len for ler is 3. need > 5 chars total?
    # kiler is 5 chars. 5 > 5 is false. so it should NOT strip.
    lemmatizer = Lemmatizer(strategy="heuristic")
    assert lemmatizer("kiler") == "kiler"
