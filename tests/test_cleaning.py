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


# ==============================================================================
# EMOJI PROCESSING TESTS
# ==============================================================================


def test_remove_emojis_strips_all_emojis() -> None:
    text = "Harika! 🎉🎊 Çok güzel olmuş 😍"
    result = cleaning.remove_emojis(text)
    assert result == "Harika! Çok güzel olmuş"
    assert "🎉" not in result
    assert "🎊" not in result
    assert "😍" not in result


def test_remove_emojis_preserves_non_emoji_text() -> None:
    text = "Sade metin, emoji yok"
    assert cleaning.remove_emojis(text) == text


def test_remove_emojis_handles_empty_string() -> None:
    assert cleaning.remove_emojis("") == ""


def test_remove_emojis_collapses_whitespace() -> None:
    text = "A 🎉   🎊   B"
    result = cleaning.remove_emojis(text)
    assert result == "A B"


def test_extract_emojis_returns_list_of_emojis() -> None:
    text = "Müthiş gün! 🌞☀️🔥"
    emojis = cleaning.extract_emojis(text)
    assert emojis == ["🌞", "☀️", "🔥"]


def test_extract_emojis_empty_when_no_emojis() -> None:
    text = "Emoji yok burada"
    assert cleaning.extract_emojis(text) == []


def test_extract_emojis_preserves_duplicates() -> None:
    text = "Çok mutluyum! 😊😊😊"
    emojis = cleaning.extract_emojis(text)
    assert len(emojis) == 3
    assert all(e == "😊" for e in emojis)


def test_extract_emojis_handles_various_emoji_categories() -> None:
    text = "👍 Harika! 🚀 Gidiyor! ❤️ Seviyorum!"
    emojis = cleaning.extract_emojis(text)
    assert "👍" in emojis
    assert "🚀" in emojis
    assert "❤️" in emojis or "❤" in emojis  # Variation selector handling


@pytest.mark.parametrize(
    ("emoji_mode", "input_text", "expected"),
    [
        # Keep mode: preserve emojis
        ("keep", "Harika! 🎉", "harika! 🎉"),
        ("keep", "Emoji yok", "emoji yok"),
        # Remove mode: strip emojis
        ("remove", "Harika! 🎉", "harika!"),
        ("remove", "Çok güzel 😍🎊", "çok güzel"),
        ("remove", "Emoji yok", "emoji yok"),
    ],
)
def test_clean_text_emoji_mode_keep_and_remove(
    emoji_mode: str, input_text: str, expected: str
) -> None:
    result = cleaning.clean_text(input_text, emoji_mode=emoji_mode)
    assert result == expected


def test_clean_text_emoji_mode_extract_returns_tuple() -> None:
    text = "Harika! 🎉 Çok güzel 😍"
    result = cleaning.clean_text(text, emoji_mode="extract")

    # Should return tuple
    assert isinstance(result, tuple)
    assert len(result) == 2

    cleaned_text, emojis = result
    assert isinstance(cleaned_text, str)
    assert isinstance(emojis, list)

    # Verify cleaned text has no emojis
    assert "🎉" not in cleaned_text
    assert "😍" not in cleaned_text
    assert "harika" in cleaned_text.lower()

    # Verify emojis were extracted
    assert "🎉" in emojis
    assert "😍" in emojis


def test_clean_text_emoji_mode_extract_empty_emoji_list() -> None:
    text = "Emoji yok burada"
    cleaned_text, emojis = cleaning.clean_text(text, emoji_mode="extract")

    assert "emoji yok burada" in cleaned_text.lower()
    assert emojis == []


def test_clean_text_emoji_mode_extract_with_empty_input() -> None:
    result = cleaning.clean_text("", emoji_mode="extract")
    assert result == ("", [])


def test_clean_text_emoji_mode_invalid_raises() -> None:
    with pytest.raises(ValueError, match="emoji_mode must be"):
        cleaning.clean_text("test", emoji_mode="invalid")


def test_clean_text_emoji_mode_with_custom_steps() -> None:
    text = "HARIKA! 🎉 GÜZEL 😍"
    steps = (cleaning.normalize_case, cleaning.remove_emojis)

    # Should apply custom steps first, then emoji mode
    result = cleaning.clean_text(text, steps=steps, emoji_mode="remove")
    # Note: Turkish I normalization: HARIKA → harıka (I→ı)
    assert "harıka" in result or "harika" in result
    assert "güzel" in result
    assert "🎉" not in result
    assert "😍" not in result


def test_emoji_integration_with_social_media_cleaning() -> None:
    """Test emoji handling in realistic social media scenario."""
    tweet = """
    Harika bir gün! 🌞☀️ @arkadas ile #tatil 🏖️
    https://example.com/foto.jpg 😍😍😍
    Çok mutluyummm!!!
    """

    # Extract emojis first
    emojis = cleaning.extract_emojis(tweet)
    assert len(emojis) >= 5  # At least 5 emojis

    # Clean with emoji removal
    cleaned = cleaning.clean_text(tweet, emoji_mode="remove")
    # Note: Turkish I normalization (HARIKA → harıka)
    assert "harıka" in cleaned or "harika" in cleaned
    # Note: Default pipeline removes hashtags, so "tatil" won't be in cleaned
    # (We can test this behavior instead)
    assert "🌞" not in cleaned
    assert "😍" not in cleaned
    assert "http" not in cleaned  # URLs removed

    # Clean and extract in one go
    cleaned_with_extract, extracted_emojis = cleaning.clean_text(
        tweet, emoji_mode="extract"
    )
    assert len(extracted_emojis) >= 5
    assert "harıka" in cleaned_with_extract or "harika" in cleaned_with_extract
    assert "😍" not in cleaned_with_extract
