import pytest
from durak.lemmatizer import Lemmatizer, LemmatizerMetrics


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


# ============================================================================
# Metrics Tests (Issue #63)
# ============================================================================

def test_metrics_disabled_by_default():
    """Metrics collection should be disabled by default"""
    lemmatizer = Lemmatizer()
    assert not lemmatizer.collect_metrics
    
    with pytest.raises(ValueError, match="not enabled"):
        lemmatizer.get_metrics()


def test_metrics_enabled():
    """Metrics collection can be enabled explicitly"""
    lemmatizer = Lemmatizer(collect_metrics=True)
    assert lemmatizer.collect_metrics
    
    metrics = lemmatizer.get_metrics()
    assert isinstance(metrics, LemmatizerMetrics)
    assert metrics.total_calls == 0


def test_metrics_lookup_hits():
    """Metrics should track lookup hits correctly"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="lookup", collect_metrics=True)
    
    # These words are in the dictionary
    lemmatizer("kitaplar")
    lemmatizer("evler")
    lemmatizer("geliyorum")
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 3
    assert metrics.lookup_hits == 3
    assert metrics.lookup_misses == 0
    assert metrics.heuristic_calls == 0
    assert metrics.cache_hit_rate == 1.0  # 100% hit rate


def test_metrics_lookup_misses():
    """Metrics should track lookup misses in lookup-only mode"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="lookup", collect_metrics=True)
    
    # Word not in dictionary
    lemmatizer("unknownword123")
    lemmatizer("anotherunkn own")
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 2
    assert metrics.lookup_hits == 0
    assert metrics.lookup_misses == 2
    assert metrics.heuristic_calls == 0
    assert metrics.cache_hit_rate == 0.0


def test_metrics_heuristic_only():
    """Metrics should track heuristic-only calls"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="heuristic", collect_metrics=True)
    
    lemmatizer("masalar")
    lemmatizer("arabalar")
    lemmatizer("evlerden")
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 3
    assert metrics.lookup_hits == 0
    assert metrics.lookup_misses == 0
    assert metrics.heuristic_calls == 3


def test_metrics_hybrid_strategy():
    """Metrics should track hybrid strategy (lookup + fallback)"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    # In dictionary -> lookup hit
    lemmatizer("kitaplar")
    lemmatizer("geliyorum")
    
    # Not in dictionary -> heuristic fallback
    lemmatizer("unknownword")
    lemmatizer("testleri")
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 4
    assert metrics.lookup_hits == 2
    assert metrics.lookup_misses == 2
    assert metrics.heuristic_calls == 2
    assert 0.0 < metrics.cache_hit_rate < 1.0  # Partial hit rate


def test_metrics_timing():
    """Metrics should track timing information"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    # Process some words
    for _ in range(100):
        lemmatizer("kitaplar")
        lemmatizer("unknownword")
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 200
    assert metrics.total_time > 0.0
    assert metrics.lookup_time > 0.0
    assert metrics.heuristic_time > 0.0
    assert metrics.avg_call_time_ms > 0.0


def test_metrics_reset():
    """Metrics should reset to zero"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(collect_metrics=True)
    
    lemmatizer("kitaplar")
    lemmatizer("evler")
    
    assert lemmatizer.get_metrics().total_calls == 2
    
    lemmatizer.reset_metrics()
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 0
    assert metrics.lookup_hits == 0
    assert metrics.total_time == 0.0


def test_metrics_properties():
    """Test computed properties of LemmatizerMetrics"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    # 3 hits, 2 misses (5 lookups total), 2 heuristic fallbacks
    lemmatizer("kitaplar")   # hit
    lemmatizer("evler")      # hit
    lemmatizer("geliyorum")  # hit
    lemmatizer("unknown1")   # miss -> heuristic
    lemmatizer("unknown2")   # miss -> heuristic
    
    metrics = lemmatizer.get_metrics()
    
    # Total calls = 5
    assert metrics.total_calls == 5
    
    # Cache hit rate = 3/5 = 60%
    assert abs(metrics.cache_hit_rate - 0.6) < 0.01
    
    # Lookup hit rate = 3/5 = 60%
    assert abs(metrics.lookup_hit_rate - 0.6) < 0.01
    
    # Heuristic calls = 2 (only for misses in hybrid mode)
    assert metrics.heuristic_calls == 2


def test_metrics_string_representation():
    """Test metrics __str__ method"""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(collect_metrics=True)
    lemmatizer("kitaplar")
    
    metrics_str = str(lemmatizer.get_metrics())
    assert "Lemmatizer Metrics:" in metrics_str
    assert "Total Calls:" in metrics_str
    assert "Lookup Hits:" in metrics_str
    assert "Avg Call Time:" in metrics_str


def test_repr_with_metrics():
    """Test Lemmatizer __repr__ shows metrics status"""
    lemmatizer_no_metrics = Lemmatizer()
    assert "metrics_disabled" in repr(lemmatizer_no_metrics)
    
    lemmatizer_with_metrics = Lemmatizer(collect_metrics=True)
    assert "metrics_enabled" in repr(lemmatizer_with_metrics)
