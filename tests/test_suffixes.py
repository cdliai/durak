from durak.suffixes import attach_detached_suffixes


def test_attach_detached_suffixes_with_apostrophe() -> None:
    tokens = ["ankara", "'", "da"]
    assert attach_detached_suffixes(tokens) == ["ankara'da"]


def test_attach_detached_suffixes_without_apostrophe_disabled_by_default() -> None:
    tokens = ["ankara", "da", "kaldım"]
    assert attach_detached_suffixes(tokens) == tokens


def test_attach_detached_suffixes_without_apostrophe_opt_in() -> None:
    tokens = ["ankara", "da", "kaldım"]
    assert attach_detached_suffixes(
        tokens,
        allow_without_apostrophe=True,
    ) == ["ankarada", "kaldım"]


def test_attach_detached_suffixes_requires_alpha_base() -> None:
    tokens = ["123", "'", "da", "ankara"]
    assert attach_detached_suffixes(tokens) == ["123", "'", "da", "ankara"]


def test_attach_detached_suffixes_does_not_merge_function_word_sequence() -> None:
    tokens = ["ben", "de", "ofisteyim"]
    assert attach_detached_suffixes(tokens, allow_without_apostrophe=True) == tokens


def test_attach_detached_suffixes_safe_mode_avoids_quote_artifact_join() -> None:
    tokens = ["ve", "'", "da", "geldi"]
    assert attach_detached_suffixes(tokens) == tokens
