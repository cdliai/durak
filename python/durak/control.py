"""Backend control layer for high-level system orchestration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

from durak.exceptions import ConfigurationError, NormalizerError, RustExtensionError
from durak.lemmatizer import Lemmatizer
from durak.normalizer import Normalizer
from durak.tokenizer import RUST_TOKENIZER_AVAILABLE, tokenize, tokenize_with_offsets

BackendName = Literal["auto", "rust", "python"]
ResolvedBackendName = Literal["rust", "python"]


@dataclass(frozen=True)
class BackendCapabilities:
    """Capability declaration for a backend."""

    available: bool
    normalize: bool
    tokenize: bool
    tokenize_with_offsets: bool
    lemmatize: bool
    embedded_resources: bool


_BACKEND_CAPABILITY_MATRIX: dict[ResolvedBackendName, BackendCapabilities] = {
    "rust": BackendCapabilities(
        available=RUST_TOKENIZER_AVAILABLE,
        normalize=True,
        tokenize=True,
        tokenize_with_offsets=True,
        lemmatize=True,
        embedded_resources=True,
    ),
    "python": BackendCapabilities(
        available=True,
        normalize=True,
        tokenize=True,
        tokenize_with_offsets=False,
        lemmatize=False,
        embedded_resources=False,
    ),
}


def resolve_backend(requested: BackendName = "auto") -> ResolvedBackendName:
    """Resolve requested backend to an executable backend name."""
    if requested == "auto":
        return "rust" if RUST_TOKENIZER_AVAILABLE else "python"

    if requested == "rust" and not RUST_TOKENIZER_AVAILABLE:
        raise RustExtensionError(
            "Rust backend requested but extension is not installed. "
            "Use backend='python' or install Rust extension via `maturin develop`."
        )

    return requested


def capability_matrix() -> dict[str, dict[str, bool]]:
    """Return backend capabilities as JSON-serializable dictionaries."""
    return {name: asdict(caps) for name, caps in _BACKEND_CAPABILITY_MATRIX.items()}


def _normalize_python(text: str, *, lowercase: bool, handle_turkish_i: bool) -> str:
    if not isinstance(text, str):
        raise NormalizerError(f"Input must be a string, got {type(text).__name__}")

    if not text:
        return ""

    chars: list[str] = []
    for ch in text:
        if handle_turkish_i and ch == "İ":
            mapped = "i"
        elif handle_turkish_i and ch == "I":
            mapped = "ı"
        else:
            mapped = ch

        if lowercase:
            chars.append(mapped.lower())
        else:
            chars.append(mapped)
    return "".join(chars)


class DurakController:
    """High-level backend controller for system-level orchestration."""

    def __init__(self, backend: BackendName = "auto") -> None:
        self.requested_backend: BackendName = backend
        self.backend: ResolvedBackendName = resolve_backend(backend)

    @property
    def capabilities(self) -> BackendCapabilities:
        return _BACKEND_CAPABILITY_MATRIX[self.backend]

    @staticmethod
    def capability_matrix() -> dict[str, dict[str, bool]]:
        return capability_matrix()

    def normalize(
        self,
        text: str,
        *,
        lowercase: bool = True,
        handle_turkish_i: bool = True,
    ) -> str:
        if self.backend == "rust":
            return Normalizer(
                lowercase=lowercase,
                handle_turkish_i=handle_turkish_i,
            )(text)
        return _normalize_python(
            text,
            lowercase=lowercase,
            handle_turkish_i=handle_turkish_i,
        )

    def tokenize(
        self,
        text: str,
        *,
        strip_punct: bool = False,
        with_offsets: bool = False,
    ) -> list[str] | list[tuple[str, int, int]]:
        if with_offsets:
            if self.backend != "rust":
                raise ConfigurationError(
                    "Offset tokenization is only available with backend='rust'."
                )
            return tokenize_with_offsets(text)

        strategy = "rust" if self.backend == "rust" else "regex"
        return tokenize(text, strategy=strategy, strip_punct=strip_punct)

    def lemmatize(
        self,
        word: str,
        *,
        strategy: Literal["lookup", "heuristic", "hybrid"] = "hybrid",
    ) -> str:
        if self.backend != "rust":
            raise ConfigurationError(
                "Lemmatization currently requires backend='rust'. "
                "Use backend='rust' or keep backend='auto' with Rust extension installed."
            )
        return Lemmatizer(strategy=strategy)(word)


__all__ = [
    "BackendCapabilities",
    "BackendName",
    "DurakController",
    "ResolvedBackendName",
    "capability_matrix",
    "resolve_backend",
]
