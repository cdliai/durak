import pytest
from durak import cleaning


def test_normalize_unicode_handles_typographic_variants() -> None:
    raw = "“İstanbul’da—efsane!”"
    assert cleaning.normalize_unicode(raw) == '"İstanbul\'da-efsane!"'


def test_strip_html_removes_tags_and_scripts() -> None:
    html_text = "<p>Merhaba <strong>dünya</strong></p><script>alert('x')</script>"
    assert cleaning.strip_html(html_text) == "Merhaba dünya"


def test_collapse_whitespace_trim_and_punctuation_spacing() -> None:
    text = "Merhaba   dünya \n  !"
    assert cleaning.collapse_whitespace(text) == "Merhaba dünya!"


@pytest.mark.parametrize(
    ("mode", "input_text", "expected"),
    [
        ("lower", "İSTANBUL IĞDIR", "istanbul ığdır"),
        ("upper", "istanbul ığdır", "İSTANBUL IĞDIR"),
        ("none", "İstanbul", "İstanbul"),
    ],
)
def test_normalize_case_supports_turkish_i_variants(
    mode: str, input_text: str, expected: str
) -> None:
    assert cleaning.normalize_case(input_text, mode=mode) == expected


def test_remove_urls_keeps_trailing_punctuation() -> None:
    text = "Ziyaret edin https://karagoz.io."
    assert cleaning.remove_urls(text) == "Ziyaret edin."


@pytest.mark.parametrize(
    ("keep_hash", "expected"),
    [
        (False, "Bugün ile gün!"),
        (True, "Bugün ile güzel gün!"),
    ],
)
def test_remove_mentions_hashtags_variants(keep_hash: bool, expected: str) -> None:
    text = "Bugün @fbkaragoz ile #güzel gün!"
    assert cleaning.remove_mentions_hashtags(text, keep_hash=keep_hash) == expected


def test_remove_repeated_chars_limits_long_runs() -> None:
    assert cleaning.remove_repeated_chars("Süüüperrr!!!") == "Süüperr!!"


def test_clean_text_with_default_pipeline() -> None:
    noisy = """<div>İnanılmazzz!!! @user https://example.com
    """
    assert cleaning.clean_text(noisy) == "inanılmazz!!"


def test_clean_text_custom_steps() -> None:
    text = "Merhaba\t\tDURAK"
    steps = (cleaning.collapse_whitespace, cleaning.normalize_case)
    assert cleaning.clean_text(text, steps=steps) == "merhaba durak"
