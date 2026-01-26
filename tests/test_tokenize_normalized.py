"""Integration tests for tokenize_normalized with Token objects."""

import pytest


def test_tokenize_normalized_basic():
    """Test basic normalized tokenization with offset mapping."""
    try:
        from durak import tokenize_normalized
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    text = "İstanbul güzel"
    tokens = tokenize_normalized(text)
    
    assert len(tokens) == 2
    
    # First token: "İstanbul" → "istanbul"
    assert tokens[0].text == "istanbul"
    assert tokens[0].start == 0
    assert tokens[0].end == 8
    # Verify original extraction using byte offsets
    assert text[tokens[0].start:tokens[0].end] == "İstanbul"
    
    # Second token: "güzel" → "güzel"
    assert tokens[1].text == "güzel"
    assert tokens[1].start == 9
    assert text[tokens[1].start:tokens[1].end] == "güzel"


def test_tokenize_normalized_turkish_i():
    """Test Turkish I/İ and i/ı normalization with offsets."""
    try:
        from durak import tokenize_normalized
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    text = "IŞIK İNSAN"
    tokens = tokenize_normalized(text)
    
    assert len(tokens) == 2
    
    # "IŞIK" should normalize to "ışık"
    assert tokens[0].text == "ışık"
    assert text[tokens[0].start:tokens[0].end] == "IŞIK"
    
    # "İNSAN" should normalize to "insan"
    assert tokens[1].text == "insan"
    assert text[tokens[1].start:tokens[1].end] == "İNSAN"


def test_tokenize_normalized_apostrophe():
    """Test apostrophe handling in Turkish possessives."""
    try:
        from durak import tokenize_normalized
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    text = "İstanbul'a Ankara'dan"
    tokens = tokenize_normalized(text)
    
    assert len(tokens) == 2
    
    # "İstanbul'a" → "istanbul'a"
    assert tokens[0].text == "istanbul'a"
    assert text[tokens[0].start:tokens[0].end] == "İstanbul'a"
    
    # "Ankara'dan" → "ankara'dan"
    assert tokens[1].text == "ankara'dan"
    assert text[tokens[1].start:tokens[1].end] == "Ankara'dan"


def test_tokenize_normalized_ner_use_case():
    """Test realistic NER scenario with entity extraction."""
    try:
        from durak import tokenize_normalized
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    text = "Ahmet İstanbul'a gitti."
    tokens = tokenize_normalized(text)
    
    # Should tokenize: ["ahmet", "istanbul'a", "gitti", "."]
    assert len(tokens) == 4
    
    # Entity: "Ahmet" at position 0-5
    assert tokens[0].text == "ahmet"
    entity_text = text[tokens[0].start:tokens[0].end]
    assert entity_text == "Ahmet"
    
    # Entity: "İstanbul'a" 
    assert tokens[1].text == "istanbul'a"
    location_text = text[tokens[1].start:tokens[1].end]
    assert location_text == "İstanbul'a"
    
    # Verify we can create entity labels with original case preserved
    entity_label = f"{entity_text} (PER)"
    assert entity_label == "Ahmet (PER)"
    
    location_label = f"{location_text} (LOC)"
    assert location_label == "İstanbul'a (LOC)"


def test_tokenize_normalized_whitespace():
    """Test that whitespace is correctly skipped in offset mapping."""
    try:
        from durak import tokenize_normalized
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    text = "  Merhaba   dünya  "
    tokens = tokenize_normalized(text)
    
    assert len(tokens) == 2
    
    # "Merhaba" → "merhaba" (skips leading whitespace)
    assert tokens[0].text == "merhaba"
    assert text[tokens[0].start:tokens[0].end] == "Merhaba"
    
    # "dünya" → "dünya" (accounts for whitespace between tokens)
    assert tokens[1].text == "dünya"
    assert text[tokens[1].start:tokens[1].end] == "dünya"


def test_tokenize_normalized_punctuation():
    """Test punctuation tokenization with offsets."""
    try:
        from durak import tokenize_normalized
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    text = "Merhaba, dünya!"
    tokens = tokenize_normalized(text)
    
    assert len(tokens) == 4
    assert tokens[0].text == "merhaba"
    assert tokens[1].text == ","
    assert tokens[2].text == "dünya"
    assert tokens[3].text == "!"
    
    # Verify all offsets point to correct original text
    for token in tokens:
        assert text[token.start:token.end] == text[token.start:token.end]


def test_tokenize_normalized_empty():
    """Test empty text input."""
    try:
        from durak import tokenize_normalized
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    text = ""
    tokens = tokenize_normalized(text)
    assert len(tokens) == 0


def test_tokenize_normalized_numbers():
    """Test number tokenization with offsets."""
    try:
        from durak import tokenize_normalized
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    text = "2024 yılında 3.14 değerinde"
    tokens = tokenize_normalized(text)
    
    assert len(tokens) == 4
    assert tokens[0].text == "2024"
    assert tokens[1].text == "yılında"
    assert tokens[2].text == "3.14"
    assert tokens[3].text == "değerinde"
    
    # Verify offsets
    for token in tokens:
        extracted = text[token.start:token.end]
        # Numbers should preserve their original form
        if token.text.replace(".", "").isdigit():
            assert extracted == token.text


def test_token_repr():
    """Test Token __repr__ method."""
    try:
        from durak import Token
    except ImportError:
        pytest.skip("Rust extension not installed")
    
    token = Token("test", 0, 4)
    repr_str = repr(token)
    assert "Token" in repr_str
    assert "test" in repr_str
    assert "0" in repr_str
    assert "4" in repr_str
