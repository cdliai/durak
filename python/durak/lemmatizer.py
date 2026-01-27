from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter
from typing import Literal

try:
    from durak._durak_core import lookup_lemma, strip_suffixes
except ImportError:
    def lookup_lemma(word: str) -> str | None:
        raise ImportError("Rust extension not installed")
    def strip_suffixes(word: str) -> str:
        raise ImportError("Rust extension not installed")

Strategy = Literal["lookup", "heuristic", "hybrid"]


@dataclass
class LemmatizerMetrics:
    """Performance metrics for lemmatization strategies."""
    
    # Call counts
    total_calls: int = 0
    lookup_hits: int = 0
    lookup_misses: int = 0
    heuristic_calls: int = 0
    
    # Timing (in seconds)
    total_time: float = 0.0
    lookup_time: float = 0.0
    heuristic_time: float = 0.0
    
    @property
    def cache_hit_rate(self) -> float:
        """Percentage of lookups that hit the dictionary."""
        return (self.lookup_hits / self.total_calls) if self.total_calls > 0 else 0.0
    
    @property
    def avg_call_time_ms(self) -> float:
        """Average time per call in milliseconds."""
        if self.total_calls > 0:
            return (self.total_time / self.total_calls * 1000)
        return 0.0
    
    @property
    def lookup_hit_rate(self) -> float:
        """Percentage of lookup attempts that found a match."""
        total_lookups = self.lookup_hits + self.lookup_misses
        return (self.lookup_hits / total_lookups) if total_lookups > 0 else 0.0
    
    def __str__(self) -> str:
        return f"""Lemmatizer Metrics:
  Total Calls:         {self.total_calls:,}
  Lookup Hits:         {self.lookup_hits:,} ({self.cache_hit_rate:.1%} of all calls)
  Lookup Hit Rate:     {self.lookup_hit_rate:.1%}
  Heuristic Fallbacks: {self.heuristic_calls:,}
  Avg Call Time:       {self.avg_call_time_ms:.3f}ms
  Total Time:          {self.total_time:.3f}s
  Lookup Time:         {self.lookup_time:.3f}s
  Heuristic Time:      {self.heuristic_time:.3f}s"""


class Lemmatizer:
    """
    Tiered Lemmatizer backed by Rust.
    
    Strategies:
    - lookup: Use only the exact dictionary 
      (fastest, high precision, low recall on OOV).
    - heuristic: Use only suffix stripping (fast, works on OOV, lower precision).
    - hybrid: Try lookup first, fallback to heuristic (default).
    
    Args:
        strategy: Lemmatization strategy to use.
        collect_metrics: Enable performance metrics collection (default: False).
    
    Example:
        >>> lemmatizer = Lemmatizer(strategy="hybrid", collect_metrics=True)
        >>> for word in corpus:
        ...     lemma = lemmatizer(word)
        >>> print(lemmatizer.get_metrics())
    """
    
    def __init__(
        self,
        strategy: Strategy = "hybrid",
        collect_metrics: bool = False,
    ):
        self.strategy = strategy
        self.collect_metrics = collect_metrics
        self._metrics = LemmatizerMetrics() if collect_metrics else None

    def __call__(self, word: str) -> str:
        if not word:
            return ""
        
        start_time = perf_counter() if self.collect_metrics else None
        
        # Tier 1: Lookup
        if self.strategy in ("lookup", "hybrid"):
            lookup_start = perf_counter() if self.collect_metrics else None
            lemma = lookup_lemma(word)
            
            if self._metrics is not None:
                self._metrics.lookup_time += perf_counter() - lookup_start
            
            if lemma is not None:
                if self._metrics is not None:
                    self._metrics.lookup_hits += 1
                    self._metrics.total_calls += 1
                    self._metrics.total_time += perf_counter() - start_time
                return lemma
            
            if self._metrics is not None:
                self._metrics.lookup_misses += 1
            
            if self.strategy == "lookup":
                if self._metrics is not None:
                    self._metrics.total_calls += 1
                    self._metrics.total_time += perf_counter() - start_time
                return word  # Return as-is if not found
        
        # Tier 2: Heuristic
        if self.strategy in ("heuristic", "hybrid"):
            heuristic_start = perf_counter() if self.collect_metrics else None
            result = strip_suffixes(word)
            
            if self._metrics is not None:
                self._metrics.heuristic_time += perf_counter() - heuristic_start
                self._metrics.heuristic_calls += 1
                self._metrics.total_calls += 1
                self._metrics.total_time += perf_counter() - start_time
            
            return result
        
        return word

    def get_metrics(self) -> LemmatizerMetrics:
        """
        Return collected performance metrics.
        
        Returns:
            LemmatizerMetrics object with call counts and timing data.
        
        Raises:
            ValueError: If metrics collection is not enabled.
        
        Example:
            >>> lemmatizer = Lemmatizer(collect_metrics=True)
            >>> lemmatizer("kitaplar")
            >>> metrics = lemmatizer.get_metrics()
            >>> print(f"Hit rate: {metrics.cache_hit_rate:.1%}")
        """
        if not self.collect_metrics:
            raise ValueError(
                "Metrics collection not enabled. "
                "Initialize with collect_metrics=True."
            )
        return self._metrics
    
    def reset_metrics(self) -> None:
        """
        Reset all metrics to zero.
        
        Example:
            >>> lemmatizer.reset_metrics()
            >>> lemmatizer.get_metrics().total_calls
            0
        """
        if self._metrics is not None:
            self._metrics = LemmatizerMetrics()

    def __repr__(self) -> str:
        status = "metrics_enabled" if self.collect_metrics else "metrics_disabled"
        return f"Lemmatizer(strategy='{self.strategy}', {status})"
