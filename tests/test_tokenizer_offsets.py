import pytest

from durak.tokenizer import tokenize_with_offsets, tokenize_with_normalized_offsets


def test_offset_mapping():
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
        
    text = "Ali gel."
    # Ali (0,3), space (3,4), gel (4,7), . (7,8)
    # Our regex captures words and punctuation, but not spaces (unless they match?)
    # Regex: WORD | PUNCT. Spaces are usually skipped by findall 
    # unless explicitly matched.
    # Logic in Rust: `for caps in re.captures_iter(text)`
    
    tokens = tokenize_with_offsets(text)
    
    expected = [
        ("Ali", 0, 3),
        ("gel", 4, 7),
        (".", 7, 8)
    ]
    
    # Check values
    assert len(tokens) == 3
    for (tok, start, end), (exp_tok, exp_start, exp_end) in zip(tokens, expected):
        assert tok == exp_tok
        assert start == exp_start
        assert end == exp_end
        
        # Verify slicing matches
        assert text[start:end] == tok

def test_turkish_offsets():
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
        
    # Turkish characters have multi-byte UTF-8 representations.
    # Char offset logic must handle this. 'İ' is 2 bytes.
    text = "İğne" 
    # Index 0: İ
    # Index 1: ğ
    # Index 2: n
    # Index 3: e
    # Token "İğne" -> (0, 4)
    
    tokens = tokenize_with_offsets(text)
    assert len(tokens) == 1
    assert tokens[0] == ("İğne", 0, 4)
    assert text[0:4] == "İğne"
    
def test_mixed_content():
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
        
    text = "Koş! (Hızlıca)"
    # Koş -> 0-3
    # ! -> 3-4
    # ( -> 5-6
    # Hızlıca -> 6-13
    # ) -> 13-14
    
    tokens = tokenize_with_offsets(text)
    token_strs = [t[0] for t in tokens]
    assert token_strs == ["Koş", "!", "(", "Hızlıca", ")"]
    
    for tok, start, end in tokens:
        assert text[start:end] == tok


# ============================================================================
# Tests for tokenize_with_normalized_offsets (NER-friendly version)
# ============================================================================

def test_normalized_offsets_istanbul():
    """Test İ→i normalization while preserving original offsets."""
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
        
    text = "İstanbul"
    tokens = tokenize_with_normalized_offsets(text)
    
    assert len(tokens) == 1
    assert tokens[0] == ("istanbul", 0, 8)
    
    # Verify offset points to original text
    assert text[0:8] == "İstanbul"

def test_normalized_offsets_i_dotless():
    """Test I→ı normalization while preserving original offsets."""
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
        
    text = "IĞDIR"
    tokens = tokenize_with_normalized_offsets(text)
    
    assert len(tokens) == 1
    assert tokens[0] == ("ığdır", 0, 5)
    
    # Verify offset points to original text
    assert text[0:5] == "IĞDIR"

def test_normalized_offsets_apostrophe():
    """Test apostrophe handling with normalization."""
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
        
    text = "Ankara'da"
    tokens = tokenize_with_normalized_offsets(text)
    
    assert len(tokens) == 1
    assert tokens[0] == ("ankara'da", 0, 9)
    
    # Verify offset points to original text
    assert text[0:9] == "Ankara'da"

def test_normalized_offsets_sentence():
    """Test a full sentence with mixed case and Turkish characters."""
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
        
    text = "İstanbul'a gittim."
    tokens = tokenize_with_normalized_offsets(text)
    
    expected = [
        ("istanbul'a", 0, 10),
        ("gittim", 11, 17),
        (".", 17, 18),
    ]
    
    assert len(tokens) == 3
    for (tok, start, end), (exp_tok, exp_start, exp_end) in zip(tokens, expected):
        assert tok == exp_tok
        assert start == exp_start
        assert end == exp_end
        
        # Verify offset points to original text (case-sensitive check)
        original_slice = text[start:end]
        # Token is normalized but offset references original
        assert original_slice.lower() == tok or original_slice == tok

def test_normalized_offsets_ner_use_case():
    """Simulate NER use case: labels reference original text, tokens are normalized."""
    try:
        import _durak_core  # noqa: F401
    except ImportError:
        pytest.skip("Rust extension not installed")
        
    # Simulated labeled data: entity "İstanbul" at position 0-8
    text = "İstanbul güzel bir şehir."
    entity_label = {"text": "İstanbul", "start": 0, "end": 8, "label": "LOC"}
    
    # Tokenize with normalized offsets
    tokens = tokenize_with_normalized_offsets(text)
    
    # Find token that matches entity position
    entity_token = None
    for tok, start, end in tokens:
        if start == entity_label["start"] and end == entity_label["end"]:
            entity_token = (tok, start, end)
            break
    
    # Verify we found the entity token
    assert entity_token is not None
    assert entity_token[0] == "istanbul"  # Normalized token
    assert text[entity_token[1]:entity_token[2]] == "İstanbul"  # Original text
