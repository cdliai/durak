"""Stopword utilities for Durak."""

from __future__ import annotations

import json
from collections.abc import Iterable, MutableSet, Sequence
from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import Any, cast

from durak.cleaning import normalize_case

STOPWORD_DATA_DIR = Path(__file__).resolve().parent / "data" / "stopwords"
DEFAULT_STOPWORD_RESOURCE = "base/turkish"
STOPWORD_METADATA_PATH = STOPWORD_DATA_DIR / "metadata.json"

__all__ = [
    "BASE_STOPWORDS",
    "DEFAULT_STOPWORD_RESOURCE",
    "STOPWORD_METADATA_PATH",
    "StopwordMetadataError",
    "StopwordManager",
    "StopwordSnapshot",
    "load_stopword_resource",
    "load_stopword_resources",
    "load_stopwords",
    "is_stopword",
    "list_stopwords",
    "remove_stopwords",
]


class StopwordMetadataError(RuntimeError):
    """Raised when stopword metadata is missing or malformed."""


def _resolve_metadata_path(metadata_path: Path | str | None) -> Path:
    if metadata_path is None:
        return STOPWORD_METADATA_PATH
    return Path(metadata_path)


@cache
def _read_stopword_metadata(resolved_metadata_path: str) -> dict[str, Any]:
    metadata_path = Path(resolved_metadata_path)
    try:
        raw = metadata_path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise StopwordMetadataError(
            f"Stopword metadata file not found at '{metadata_path}'."
        ) from exc
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise StopwordMetadataError(
            f"Stopword metadata at '{metadata_path}' is not valid JSON."
        ) from exc
    if not isinstance(data, dict):
        raise StopwordMetadataError("Stopword metadata must be a JSON object.")
    sets = data.get("sets")
    if not isinstance(sets, dict) or not sets:
        raise StopwordMetadataError("Stopword metadata 'sets' must be a non-empty map.")
    return data


def _resolve_resource_path(relative_path: str, *, base_dir: Path) -> Path:
    if not relative_path or not isinstance(relative_path, str):
        raise StopwordMetadataError("Stopword resource entry is missing its 'file'.")
    candidate = (base_dir / relative_path).resolve()
    base_dir_resolved = base_dir.resolve()
    try:
        candidate.relative_to(base_dir_resolved)
    except ValueError as exc:
        raise StopwordMetadataError(
            f"Stopword resource path '{relative_path}' escapes the data directory."
        ) from exc
    if not candidate.is_file():
        raise StopwordMetadataError(
            f"Stopword resource file '{relative_path}' not found under '{base_dir}'."
        )
    return candidate


def _ensure_sequence(value: Any, *, field: str) -> Sequence[str]:
    if value is None:
        return ()
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, Sequence):
        raise StopwordMetadataError(
            f"Stopword resource '{field}' must be a sequence of strings."
        )
    if not all(isinstance(item, str) for item in value):
        raise StopwordMetadataError(
            f"Stopword resource '{field}' must only contain strings."
        )
    return cast(Sequence[str], value)


def _collect_resource_words(
    resource_name: str,
    *,
    sets: dict[str, Any],
    base_dir: Path,
    case_sensitive: bool,
    stack: set[str],
    cache: dict[str, frozenset[str]],
) -> frozenset[str]:
    if resource_name in cache:
        return cache[resource_name]
    if resource_name in stack:
        cycle = " -> ".join((*stack, resource_name))
        raise StopwordMetadataError(
            f"Circular stopword resource extends chain: {cycle}"
        )
    try:
        entry: dict[str, Any] = sets[resource_name]
    except KeyError as exc:
        raise StopwordMetadataError(
            f"Unknown stopword resource '{resource_name}'."
        ) from exc

    alias_target = entry.get("alias")
    if alias_target is not None and not isinstance(alias_target, str):
        raise StopwordMetadataError("Stopword resource 'alias' must be a string.")

    stack.add(resource_name)
    try:
        if alias_target:
            if not alias_target.strip():
                raise StopwordMetadataError(
                    f"Stopword resource '{resource_name}' alias cannot be empty."
                )
            invalid_fields = set(entry) - {"alias", "description"}
            if invalid_fields:
                fields = ", ".join(sorted(invalid_fields))
                raise StopwordMetadataError(
                    "Stopword alias "
                    f"'{resource_name}' cannot define additional fields: {fields}."
                )
            aliased_words = _collect_resource_words(
                alias_target,
                sets=sets,
                base_dir=base_dir,
                case_sensitive=case_sensitive,
                stack=stack,
                cache=cache,
            )
            cache[resource_name] = aliased_words
            return aliased_words

        words: set[str] = set()
        extends = _ensure_sequence(entry.get("extends"), field="extends")
        for parent in extends:
            parent_words = _collect_resource_words(
                parent,
                sets=sets,
                base_dir=base_dir,
                case_sensitive=case_sensitive,
                stack=stack,
                cache=cache,
            )
            words.update(parent_words)
        file_path = _resolve_resource_path(entry.get("file", ""), base_dir=base_dir)
        words.update(load_stopwords(file_path, case_sensitive=case_sensitive))
    finally:
        stack.remove(resource_name)

    frozen = frozenset(words)
    cache[resource_name] = frozen
    return frozen


@cache
def _load_stopword_resource_cached(
    resolved_metadata_path: str, resource_name: str, case_sensitive: bool
) -> frozenset[str]:
    metadata = _read_stopword_metadata(resolved_metadata_path)
    sets = metadata["sets"]
    if not isinstance(sets, dict):
        raise StopwordMetadataError("Stopword metadata 'sets' must be a mapping.")
    base_dir = Path(resolved_metadata_path).parent
    cache: dict[str, frozenset[str]] = {}
    words = _collect_resource_words(
        resource_name,
        sets=sets,
        base_dir=base_dir,
        case_sensitive=case_sensitive,
        stack=set(),
        cache=cache,
    )
    return words


def load_stopword_resource(
    resource_name: str,
    *,
    metadata_path: Path | str | None = None,
    case_sensitive: bool = False,
) -> set[str]:
    """Load a stopword resource defined in metadata, applying inheritance.
    Args:
        resource_name: The name of the stopword resource to load.
        metadata_path: The path to the stopword metadata file. Defaults to
            the path of the default metadata file.
        case_sensitive: Whether to treat stopwords as case-sensitive.
            Defaults to False.
    Returns:
        A set of stopwords.
    """
    metadata = _resolve_metadata_path(metadata_path).resolve()
    words = _load_stopword_resource_cached(
        str(metadata),
        resource_name,
        case_sensitive,
    )
    return set(words)


def load_stopword_resources(
    resource_names: Iterable[str],
    *,
    metadata_path: Path | str | None = None,
    case_sensitive: bool = False,
) -> set[str]:
    """Load and merge multiple stopword resources.
    Args:
        resource_names: An iterable of stopword resource names to load.
        metadata_path: The path to the stopword metadata file. Defaults to
            the path of the default metadata file.
        case_sensitive: Whether to treat stopwords as case-sensitive.
            Defaults to False.
    Returns:
        A set of merged stopwords.
    """
    merged: set[str] = set()
    for name in resource_names:
        merged.update(
            load_stopword_resource(
                name,
                metadata_path=metadata_path,
                case_sensitive=case_sensitive,
            )
        )
    return merged


def _normalize(token: str, *, case_sensitive: bool) -> str:
    return token if case_sensitive else normalize_case(token, mode="lower")


def load_stopwords(path: Path | str, *, case_sensitive: bool = False) -> set[str]:
    """Load newline-delimited stopwords from a file.
    Args:
        path: The path to the stopword file.
        case_sensitive: Whether to treat stopwords as case-sensitive.
            Defaults to False.
    Returns:
        A set of stopwords.
    """
    entries: set[str] = set()
    raw_text = Path(path).read_text(encoding="utf-8")
    for line in raw_text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        entries.add(_normalize(stripped, case_sensitive=case_sensitive))
    return entries


BASE_STOPWORDS: frozenset[str] = frozenset(
    load_stopword_resource(DEFAULT_STOPWORD_RESOURCE, case_sensitive=False)
)


def remove_stopwords(
    tokens: Iterable[str] | None,
    *,
    manager: StopwordManager | None = None,
    base: Iterable[str] | None = None,
    additions: Iterable[str] | None = None,
    keep: Iterable[str] | None = None,
    case_sensitive: bool | None = None,
) -> list[str]:
    """Return tokens that are not stopwords.
    Args:
        tokens: The tokens to filter.
        manager: A `StopwordManager` instance to use.
        base: The base set of stopwords to use.
        additions: A set of stopwords to add to the base set.
        keep: A set of words to keep, even if they are in the stopword list.
        case_sensitive: Whether to treat stopwords as case-sensitive.
    Returns:
        A list of tokens with stopwords removed.
    Raises:
        ValueError: If a manager is provided along with base, additions, or
            keep, or if case_sensitive is provided and does not match the
            manager's case_sensitive setting.
    Examples:
        >>> remove_stopwords(["bu", "bir", "test"])
        ['test']
    """
    if tokens is None:
        return []
    if manager is None:
        resolved_case_sensitive = (
            case_sensitive if case_sensitive is not None else False
        )
        resolved_base = base if base is not None else BASE_STOPWORDS
        manager = StopwordManager(
            base=resolved_base,
            additions=additions,
            keep=keep,
            case_sensitive=resolved_case_sensitive,
        )
    else:
        if case_sensitive is not None and case_sensitive != manager.case_sensitive:
            raise ValueError(
                "Provided case_sensitive does not match the supplied manager."
            )
        if base is not None or additions is not None or keep is not None:
            raise ValueError(
                "Cannot provide base/additions/keep when a manager instance is "
                "supplied."
            )

    filtered: list[str] = []
    for token in tokens:
        if not manager.is_stopword(token):
            filtered.append(token)
    return filtered


def _resolve_stopword_set(
    resource: str | Iterable[str] | None,
    *,
    metadata_path: Path | str | None,
    case_sensitive: bool,
) -> frozenset[str]:
    if resource is None:
        if case_sensitive:
            words = load_stopword_resource(
                DEFAULT_STOPWORD_RESOURCE,
                metadata_path=metadata_path,
                case_sensitive=case_sensitive,
            )
            return frozenset(words)
        return BASE_STOPWORDS

    if isinstance(resource, str):
        words = load_stopword_resource(
            resource,
            metadata_path=metadata_path,
            case_sensitive=case_sensitive,
        )
    else:
        words = load_stopword_resources(
            resource,
            metadata_path=metadata_path,
            case_sensitive=case_sensitive,
        )
    return frozenset(words)


def is_stopword(
    token: str | None,
    *,
    resource: str | Iterable[str] | None = None,
    metadata_path: Path | str | None = None,
    case_sensitive: bool = False,
) -> bool:
    """Return True if the token is present in the selected stopword set.
    Args:
        token: The token to check.
        resource: The stopword resource to use. Defaults to the base resource.
        metadata_path: The path to the stopword metadata file. Defaults to
            the path of the default metadata file.
        case_sensitive: Whether to treat stopwords as case-sensitive.
            Defaults to False.
    Returns:
        True if the token is a stopword, False otherwise.
    Examples:
        >>> is_stopword("ve")
        True
        >>> is_stopword("durak")
        False
    """
    if token is None:
        return False
    normalized = _normalize(token, case_sensitive=case_sensitive)
    if not normalized:
        return False
    words = _resolve_stopword_set(
        resource,
        metadata_path=metadata_path,
        case_sensitive=case_sensitive,
    )
    return normalized in words


def list_stopwords(
    *,
    resource: str | Iterable[str] | None = None,
    metadata_path: Path | str | None = None,
    case_sensitive: bool = False,
    sort: bool = True,
) -> list[str]:
    """Return the stopword list for the selected resource(s).
    Args:
        resource: The stopword resource to use. Defaults to the base resource.
        metadata_path: The path to the stopword metadata file. Defaults to
            the path of the default metadata file.
        case_sensitive: Whether to treat stopwords as case-sensitive.
            Defaults to False.
        sort: Whether to sort the returned list of stopwords. Defaults to
            True.
    Returns:
        A list of stopwords.
    Examples:
        >>> list_stopwords()[:3]
        ['acaba', 'ama', 'aslında']
    """
    words = _resolve_stopword_set(
        resource,
        metadata_path=metadata_path,
        case_sensitive=case_sensitive,
    )
    return sorted(words) if sort else list(words)


@dataclass(frozen=True)
class StopwordSnapshot:
    """A snapshot of the state of a `StopwordManager`.
    Attributes:
        stopwords: A frozenset of the stopwords.
        keep_words: A frozenset of the words to keep.
        case_sensitive: Whether the stopword manager is case-sensitive.
    """

    stopwords: frozenset[str]
    keep_words: frozenset[str]
    case_sensitive: bool


class StopwordManager:
    """Manage stopword sets with extension and keep-list support.
    Args:
        base: The base set of stopwords to use.
        additions: A set of stopwords to add to the base set.
        keep: A set of words to keep, even if they are in the stopword list.
        case_sensitive: Whether to treat stopwords as case-sensitive.
    """

    def __init__(
        self,
        *,
        base: Iterable[str] | None = None,
        additions: Iterable[str] | None = None,
        keep: Iterable[str] | None = None,
        case_sensitive: bool = False,
    ) -> None:
        self.case_sensitive = case_sensitive
        base_words = set(base) if base is not None else set(BASE_STOPWORDS)
        normalized_base = {
            _normalize(word, case_sensitive=case_sensitive) for word in base_words
        }
        self._stopwords: MutableSet[str] = set(normalized_base)
        self._keep_words: MutableSet[str] = set()
        if additions:
            self.add(additions)
        if keep:
            self.add_keep_words(keep)

    @property
    def stopwords(self) -> frozenset[str]:
        """The current set of stopwords."""
        return frozenset(self._stopwords)

    @property
    def keep_words(self) -> frozenset[str]:
        """The current set of words to keep."""
        return frozenset(self._keep_words)

    def snapshot(self) -> StopwordSnapshot:
        """Return a snapshot of the current state of the manager."""
        return StopwordSnapshot(self.stopwords, self.keep_words, self.case_sensitive)

    def is_stopword(self, token: str | None) -> bool:
        """Return True if the token is a stopword.
        Args:
            token: The token to check.
        Returns:
            True if the token is a stopword, False otherwise.
        """
        if token is None:
            return False
        normalized = _normalize(token, case_sensitive=self.case_sensitive)
        if normalized in self._keep_words:
            return False
        return normalized in self._stopwords

    def add(self, words: Iterable[str]) -> None:
        """Add words to the stopword list.
        Args:
            words: An iterable of words to add.
        """
        for word in words:
            normalized = _normalize(word, case_sensitive=self.case_sensitive)
            if normalized and normalized not in self._keep_words:
                self._stopwords.add(normalized)

    def remove(self, words: Iterable[str]) -> None:
        """Remove words from the stopword list.
        Args:
            words: An iterable of words to remove.
        """
        for word in words:
            normalized = _normalize(word, case_sensitive=self.case_sensitive)
            self._stopwords.discard(normalized)

    def add_keep_words(self, words: Iterable[str]) -> None:
        """Add words to the keep list.
        Args:
            words: An iterable of words to add to the keep list.
        """
        for word in words:
            normalized = _normalize(word, case_sensitive=self.case_sensitive)
            if normalized:
                self._keep_words.add(normalized)
                self._stopwords.discard(normalized)

    def load_additions(self, path: Path | str) -> None:
        """Load stopwords from a file and add them to the stopword list.
        Args:
            path: The path to the file containing the stopwords.
        """
        self.add(load_stopwords(path, case_sensitive=self.case_sensitive))

    def export(self, path: Path | str, *, fmt: str = "txt") -> None:
        """Export the stopword list to a file.
        Args:
            path: The path to the file to export the stopwords to.
            fmt: The format to export the stopwords in. Can be "txt" or "json".
                Defaults to "txt".
        Raises:
            ValueError: If an unsupported format is provided.
        """
        dest = Path(path)
        words = sorted(self.stopwords)
        if fmt == "txt":
            dest.write_text("\n".join(words) + "\n", encoding="utf-8")
        elif fmt == "json":
            dest.write_text(
                json.dumps(words, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        else:
            raise ValueError("Unsupported fmt; use 'txt' or 'json'.")

    def to_dict(self) -> dict[str, object]:
        """Return a dictionary representation of the stopword manager."""
        return {
            "stopwords": sorted(self.stopwords),
            "keep_words": sorted(self.keep_words),
            "case_sensitive": self.case_sensitive,
        }

    @classmethod
    def from_files(
        cls,
        *,
        additions: Iterable[Path | str] = (),
        keep: Iterable[Path | str] = (),
        case_sensitive: bool = False,
    ) -> StopwordManager:
        """Create a `StopwordManager` from files.
        Args:
            additions: An iterable of paths to files containing stopwords to
                add.
            keep: An iterable of paths to files containing words to keep.
            case_sensitive: Whether to treat stopwords as case-sensitive.
                Defaults to False.
        Returns:
            A `StopwordManager` instance.
        """
        manager = cls(case_sensitive=case_sensitive)
        for addition_path in additions:
            manager.load_additions(addition_path)
        for keep_path in keep:
            keep_words = load_stopwords(keep_path, case_sensitive=case_sensitive)
            manager.add_keep_words(keep_words)
        return manager

    @classmethod
    def from_resources(
        cls,
        resource_names: Iterable[str] | None = None,
        *,
        metadata_path: Path | str | None = None,
        additions: Iterable[str] | None = None,
        keep: Iterable[str] | None = None,
        case_sensitive: bool = False,
    ) -> StopwordManager:
        """Factory that loads base words from metadata-defined resources.
        Args:
            resource_names: An iterable of stopword resource names to load.
            metadata_path: The path to the stopword metadata file. Defaults to
                the path of the default metadata file.
            additions: A set of stopwords to add to the base set.
            keep: A set of words to keep, even if they are in the stopword list.
            case_sensitive: Whether to treat stopwords as case-sensitive.
                Defaults to False.
        Returns:
            A `StopwordManager` instance.
        """
        names = (
            tuple(resource_names)
            if resource_names
            else (DEFAULT_STOPWORD_RESOURCE,)
        )
        base_words = load_stopword_resources(
            names,
            metadata_path=metadata_path,
            case_sensitive=case_sensitive,
        )
        return cls(
            base=base_words,
            additions=additions,
            keep=keep,
            case_sensitive=case_sensitive,
        )
