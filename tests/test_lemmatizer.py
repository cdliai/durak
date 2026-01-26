import pytest

from durak.lemmatizer import Lemmatizer


def test_tier1_lookup():
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
        
    lemmatizer = Lemmatizer(strategy="lookup")
    # "kitaplar" is in our mock dict -> "kitap"
    assert lemmatizer("kitaplar") == "kitap"
    # "unknownword" -> returns as-is in lookup mode
    assert lemmatizer("unknownword") == "unknownword"

def test_tier2_heuristic():
    try:
        from durak import _durak_core  # noqa: F401
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
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
        
    lemmatizer = Lemmatizer(strategy="hybrid")
    # "gittim" is in dict -> "git"
    assert lemmatizer("gittim") == "git"
    
    # "arabalar" not in dict -> heuristic "araba"
    assert lemmatizer("arabalar") == "araba"

def test_protection_rule():
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")

    # Heuristic shouldn't strip too much
    # "kiler" ends with "ler" but "ki" is too short (<=2 chars + suffix len?)
    # implementation has > suffix.len() + 2
    # suffix len for ler is 3. need > 5 chars total?
    # kiler is 5 chars. 5 > 5 is false. so it should NOT strip.
    lemmatizer = Lemmatizer(strategy="heuristic")
    assert lemmatizer("kiler") == "kiler"


def test_comprehensive_dictionary_nouns():
    """Test comprehensive dictionary with common Turkish nouns"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="lookup")
    
    # Test plural forms
    assert lemmatizer("evler") == "ev"
    assert lemmatizer("insanlar") == "insan"
    assert lemmatizer("çocuklar") == "çocuk"
    assert lemmatizer("kadınlar") == "kadın"
    assert lemmatizer("erkekler") == "erkek"
    
    # Test case forms (accusative, dative, locative, ablative)
    assert lemmatizer("kitabı") == "kitap"  # accusative
    assert lemmatizer("kitaba") == "kitap"  # dative
    assert lemmatizer("kitapta") == "kitap"  # locative
    assert lemmatizer("kitaptan") == "kitap"  # ablative
    
    # Test possessive forms
    assert lemmatizer("evim") == "ev"
    assert lemmatizer("evimiz") == "ev"


def test_comprehensive_dictionary_verbs():
    """Test comprehensive dictionary with common Turkish verbs"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="lookup")
    
    # Test present tense conjugations
    assert lemmatizer("geliyorum") == "gel"
    assert lemmatizer("geliyorsun") == "gel"
    assert lemmatizer("geliyor") == "gel"
    assert lemmatizer("geliyoruz") == "gel"
    
    # Test past tense
    assert lemmatizer("geldim") == "gel"
    assert lemmatizer("geldin") == "gel"
    assert lemmatizer("geldi") == "gel"
    assert lemmatizer("geldik") == "gel"
    
    # Test future tense
    assert lemmatizer("geleceğim") == "gel"
    assert lemmatizer("geleceksin") == "gel"
    assert lemmatizer("gelecek") == "gel"
    
    # Test different verbs
    assert lemmatizer("gidiyorum") == "git"
    assert lemmatizer("yapıyorum") == "yap"
    assert lemmatizer("okuyorum") == "oku"
    assert lemmatizer("yazıyorum") == "yaz"
    assert lemmatizer("görüyorum") == "gör"


def test_comprehensive_dictionary_pronouns():
    """Test comprehensive dictionary with Turkish pronouns"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="lookup")
    
    # Test personal pronouns with case markers
    assert lemmatizer("beni") == "ben"
    assert lemmatizer("bana") == "ben"
    assert lemmatizer("bende") == "ben"
    assert lemmatizer("benden") == "ben"
    
    assert lemmatizer("seni") == "sen"
    assert lemmatizer("sana") == "sen"
    
    assert lemmatizer("onu") == "o"
    assert lemmatizer("ona") == "o"
    
    # Test plural pronouns
    assert lemmatizer("bizi") == "biz"
    assert lemmatizer("bize") == "biz"
    assert lemmatizer("sizi") == "siz"
    assert lemmatizer("size") == "siz"
    
    # Test demonstratives
    assert lemmatizer("bunlar") == "bu"
    assert lemmatizer("şunlar") == "şu"


def test_dictionary_coverage():
    """Verify dictionary has significantly more entries than mock data"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="lookup")
    
    # Count successful lookups from a diverse sample
    test_words = [
        "kitaplar", "evler", "insanlar", "çocuklar",  # nouns
        "geliyorum", "gidiyorum", "yapıyorum",  # verbs
        "beni", "seni", "bunlar",  # pronouns
        "güzeller", "iyiler", "büyükler"  # adjectives
    ]
    
    successful_lookups = sum(
        1 for word in test_words 
        if lemmatizer(word) != word  # lemma found (not returned as-is)
    )
    
    # Should have high coverage (at least 80% of test samples)
    assert successful_lookups >= len(test_words) * 0.8


def test_hybrid_with_comprehensive_dict():
    """Test hybrid strategy prioritizes comprehensive dictionary"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="hybrid")
    
    # Words in dictionary should use lookup
    assert lemmatizer("geliyorum") == "gel"
    assert lemmatizer("kitapları") == "kitap"
    assert lemmatizer("evleri") == "ev"
    
    # Words not in dictionary should fall back to heuristic
    # (assuming "arabalar" is not in our dictionary)
    result = lemmatizer("arabalar")
    # Should strip -lar suffix heuristically
    assert result == "araba"
