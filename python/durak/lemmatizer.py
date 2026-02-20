from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from time import perf_counter
from typing import Literal

from durak.exceptions import ConfigurationError, LemmatizerError, RustExtensionError


def _get_rust_function(name: str):
    """Lazy import of Rust functions to avoid circular import issues."""
    from durak import _durak_core
    
    if _durak_core is None:
        def fallback(*args, **kwargs):
            raise RustExtensionError("Rust extension not installed. Run: maturin develop")
        return fallback
    
    return getattr(_durak_core, name)


def lookup_lemma(word: str) -> str | None:
    return _get_rust_function("lookup_lemma")(word)


def strip_suffixes(word: str) -> str:
    return _get_rust_function("strip_suffixes")(word)


def strip_suffixes_validated(word: str, strict: bool = False, min_root_length: int = 2) -> str:
    return _get_rust_function("strip_suffixes_validated")(word, strict, min_root_length)

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
    """
    def __init__(
        self, 
        strategy: Strategy = "hybrid",
        validate_roots: bool = False,
        strict_validation: bool = False,
        min_root_length: int = 2,
        collect_metrics: bool = False,
    ):
        # Validate strategy
        valid_strategies = ("lookup", "heuristic", "hybrid")
        if strategy not in valid_strategies:
            raise ConfigurationError(
                f"Unknown strategy: '{strategy}'. "
                f"Valid options: {', '.join(valid_strategies)}"
            )
        
        # Validate min_root_length
        if min_root_length < 1:
            raise ConfigurationError("min_root_length must be at least 1")
        
        self.strategy = strategy
        self.validate_roots = validate_roots
        self.strict_validation = strict_validation
        self.min_root_length = min_root_length
        self.collect_metrics = collect_metrics
        self._metrics = LemmatizerMetrics() if collect_metrics else None

    def __call__(self, word: str) -> str:
        """Lemmatize a word.
        
        Args:
            word: Input word to lemmatize
            
        Returns:
            Lemmatized form of the word
            
        Raises:
            LemmatizerError: If input is not a string
            RustExtensionError: If Rust extension is not available
        """
        if not isinstance(word, str):
            raise LemmatizerError(
                f"Input must be a string, got {type(word).__name__}"
            )
        
        if not word:
            return ""
        
        try:
            return self._lemmatize(word)
        except RustExtensionError:
            raise  # Re-raise as-is
        except Exception as e:
            raise LemmatizerError(f"Lemmatization failed: {e}") from e
    
    def _lemmatize(self, word: str) -> str:
        """Internal lemmatization logic."""
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

    def get_metrics(self) -> LemmatizerMetrics:
        """Return collected metrics.
        
        Returns:
            LemmatizerMetrics: Performance metrics snapshot
            
        Raises:
            ValueError: If metrics collection is not enabled
        """
        if not self.collect_metrics:
            raise ConfigurationError(
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
            raise ConfigurationError(
                "Metrics not enabled. Initialize with collect_metrics=True."
            )
        self._metrics = LemmatizerMetrics()

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
        return f"Lemmatizer({', '.join(parts)})"
