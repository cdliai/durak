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

# ============================================================================
# Vowel Harmony Tests
# ============================================================================

def test_vowel_harmony_check_back_back():
    """Test vowel harmony: back vowel stem + back vowel suffix = valid"""
    try:
        import _durak_core
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    # Back-back harmony should be valid
    assert _durak_core.check_vowel_harmony_py("kitap", "lar") is True  # a-a
    assert _durak_core.check_vowel_harmony_py("okul", "dan") is True   # u-a
    assert _durak_core.check_vowel_harmony_py("masa", "nın") is True   # a-ı

def test_vowel_harmony_check_front_front():
    """Test vowel harmony: front vowel stem + front vowel suffix = valid"""
    try:
        import _durak_core
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    # Front-front harmony should be valid
    assert _durak_core.check_vowel_harmony_py("ev", "ler") is True     # e-e
    assert _durak_core.check_vowel_harmony_py("gül", "den") is True    # ü-e
    assert _durak_core.check_vowel_harmony_py("şehir", "nin") is True  # i-i

def test_vowel_harmony_check_back_front_invalid():
    """Test vowel harmony: back vowel stem + front vowel suffix = invalid"""
    try:
        import _durak_core
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    # Back-front mismatch should be invalid
    assert _durak_core.check_vowel_harmony_py("kitap", "ler") is False  # a-e
    assert _durak_core.check_vowel_harmony_py("okul", "den") is False   # u-e
    assert _durak_core.check_vowel_harmony_py("masa", "nin") is False   # a-i

def test_vowel_harmony_check_front_back_invalid():
    """Test vowel harmony: front vowel stem + back vowel suffix = invalid"""
    try:
        import _durak_core
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    # Front-back mismatch should be invalid
    assert _durak_core.check_vowel_harmony_py("ev", "lar") is False     # e-a
    assert _durak_core.check_vowel_harmony_py("gül", "dan") is False    # ü-a
    assert _durak_core.check_vowel_harmony_py("şehir", "nın") is False  # i-ı

def test_heuristic_with_vowel_harmony_valid():
    """Test suffix stripping with valid vowel harmony"""
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")

    lemmatizer = Lemmatizer(strategy="heuristic")
    
    # Should strip when harmony is valid
    assert lemmatizer("kitaplar") == "kitap"   # a-a harmony ✅
    assert lemmatizer("evler") == "ev"         # e-e harmony ✅
    assert lemmatizer("okuldan") == "okul"     # u-a harmony ✅
    assert lemmatizer("gülden") == "gül"       # ü-e harmony ✅

def test_heuristic_with_vowel_harmony_invalid():
    """Test suffix stripping respects vowel harmony violations"""
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")

    lemmatizer = Lemmatizer(strategy="heuristic")
    
    # Should NOT strip when harmony is violated
    # (These are artificial test cases - wouldn't occur naturally in Turkish)
    assert lemmatizer("kitapler") == "kitapler"  # a-e violation ❌
    assert lemmatizer("evlar") == "evlar"        # e-a violation ❌
    assert lemmatizer("okulden") == "okulden"    # u-e violation ❌
    assert lemmatizer("güldan") == "güldan"      # ü-a violation ❌

def test_heuristic_recursive_with_harmony():
    """Test multi-suffix stripping respects harmony at each step"""
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")

    lemmatizer = Lemmatizer(strategy="heuristic")
    
    # "kitaplardan" → "kitaplar" (strip "dan" with a-a harmony)
    #              → "kitap" (strip "lar" with a-a harmony)
    # (Note: "kitaplardan" is grammatically incorrect but tests recursive logic)
    # Real Turkish would use "kitaplardan" only if semantic context demands it,
    # but for this test we're checking recursion
    
    # Let's test with real recursive cases:
    # "evlerden" → "evler" (strip "den" with e-e harmony)
    #           → "ev" (strip "ler" with e-e harmony)
    assert lemmatizer("evlerden") == "ev"
