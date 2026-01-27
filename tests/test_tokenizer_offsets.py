import pytest
from durak.tokenizer import tokenize_with_offsets


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
