"""Tests for LemmatizerMetrics performance tracking."""

import pytest
from durak.exceptions import ConfigurationError
from durak.lemmatizer import Lemmatizer, LemmatizerMetrics


def test_metrics_disabled_by_default():
    """Metrics should be disabled by default (zero overhead)."""
    lemmatizer = Lemmatizer(strategy="hybrid")
    assert not lemmatizer.collect_metrics
    assert lemmatizer._metrics is None


def test_metrics_raises_when_disabled():
    """Should raise ConfigurationError when accessing metrics if not enabled."""
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=False)
    
    with pytest.raises(ConfigurationError, match="Metrics not enabled"):
        lemmatizer.get_metrics()
    
    with pytest.raises(ConfigurationError, match="Metrics not enabled"):
        lemmatizer.reset_metrics()


def test_metrics_basic_tracking():
    """Test basic metrics collection for lookup hits."""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="lookup", collect_metrics=True)
    
    # Initial state
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 0
    assert metrics.lookup_hits == 0
    assert metrics.lookup_misses == 0
    
    # Process a known word (in dictionary)
    lemmatizer("kitaplar")  # Should hit dictionary
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 1
    assert metrics.lookup_hits == 1
    assert metrics.lookup_misses == 0
    assert metrics.heuristic_calls == 0


def test_metrics_lookup_miss():
    """Test metrics track lookup misses correctly."""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="lookup", collect_metrics=True)
    
    # Process unknown word (not in dictionary)
    lemmatizer("unknownxyzword")
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 1
    assert metrics.lookup_hits == 0
    assert metrics.lookup_misses == 1
    assert metrics.heuristic_calls == 0


def test_metrics_heuristic_strategy():
    """Test metrics for heuristic-only strategy."""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="heuristic", collect_metrics=True)
    
    # Process words (should use heuristic)
    lemmatizer("masalar")
    lemmatizer("arabalar")
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 2
    assert metrics.heuristic_calls == 2
    assert metrics.lookup_hits == 0  # Lookup not used in heuristic mode


def test_metrics_hybrid_fallback():
    """Test metrics track hybrid strategy fallback correctly."""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    # Known word (should hit dictionary)
    lemmatizer("kitaplar")
    
    # Unknown word (should fall back to heuristic)
    # Use a word unlikely to be in dictionary
    lemmatizer("unknownxyzwordlar")
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 2
    assert metrics.lookup_hits == 1  # First word
    assert metrics.lookup_misses == 1  # Second word missed
    assert metrics.heuristic_calls == 1  # Second word used heuristic


def test_metrics_cache_hit_rate():
    """Test cache hit rate calculation."""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    # Process mix of known and unknown words
    words = ["kitaplar", "evler", "unknownword1", "geliyorum", "unknownword2"]
    for word in words:
        lemmatizer(word)
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 5
    # kitaplar, evler, geliyorum should hit (3/5 = 60%)
    assert metrics.cache_hit_rate == pytest.approx(0.6, rel=0.01)


def test_metrics_timing():
    """Test that timing metrics are collected."""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    # Process words - mix of lookup hits and heuristic fallbacks
    for _ in range(100):
        lemmatizer("kitaplar")  # Known word
        lemmatizer("unknownxyzwordlar")  # Unknown word
    
    metrics = lemmatizer.get_metrics()
    
    # Timing should be positive
    assert metrics.total_time > 0
    assert metrics.lookup_time > 0
    assert metrics.heuristic_time > 0
    
    # Average call time should be reasonable (<1ms per call typically)
    assert metrics.avg_call_time_ms > 0
    assert metrics.avg_call_time_ms < 10  # Sanity check


def test_metrics_reset():
    """Test metrics reset functionality."""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    # Process some words
    lemmatizer("kitaplar")
    lemmatizer("evler")
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 2
    
    # Reset
    lemmatizer.reset_metrics()
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 0
    assert metrics.lookup_hits == 0
    assert metrics.total_time == 0.0


def test_metrics_to_dict():
    """Test metrics export to dictionary."""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    # Process words
    lemmatizer("kitaplar")  # Known word
    lemmatizer("unknownxyzwordlar")  # Unknown word
    
    metrics = lemmatizer.get_metrics()
    metrics_dict = metrics.to_dict()
    
    # Check all keys present
    assert "total_calls" in metrics_dict
    assert "lookup_hits" in metrics_dict
    assert "lookup_misses" in metrics_dict
    assert "heuristic_calls" in metrics_dict
    assert "cache_hit_rate" in metrics_dict
    assert "avg_call_time_ms" in metrics_dict
    assert "total_time" in metrics_dict
    assert "lookup_time" in metrics_dict
    assert "heuristic_time" in metrics_dict
    
    # Check values
    assert metrics_dict["total_calls"] == 2
    assert metrics_dict["lookup_hits"] == 1
    assert metrics_dict["heuristic_calls"] == 1


def test_metrics_str_format():
    """Test metrics string formatting."""
    try:
        from durak import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    # Process words
    lemmatizer("kitaplar")  # Known word
    lemmatizer("unknownxyzwordlar")  # Unknown word
    
    metrics = lemmatizer.get_metrics()
    metrics_str = str(metrics)
    
    # Check formatting includes key info
    assert "Total Calls: 2" in metrics_str
    assert "Lookup Hits: 1" in metrics_str
    assert "Heuristic Fallbacks: 1" in metrics_str
    assert "Avg Call Time:" in metrics_str


def test_metrics_empty_input():
    """Test metrics handle empty string correctly."""
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    # Empty strings should return early (not counted)
    result = lemmatizer("")
    assert result == ""
    
    metrics = lemmatizer.get_metrics()
    assert metrics.total_calls == 0  # Should not increment


def test_metrics_repr():
    """Test Lemmatizer repr includes collect_metrics."""
    lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
    
    repr_str = repr(lemmatizer)
    assert "collect_metrics=True" in repr_str


def test_metrics_no_overhead_when_disabled():
    """Verify metrics=False has minimal overhead."""
    try:
        from durak import _durak_core  # noqa: F401
        import time
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    # Benchmark without metrics
    lemmatizer_fast = Lemmatizer(strategy="hybrid", collect_metrics=False)
    start = time.perf_counter()
    for _ in range(1000):
        lemmatizer_fast("kitaplar")
    time_without = time.perf_counter() - start
    
    # Benchmark with metrics
    lemmatizer_slow = Lemmatizer(strategy="hybrid", collect_metrics=True)
    start = time.perf_counter()
    for _ in range(1000):
        lemmatizer_slow("kitaplar")
    time_with = time.perf_counter() - start
    
    # Overhead should be reasonable (typically 10-50%, max 200%)
    overhead = (time_with - time_without) / time_without
    # Main point: metrics don't 10x slow things down
    assert overhead < 2.0  # Less than 200% overhead (3x slower max)
