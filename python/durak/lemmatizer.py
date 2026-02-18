from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter
from typing import TYPE_CHECKING, Literal

from durak.exceptions import ConfigurationError, LemmatizerError, RustExtensionError

if TYPE_CHECKING:
    pass

try:
    from durak._durak_core import lookup_lemma, strip_suffixes, strip_suffixes_validated
except ImportError:

    def lookup_lemma(word: str) -> str | None:
        raise RustExtensionError("Rust extension not installed. Run: maturin develop")

    def strip_suffixes(word: str) -> str:
        raise RustExtensionError("Rust extension not installed. Run: maturin develop")

    def strip_suffixes_validated(
        word: str,
        strict: bool = False,
        min_root_length: int = 2,
        check_harmony: bool = True,
    ) -> str:
        raise RustExtensionError("Rust extension not installed. Run: maturin develop")


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

    total_calls: int = 0
    lookup_hits: int = 0
    lookup_misses: int = 0
    heuristic_calls: int = 0

    total_time: float = 0.0
    lookup_time: float = 0.0
    heuristic_time: float = 0.0

    cache_hit_rate: float = field(init=False)
    avg_call_time_ms: float = field(init=False)

    def __post_init__(self) -> None:
        """Compute derived metrics."""
        self.cache_hit_rate = (
            self.lookup_hits / self.total_calls if self.total_calls > 0 else 0.0
        )
        self.avg_call_time_ms = (
            (self.total_time / self.total_calls) * 1000 if self.total_calls > 0 else 0.0
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

    def to_dict(self) -> dict[str, float | int]:
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
        valid_strategies = ("lookup", "heuristic", "hybrid")
        if strategy not in valid_strategies:
            raise ConfigurationError(
                f"Unknown strategy: '{strategy}'. "
                f"Valid options: {', '.join(valid_strategies)}"
            )

        if min_root_length < 1:
            raise ConfigurationError("min_root_length must be at least 1")

        self.strategy: Strategy = strategy
        self.validate_roots: bool = validate_roots
        self.strict_validation: bool = strict_validation
        self.min_root_length: int = min_root_length
        self.collect_metrics: bool = collect_metrics
        self._metrics: LemmatizerMetrics | None = (
            LemmatizerMetrics() if collect_metrics else None
        )

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
            raise LemmatizerError(f"Input must be a string, got {type(word).__name__}")

        if not word:
            return ""

        try:
            return self._lemmatize(word)
        except RustExtensionError:
            raise
        except Exception as e:
            raise LemmatizerError(f"Lemmatization failed: {e}") from e

    def _lemmatize(self, word: str) -> str:
        """Internal lemmatization logic."""
        if not self.collect_metrics:
            return self._lemmatize_without_metrics(word)
        return self._lemmatize_with_metrics(word)

    def _lemmatize_without_metrics(self, word: str) -> str:
        """Fast path when metrics are disabled."""
        if self.strategy in ("lookup", "hybrid"):
            lemma = lookup_lemma(word)
            if lemma is not None:
                return lemma
            if self.strategy == "lookup":
                return word

        if self.strategy in ("heuristic", "hybrid"):
            if self.validate_roots:
                return strip_suffixes_validated(
                    word,
                    strict=self.strict_validation,
                    min_root_length=self.min_root_length,
                )
            return strip_suffixes(word)

        return word

    def _lemmatize_with_metrics(self, word: str) -> str:
        """Metrics-tracked lemmatization path."""
        metrics = self._metrics
        assert metrics is not None

        start_time = perf_counter()

        if self.strategy in ("lookup", "hybrid"):
            lookup_start = perf_counter()
            lemma = lookup_lemma(word)
            metrics.lookup_time += perf_counter() - lookup_start

            if lemma is not None:
                metrics.lookup_hits += 1
                metrics.total_calls += 1
                metrics.total_time += perf_counter() - start_time
                return lemma

            metrics.lookup_misses += 1

            if self.strategy == "lookup":
                metrics.total_calls += 1
                metrics.total_time += perf_counter() - start_time
                return word

        if self.strategy in ("heuristic", "hybrid"):
            heuristic_start = perf_counter()

            if self.validate_roots:
                result = strip_suffixes_validated(
                    word,
                    strict=self.strict_validation,
                    min_root_length=self.min_root_length,
                )
            else:
                result = strip_suffixes(word)

            metrics.heuristic_time += perf_counter() - heuristic_start
            metrics.heuristic_calls += 1
            metrics.total_calls += 1
            metrics.total_time += perf_counter() - start_time

            return result

        return word

    def get_metrics(self) -> LemmatizerMetrics:
        """Return collected metrics.

        Returns:
            LemmatizerMetrics: Performance metrics snapshot

        Raises:
            ConfigurationError: If metrics collection is not enabled
        """
        if self._metrics is None:
            raise ConfigurationError(
                "Metrics not enabled. Initialize with collect_metrics=True."
            )
        self._metrics.__post_init__()
        return self._metrics

    def reset_metrics(self) -> None:
        """Reset all metrics to zero.

        Useful for:
        - Benchmarking specific corpus segments
        - Measuring performance after warmup
        - Isolating evaluation phases

        Raises:
            ConfigurationError: If metrics collection is not enabled
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
