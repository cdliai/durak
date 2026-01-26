import json
from pathlib import Path

import pytest
from durak import (
    BASE_STOPWORDS,
    DEFAULT_STOPWORD_RESOURCE,
    StopwordManager,
    StopwordSnapshot,
    is_stopword,
    list_stopwords,
    load_stopword_resource,
    load_stopwords,
    remove_stopwords,
)


def test_base_stopwords_contains_common_tokens() -> None:
    assert {"ve", "ama", "çünkü"} <= BASE_STOPWORDS


def test_base_stopwords_includes_new_suffix_variants() -> None:
    assert "öyle" in BASE_STOPWORDS
    assert remove_stopwords(["öyle", "adam"]) == ["adam"]


def test_base_stopwords_matches_resource_definition() -> None:
    resource_words = load_stopword_resource(DEFAULT_STOPWORD_RESOURCE)
    assert BASE_STOPWORDS == frozenset(resource_words)


def test_load_stopwords_normalizes_entries(tmp_path: Path) -> None:
    source = tmp_path / "custom.txt"
    source.write_text("# comment\nServis\nveri\n", encoding="utf-8")
    loaded = load_stopwords(source)
    assert loaded == {"servis", "veri"}


def test_stopword_manager_respects_keep_words() -> None:
    manager = StopwordManager(keep=["ama"])
    assert manager.is_stopword("ve")
    assert not manager.is_stopword("ama")
    assert not manager.is_stopword("Ama")


def test_stopword_manager_additions_and_file_loading(
    tmp_path: Path, data_dir: Path
) -> None:
    manager = StopwordManager(additions=["api"])
    assert manager.is_stopword("api")

    additions_path = data_dir / "extra_stopwords.txt"
    manager.load_additions(additions_path)
    assert all(manager.is_stopword(word) for word in ["uygulama", "servis", "sunucu"])


def test_case_sensitive_mode_differentiates_tokens() -> None:
    manager = StopwordManager(base=["Durak"], case_sensitive=True)
    assert manager.is_stopword("Durak")
    assert not manager.is_stopword("durak")


def test_load_stopword_resource_handles_extends() -> None:
    social_media = load_stopword_resource("domains/social_media")
    assert {"rt", "dm", "ve"} <= social_media
    assert BASE_STOPWORDS <= frozenset(social_media)


def test_export_and_snapshot_roundtrip(tmp_path: Path, data_dir: Path) -> None:
    manager = StopwordManager(additions=["veri"], keep=["ama"])
    manager.load_additions(data_dir / "extra_stopwords.txt")
    snapshot = manager.snapshot()
    assert isinstance(snapshot, StopwordSnapshot)
    assert "ama" in snapshot.keep_words

    txt_path = tmp_path / "stopwords.txt"
    json_path = tmp_path / "stopwords.json"
    manager.export(txt_path)
    manager.export(json_path, fmt="json")

    txt_contents = txt_path.read_text(encoding="utf-8").strip().splitlines()
    json_contents = json.loads(json_path.read_text(encoding="utf-8"))
    assert sorted(txt_contents) == sorted(json_contents)
    assert "ama" not in json_contents  # keep words should be excluded


def test_stopword_manager_from_resources_includes_domains() -> None:
    manager = StopwordManager.from_resources(["domains/social_media"])
    assert manager.is_stopword("rt")
    assert manager.is_stopword("ve")


def test_remove_stopwords_filters_tokens() -> None:
    tokens = ["ve", "Durak", "ama"]
    filtered = remove_stopwords(tokens)
    assert filtered == ["Durak"]


def test_legacy_resource_aliases_resolve() -> None:
    new_name = load_stopword_resource("domains/social_media")
    legacy_name = load_stopword_resource("tr/domains/social_media")
    assert legacy_name == new_name


def test_is_stopword_defaults_to_base_resource() -> None:
    assert is_stopword("ve")
    assert not is_stopword("durak")


def test_is_stopword_supports_custom_resources() -> None:
    assert is_stopword("rt", resource="domains/social_media")
    assert is_stopword("rt", resource="tr/domains/social_media")


def test_list_stopwords_returns_sorted_words() -> None:
    words = list_stopwords()
    assert words == sorted(words)
    assert {"ve", "ama", "çünkü"} <= set(words)


def test_list_stopwords_supports_alias_resources() -> None:
    words = list_stopwords(resource="tr/domains/social_media")
    assert {"rt", "dm"} <= set(words)


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).parent / "data"
