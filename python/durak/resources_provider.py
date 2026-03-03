"""Centralized resource loading utilities for Python-side modules."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from durak.exceptions import ResourceError

from .core.interfaces import ResourceProviderLike

RESOURCE_DIR = Path(__file__).resolve().parent.parent.parent / "resources" / "tr"
STOPWORDS_DIR = RESOURCE_DIR / "stopwords"
STOPWORDS_METADATA_PATH = STOPWORDS_DIR / "metadata.json"
DETACHED_SUFFIXES_PATH = RESOURCE_DIR / "labels" / "DETACHED_SUFFIXES.txt"
APOSTROPHES_PATH = RESOURCE_DIR / "config" / "apostrophes.txt"

try:
    from . import _durak_core
except ImportError:
    _durak_core = None  # type: ignore[assignment]


@dataclass(frozen=True)
class DefaultResourceProvider(ResourceProviderLike):
    """Primary resource provider with Rust-backed fast path and file fallback."""

    detached_suffixes_path: Path = DETACHED_SUFFIXES_PATH
    stopwords_metadata_path: Path = STOPWORDS_METADATA_PATH
    apostrophes_path: Path = APOSTROPHES_PATH

    def load_detached_suffixes(self) -> tuple[str, ...]:
        if _durak_core is not None:
            try:
                return tuple(_durak_core.get_detached_suffixes())
            except Exception:
                # Fall back to file-based loading if extension call fails.
                pass
        return _read_lines(self.detached_suffixes_path, skip_comments=False)

    def load_stopwords_metadata_text(self) -> str:
        if _durak_core is not None:
            try:
                return _durak_core.get_stopwords_metadata()
            except Exception:
                # Fall back to file-based loading if extension call fails.
                pass
        try:
            return self.stopwords_metadata_path.read_text(encoding="utf-8")
        except FileNotFoundError as exc:
            raise ResourceError(
                "durak stopword metadata file is missing from "
                f"{self.stopwords_metadata_path.parent}."
            ) from exc

    def load_apostrophes(self) -> tuple[str, ...]:
        tokens = _read_lines(self.apostrophes_path, skip_comments=True)
        # Keep stable order while removing accidental duplicates.
        return tuple(dict.fromkeys(tokens))


def _read_lines(path: Path, *, skip_comments: bool) -> tuple[str, ...]:
    try:
        raw = path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ResourceError(f"durak resource file is missing: {path}") from exc

    lines: list[str] = []
    for line in raw.splitlines():
        value = line.strip()
        if not value:
            continue
        if skip_comments and value.startswith("#"):
            continue
        lines.append(value)
    return tuple(lines)


DEFAULT_RESOURCE_PROVIDER = DefaultResourceProvider()

__all__ = [
    "DEFAULT_RESOURCE_PROVIDER",
    "APOSTROPHES_PATH",
    "DETACHED_SUFFIXES_PATH",
    "RESOURCE_DIR",
    "STOPWORDS_DIR",
    "STOPWORDS_METADATA_PATH",
    "DefaultResourceProvider",
]
