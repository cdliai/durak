from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from time import perf_counter
from typing import Literal

try:
    from durak._durak_core import lookup_lemma, strip_suffixes, strip_suffixes_validated
except ImportError:
    def lookup_lemma(word: str) -> str | None:
        raise ImportError("Rust extension not installed")
    def strip_suffixes(word: str) -> str:
        raise ImportError("Rust extension not installed")
    def strip_suffixes_validated(word: str, strict: bool = False, min_root_length: int = 2) -> str:
        raise ImportError("Rust extension not installed")

Strategy = Literal["lookup", "heuristic", "hybrid"]


@dataclass
class LemmatizerMetrics:
    """Performance metrics for lemmatization strategies.
    
    Tracks call counts, timing, and cache efficiency to enable:
    - Data-driven strategy selection
    - Performance debugging
    - Research reproducibility
    - Production monitoring
    
    Attributes:
        total_calls: Total number of lemmatization calls
        lookup_hits: Number of successful dictionary lookups
        lookup_misses: Number of failed dictionary lookups
        heuristic_calls: Number of heuristic suffix stripping calls
        total_time: Total time spent in lemmatization (seconds)
        lookup_time: Time spent in dictionary lookup (seconds)
        heuristic_time: Time spent in heuristic processing (seconds)
        cache_hit_rate: Percentage of successful lookups (0.0-1.0)
        avg_call_time_ms: Average time per call in milliseconds
    """
    
    # Call counts
    total_calls: int = 0
    lookup_hits: int = 0
    lookup_misses: int = 0
    heuristic_calls: int = 0
    
    # Timing (in seconds)
    total_time: float = 0.0
    lookup_time: float = 0.0
    heuristic_time: float = 0.0
    
    # Computed metrics
    cache_hit_rate: float = field(init=False)
    avg_call_time_ms: float = field(init=False)
    
    def __post_init__(self):
        """Compute derived metrics."""
        self.cache_hit_rate = (
            self.lookup_hits / self.total_calls 
            if self.total_calls > 0 else 0.0
        )
        self.avg_call_time_ms = (
            (self.total_time / self.total_calls) * 1000 
            if self.total_calls > 0 else 0.0
        )
    
    def __str__(self) -> str:
        """Human-readable metrics summary."""
        return f"""
Lemmatizer Metrics:
  Total Calls: {self.total_calls:,}
  Lookup Hits: {self.lookup_hits:,} ({self.cache_hit_rate:.1%})
  Lookup Misses: {self.lookup_misses:,}
  Heuristic Fallbacks: {self.heuristic_calls:,}
  Avg Call Time: {self.avg_call_time_ms:.3f}ms
  Lookup Time: {self.lookup_time:.3f}s
  Heuristic Time: {self.heuristic_time:.3f}s
        """.strip()
    
    def to_dict(self) -> dict[str, float]:
        """Export metrics as dictionary for logging/analysis."""
        return {
            "total_calls": self.total_calls,
            "lookup_hits": self.lookup_hits,
            "lookup_misses": self.lookup_misses,
            "heuristic_calls": self.heuristic_calls,
            "cache_hit_rate": self.cache_hit_rate,
            "avg_call_time_ms": self.avg_call_time_ms,
            "total_time": self.total_time,
            "lookup_time": self.lookup_time,
            "heuristic_time": self.heuristic_time,
        }

class Lemmatizer:
    """
    Tiered Lemmatizer backed by Rust.
    
    Strategies:
    - lookup: Use only the exact dictionary 
      (fastest, high precision, low recall on OOV).
    - heuristic: Use only suffix stripping (fast, works on OOV, lower precision).
    - hybrid: Try lookup first, fallback to heuristic (default).
    
    Args:
        strategy: Lemmatization strategy (lookup, heuristic, hybrid)
        validate_roots: Enable root validity checking for heuristic mode
        strict_validation: Require roots to be in lemma dictionary
        min_root_length: Minimum acceptable root length (characters)
        collect_metrics: Enable performance metrics collection (adds ~5-10% overhead)
        cache_size: LRU cache size for repeated words (0=disabled, default=10_000)
    """
    def __init__(
        self, 
        strategy: Strategy = "hybrid",
        validate_roots: bool = False,
        strict_validation: bool = False,
        min_root_length: int = 2,
        collect_metrics: bool = False,
        cache_size: int = 10_000,
    ):
        self.strategy = strategy
        self.validate_roots = validate_roots
        self.strict_validation = strict_validation
        self.min_root_length = min_root_length
        self.collect_metrics = collect_metrics
        self.cache_size = cache_size
        self._metrics = LemmatizerMetrics() if collect_metrics else None
        
        # Setup LRU cache if enabled
        if cache_size > 0:
            self._cached_call = lru_cache(maxsize=cache_size)(self._raw_call)
        else:
            self._cached_call = self._raw_call

    def _raw_call(self, word: str) -> str:
        """Core lemmatization logic (bypasses cache)."""
        start_time = perf_counter() if self.collect_metrics else None
            
        # Tier 1: Lookup
        if self.strategy in ("lookup", "hybrid"):
            lookup_start = perf_counter() if self.collect_metrics else None
            lemma = lookup_lemma(word)
            
            if self.collect_metrics:
                self._metrics.lookup_time += perf_counter() - lookup_start
            
            if lemma is not None:
                if self.collect_metrics:
                    self._metrics.lookup_hits += 1
                    self._metrics.total_calls += 1
                    self._metrics.total_time += perf_counter() - start_time
                return lemma
            
            if self.collect_metrics:
                self._metrics.lookup_misses += 1
            
            if self.strategy == "lookup":
                if self.collect_metrics:
                    self._metrics.total_calls += 1
                    self._metrics.total_time += perf_counter() - start_time
                return word  # Return as-is if not found

        # Tier 2: Heuristic (with optional root validation)
        if self.strategy in ("heuristic", "hybrid"):
            heuristic_start = perf_counter() if self.collect_metrics else None
            
            if self.validate_roots:
                result = strip_suffixes_validated(
                    word,
                    strict=self.strict_validation,
                    min_root_length=self.min_root_length,
                )
            else:
                result = strip_suffixes(word)
            
            if self.collect_metrics:
                self._metrics.heuristic_time += perf_counter() - heuristic_start
                self._metrics.heuristic_calls += 1
                self._metrics.total_calls += 1
                self._metrics.total_time += perf_counter() - start_time
            
            return result
            
        return word

    def __call__(self, word: str) -> str:
        """Lemmatize a word (with LRU caching if enabled)."""
        if not word:
            return ""
        return self._cached_call(word)

    def get_metrics(self) -> LemmatizerMetrics:
        """Return collected metrics.
        
        Returns:
            LemmatizerMetrics: Performance metrics snapshot
            
        Raises:
            ValueError: If metrics collection is not enabled
        """
        if not self.collect_metrics:
            raise ValueError(
                "Metrics not enabled. Initialize with collect_metrics=True."
            )
        # Recompute derived metrics before returning
        self._metrics.__post_init__()
        return self._metrics
    
    def reset_metrics(self) -> None:
        """Reset all metrics to zero.
        
        Useful for:
        - Benchmarking specific corpus segments
        - Measuring performance after warmup
        - Isolating evaluation phases
        
        Raises:
            ValueError: If metrics collection is not enabled
        """
        if not self.collect_metrics:
            raise ValueError(
                "Metrics not enabled. Initialize with collect_metrics=True."
            )
        self._metrics = LemmatizerMetrics()

    def get_cache_info(self):
        """Return LRU cache statistics if caching is enabled.
        
        Returns:
            CacheInfo: Named tuple with hits, misses, maxsize, currsize
            None: If caching is disabled (cache_size=0)
        
        Example:
            >>> lemmatizer = Lemmatizer(cache_size=1000)
            >>> for word in ["kitap", "kitaplar", "kitap"]:
            ...     lemmatizer(word)
            >>> info = lemmatizer.get_cache_info()
            >>> print(f"Cache hit rate: {info.hits / (info.hits + info.misses):.2%}")
        """
        if self.cache_size > 0:
            return self._cached_call.cache_info()
        return None

    def clear_cache(self) -> None:
        """Clear the LRU cache if caching is enabled.
        
        Useful for:
        - Benchmarking without cache warmup
        - Measuring cold-start performance
        - Memory management in long-running processes
        
        Example:
            >>> lemmatizer = Lemmatizer(cache_size=1000)
            >>> lemmatizer("kitaplar")  # Cache miss
            >>> lemmatizer("kitaplar")  # Cache hit
            >>> lemmatizer.clear_cache()
            >>> lemmatizer("kitaplar")  # Cache miss again
        """
        if self.cache_size > 0:
            self._cached_call.cache_clear()

    def __repr__(self) -> str:
        parts = [f"strategy='{self.strategy}'"]
        if self.validate_roots:
            parts.append("validate_roots=True")
            if self.strict_validation:
                parts.append("strict_validation=True")
            if self.min_root_length != 2:
                parts.append(f"min_root_length={self.min_root_length}")
        if self.collect_metrics:
            parts.append("collect_metrics=True")
        if self.cache_size != 10_000:  # Only show if non-default
            parts.append(f"cache_size={self.cache_size}")
        return f"Lemmatizer({', '.join(parts)})"
