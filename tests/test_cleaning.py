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


# ==============================================================================
# EMOJI SENTIMENT MAPPING TESTS
# ==============================================================================


def test_map_emoji_sentiment_label_format() -> None:
    text = "Harika! 😊🔥"
    result = cleaning.map_emoji_sentiment(text, format="label")
    assert "[HAPPY]" in result
    assert "[HOT]" in result
    assert "harika" in result.lower()


def test_map_emoji_sentiment_polarity_format() -> None:
    text = "Üzgünüm 😢"
    result = cleaning.map_emoji_sentiment(text, format="polarity")
    assert "[NEGATIVE]" in result
    assert "üzgünüm" in result.lower()


def test_map_emoji_sentiment_unknown_preserve() -> None:
    text = "Test 🦄"  # Unicorn emoji not in sentiment dictionary
    result = cleaning.map_emoji_sentiment(text, unknown="preserve")
    assert "🦄" in result


def test_map_emoji_sentiment_unknown_remove() -> None:
    text = "Test 🦄"
    result = cleaning.map_emoji_sentiment(text, unknown="remove")
    assert "🦄" not in result
    assert "test" in result.lower()


def test_map_emoji_sentiment_unknown_neutral() -> None:
    text = "Test 🦄"
    result = cleaning.map_emoji_sentiment(text, unknown="neutral")
    assert "[NEUTRAL]" in result
    assert "🦄" not in result


def test_map_emoji_sentiment_mixed_known_unknown() -> None:
    text = "Harika 😊 ve garip 🦄"
    result = cleaning.map_emoji_sentiment(text, format="label", unknown="neutral")
    assert "[HAPPY]" in result
    assert "[NEUTRAL]" in result


def test_map_emoji_sentiment_empty_string() -> None:
    assert cleaning.map_emoji_sentiment("") == ""


def test_map_emoji_sentiment_no_emojis() -> None:
    text = "Emoji yok"
    result = cleaning.map_emoji_sentiment(text)
    assert result == text


def test_map_emoji_sentiment_multiple_same_emoji() -> None:
    text = "Çok mutlu 😊😊😊"
    result = cleaning.map_emoji_sentiment(text, format="label")
    assert result.count("[HAPPY]") == 3


def test_map_emoji_sentiment_invalid_format_raises() -> None:
    with pytest.raises(ValueError, match="format must be"):
        cleaning.map_emoji_sentiment("test 😊", format="invalid")


def test_map_emoji_sentiment_invalid_unknown_raises() -> None:
    with pytest.raises(ValueError, match="unknown must be"):
        cleaning.map_emoji_sentiment("test 😊", unknown="invalid")


def test_extract_emoji_sentiment_returns_tuple() -> None:
    text = "Test 😊😢"
    emojis, sentiments = cleaning.extract_emoji_sentiment(text)
    
    assert isinstance(emojis, list)
    assert isinstance(sentiments, list)
    assert len(emojis) == 2
    assert len(sentiments) == 2


def test_extract_emoji_sentiment_known_emoji() -> None:
    text = "Happy 😊"
    emojis, sentiments = cleaning.extract_emoji_sentiment(text)
    
    assert emojis == ["😊"]
    assert len(sentiments) == 1
    
    sentiment = sentiments[0]
    assert sentiment["polarity"] == "positive"
    assert sentiment["label"] == "HAPPY"
    assert 0 <= sentiment["intensity"] <= 1


def test_extract_emoji_sentiment_unknown_emoji() -> None:
    text = "Unknown 🦄"
    emojis, sentiments = cleaning.extract_emoji_sentiment(text)
    
    assert emojis == ["🦄"]
    assert len(sentiments) == 1
    
    sentiment = sentiments[0]
    assert sentiment["polarity"] == "neutral"
    assert sentiment["label"] == "UNKNOWN"
    assert sentiment["intensity"] == 0.5


def test_extract_emoji_sentiment_mixed_emojis() -> None:
    text = "Mix 😊😢🦄"
    emojis, sentiments = cleaning.extract_emoji_sentiment(text)
    
    assert len(emojis) == 3
    assert len(sentiments) == 3
    
    # First emoji (😊) should be positive
    assert sentiments[0]["polarity"] == "positive"
    
    # Second emoji (😢) should be negative
    assert sentiments[1]["polarity"] == "negative"
    
    # Third emoji (🦄) should be unknown/neutral
    assert sentiments[2]["label"] == "UNKNOWN"


def test_extract_emoji_sentiment_empty_string() -> None:
    emojis, sentiments = cleaning.extract_emoji_sentiment("")
    assert emojis == []
    assert sentiments == []


def test_clean_text_emoji_mode_sentiment() -> None:
    text = "Harika! 😊🔥"
    result = cleaning.clean_text(text, emoji_mode="sentiment")
    
    assert isinstance(result, str)
    assert "[HAPPY]" in result
    assert "[HOT]" in result
    assert "harıka" in result or "harika" in result


def test_clean_text_emoji_mode_sentiment_with_format() -> None:
    text = "Üzgünüm 😢"
    result = cleaning.clean_text(
        text,
        emoji_mode="sentiment",
        sentiment_format="polarity",
    )
    
    assert "[NEGATIVE]" in result


def test_clean_text_emoji_mode_sentiment_with_unknown() -> None:
    text = "Test 😊 🦄"
    result = cleaning.clean_text(
        text,
        emoji_mode="sentiment",
        sentiment_unknown="neutral",
    )
    
    assert "[HAPPY]" in result
    assert "[NEUTRAL]" in result
    assert "🦄" not in result


def test_clean_text_emoji_mode_sentiment_extract_returns_tuple() -> None:
    text = "Harika! 😊🔥"
    result = cleaning.clean_text(text, emoji_mode="sentiment_extract")
    
    assert isinstance(result, tuple)
    assert len(result) == 2
    
    cleaned_text, sentiment_data = result
    assert isinstance(cleaned_text, str)
    assert isinstance(sentiment_data, list)
    
    # Verify cleaned text has no emojis
    assert "😊" not in cleaned_text
    assert "🔥" not in cleaned_text
    
    # Verify sentiment data
    assert len(sentiment_data) == 2
    assert sentiment_data[0]["label"] == "HAPPY"
    assert sentiment_data[1]["label"] == "HOT"


def test_clean_text_emoji_mode_sentiment_extract_empty() -> None:
    result = cleaning.clean_text("", emoji_mode="sentiment_extract")
    assert result == ("", [])


def test_clean_text_emoji_mode_sentiment_extract_no_emojis() -> None:
    text = "Emoji yok"
    cleaned_text, sentiment_data = cleaning.clean_text(text, emoji_mode="sentiment_extract")
    
    assert "emoji yok" in cleaned_text.lower()
    assert sentiment_data == []


def test_emoji_sentiment_social_media_use_case() -> None:
    """Test emoji sentiment mapping in realistic social media scenario."""
    tweet = "Harika gün! 🌞😍 Ama biraz üzgünüm 😢"
    
    # Use sentiment mode
    cleaned = cleaning.clean_text(tweet, emoji_mode="sentiment")
    assert "[SUNNY]" in cleaned or "[SPARKLE]" in cleaned  # Could be either
    assert "[LOVE]" in cleaned
    assert "[SAD]" in cleaned
    
    # Extract sentiment data for aggregation
    cleaned_text, sentiment_data = cleaning.clean_text(
        tweet, emoji_mode="sentiment_extract"
    )
    
    # Calculate net sentiment
    total_positive = sum(
        s["intensity"] for s in sentiment_data if s["polarity"] == "positive"
    )
    total_negative = sum(
        s["intensity"] for s in sentiment_data if s["polarity"] == "negative"
    )
    net_sentiment = total_positive - total_negative
    
    # Should be positive overall (2 positive, 1 negative)
    assert net_sentiment > 0
