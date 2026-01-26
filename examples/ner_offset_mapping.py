"""
Named Entity Recognition (NER) with Offset Mapping Example

This example demonstrates how to use Durak's offset mapping feature
to perform NER while preserving the exact positions in the original text.
"""

from durak import tokenize_normalized


def extract_entities_with_positions(text: str) -> list[tuple[str, int, int, str]]:
    """
    Extract entities from text and return their original positions.
    
    Returns:
        List of (entity_text, start, end, label) tuples
    """
    # Tokenize with offset mapping
    tokens = tokenize_normalized(text)
    
    # Mock entity detection (in production, use a NER model)
    entities = []
    for token in tokens:
        # Extract original text using character offsets
        original_text = text[token.start:token.end]
        
        # Simple heuristic: capitalized words might be entities
        if original_text and original_text[0].isupper():
            entities.append((original_text, token.start, token.end, "ENTITY"))
    
    return entities

def main():
    # Example 1: Basic NER with Turkish text
    text1 = "Ahmet İstanbul'a gitti."
    print(f"Text: {text1}")
    print("Entities found:")
    
    entities = extract_entities_with_positions(text1)
    for entity, start, end, label in entities:
        print(f"  {label}: '{entity}' at position [{start}:{end}]")
        # Verify we can extract it correctly
        assert text1[start:end] == entity
    
    print()
    
    # Example 2: Handling Turkish I/İ normalization
    text2 = "IŞIK İNSAN projesi"
    print(f"Text: {text2}")
    print("Tokens with offsets:")
    
    tokens = tokenize_normalized(text2)
    for token in tokens:
        original = text2[token.start:token.end]
        print(
            f"  Normalized: '{token.text}' | Original: '{original}' "
            f"| Position: [{token.start}:{token.end}]"
        )
    
    print()
    
    # Example 3: Real-world NER scenario
    text3 = "Fatih Burak Karagöz, Ankara Üniversitesi'nde çalışıyor."
    print(f"Text: {text3}")
    print("Token analysis:")
    
    tokens = tokenize_normalized(text3)
    for token in tokens:
        original = text3[token.start:token.end]
        is_capitalized = original and original[0].isupper()
        print(f"  '{token.text}' -> '{original}' [{token.start}:{token.end}] "
              f"{'(POTENTIAL ENTITY)' if is_capitalized else ''}")
    
    print()
    
    # Example 4: Integration with transformers/BERT
    print("Integration with transformers:")
    print("You can now pass these offsets directly to BERT/Transformers:")
    print("  tokens = [token.text for token in tokenize_normalized(text)]")
    print(
        "  offsets = [(token.start, token.end) "
        "for token in tokenize_normalized(text)]"
    )
    print(
        "  # Use offsets to align BERT predictions "
        "with original text positions"
    )

if __name__ == "__main__":
    main()
