"""
Hypothesis strategies for generating Turkish text test cases.

Provides specialized text generators for property-based testing of Turkish NLP functions.
"""

from hypothesis import strategies as st

# Turkish alphabet with proper diacritics
TURKISH_ALPHABET = "abcçdefgğhıijklmnoöprsştuüvyzABCÇDEFGĞHIİJKLMNOÖPRSŞTUÜVYZ"

# Common Turkish punctuation
TURKISH_PUNCTUATION = ".,!?;:'\"-()[]{}…"

# Common Turkish suffixes used with apostrophes
TURKISH_SUFFIXES = [
    "da",
    "de",
    "a",
    "e",
    "in",
    "ın",
    "un",
    "ün",
    "dan",
    "den",
    "tan",
    "ten",
    "nda",
    "nde",
    "nın",
    "nin",
    "nun",
    "nün",
]

# Common Turkish stopwords
TURKISH_STOPWORDS = [
    "ve",
    "veya",
    "ile",
    "gibi",
    "için",
    "ama",
    "fakat",
    "ki",
    "çünkü",
    "bu",
    "şu",
    "o",
    "bir",
    "her",
    "de",
    "da",
]


@st.composite
def turkish_word(draw, min_size=1, max_size=50):
    """Generate a random Turkish word."""
    return draw(st.text(alphabet=TURKISH_ALPHABET, min_size=min_size, max_size=max_size))


@st.composite
def turkish_word_with_suffix(draw):
    """Generate a Turkish word with an apostrophe and possessive/case marker."""
    word = draw(turkish_word(min_size=2, max_size=30))
    suffix = draw(st.sampled_from(TURKISH_SUFFIXES))
    return f"{word}'{suffix}"


@st.composite
def turkish_sentence(draw, min_words=1, max_words=20):
    """Generate a Turkish sentence with mixed words, suffixed words, and punctuation."""
    num_words = draw(st.integers(min_value=min_words, max_value=max_words))

    tokens = []
    for _ in range(num_words):
        token_type = draw(st.integers(min_value=0, max_value=2))

        if token_type == 0:
            # Regular word
            tokens.append(draw(turkish_word(min_size=1, max_size=20)))
        elif token_type == 1:
            # Word with suffix
            tokens.append(draw(turkish_word_with_suffix()))
        else:
            # Punctuation
            tokens.append(draw(st.sampled_from(list(TURKISH_PUNCTUATION))))

    return " ".join(tokens)


@st.composite
def turkish_text_with_unicode_edge_cases(draw):
    """Generate Turkish text with Unicode edge cases (zero-width chars, combining diacritics)."""
    base_text = draw(turkish_sentence())

    # Randomly insert Unicode edge cases
    edge_cases = [
        "\u200b",  # Zero-width space
        "\u200c",  # Zero-width non-joiner
        "\u200d",  # Zero-width joiner
        "\ufeff",  # Zero-width no-break space
        "a\u0301",  # Combining acute accent
        "i\u0307",  # Combining dot above
    ]

    if draw(st.booleans()):
        pos = draw(st.integers(min_value=0, max_value=len(base_text)))
        edge = draw(st.sampled_from(edge_cases))
        base_text = base_text[:pos] + edge + base_text[pos:]

    return base_text


@st.composite
def turkish_stopword_list(draw):
    """Generate a list of Turkish stopwords (for testing removal)."""
    return draw(st.sampled_from(TURKISH_STOPWORDS))
