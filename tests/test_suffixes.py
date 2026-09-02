from durak.suffixes import attach_detached_suffixes


def test_attach_detached_suffixes_with_apostrophe() -> None:
    tokens = ["ankara", "'", "da"]
    assert attach_detached_suffixes(tokens) == ["ankara'da"]


def test_attach_detached_suffixes_without_apostrophe() -> None:
    tokens = ["ankara", "da", "kaldım"]
    assert attach_detached_suffixes(tokens) == ["ankarada", "kaldım"]


def test_attach_detached_suffixes_requires_alpha_base() -> None:
    tokens = ["123", "'", "da", "ankara"]
    assert attach_detached_suffixes(tokens) == ["123", "'", "da", "ankara"]


def test_attach_detached_suffixes_disable_without_apostrophe() -> None:
    tokens = ["ankara", "da"]
    assert attach_detached_suffixes(tokens, allow_without_apostrophe=False) == tokens
