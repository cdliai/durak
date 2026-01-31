"""Demonstrate Turkish vowel harmony validation in Durak.

Vowel harmony is a fundamental rule in Turkish morphology that requires
suffix vowels to match the vowel category of the root word. This example
shows how Durak uses vowel harmony to improve lemmatization accuracy.

Turkish vowels are categorized as:
- Back vowels: a, ı, o, u
- Front vowels: e, i, ö, ü

When attaching suffixes:
- Back vowel roots take back vowel suffixes (e.g., kitap + lar → kitaplar)
- Front vowel roots take front vowel suffixes (e.g., ev + ler → evler)
"""

from durak._durak_core import check_vowel_harmony_py, strip_suffixes_validated


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def main():
    print_section("Turkish Vowel Harmony Demo")

    print("\n" + "Turkish Vowel Categories".center(70))
    print("  Back vowels (a, ı, o, u) → Back suffixes (-lar, -da, -dan)")
    print("  Front vowels (e, i, ö, ü) → Front suffixes (-ler, -de, -den)")

    # ============================================================================
    # Vowel Harmony Checker
    # ============================================================================
    print_section("Vowel Harmony Checker")

    print("\nValid harmony cases (root + suffix match):")
    valid_cases = [
        ("kitap", "lar", "kitaplar", "back + back ✓"),
        ("ev", "ler", "evler", "front + front ✓"),
        ("masa", "lar", "masalar", "back + back ✓"),
        ("göz", "ler", "gözler", "front + front ✓"),
        ("adam", "dan", "adamdan", "back + back ✓"),
        ("şehir", "den", "şehirden", "front + front ✓"),
    ]

    for root, suffix, word, note in valid_cases:
        harmony = check_vowel_harmony_py(root, suffix)
        status = "✓ PASS" if harmony else "✗ FAIL"
        print(f"  {word:15s} → {status:7s} ({note})")

    print("\nInvalid harmony cases (root + suffix mismatch):")
    invalid_cases = [
        ("kitap", "ler", "*kitapler", "back + front ✗"),
        ("ev", "lar", "*evlar", "front + back ✗"),
        ("masa", "ler", "*masaler", "back + front ✗"),
        ("göz", "lar", "*gözlar", "front + back ✗"),
    ]

    for root, suffix, word, note in invalid_cases:
        harmony = check_vowel_harmony_py(root, suffix)
        status = "✓ PASS" if harmony else "✗ FAIL"
        print(f"  {word:15s} → {status:7s} ({note})")

    # ============================================================================
    # Lemmatization with Vowel Harmony
    # ============================================================================
    print_section("Lemmatization with Vowel Harmony Validation")

    print("\nDemonstrating how vowel harmony prevents over-stripping:")
    print("  strip_suffixes_validated(word, check_harmony=True)\n")

    test_words = [
        "kitaplar",      # kitap + lar (valid)
        "evler",         # ev + ler (valid)
        "masalar",       # masa + lar (valid)
        "gözler",        # göz + ler (valid)
        "kitaplardan",   # kitap + lar + dan (multiple suffixes)
        "evlerden",      # ev + ler + den (multiple suffixes)
    ]

    print(f"  {'Word':<20s} {'Lemma':<15s} {'Harmony Valid'}")
    print(f"  { '-' * 20} { '-' * 15} { '-' * 13}")

    for word in test_words:
        # Strip with harmony checking (default behavior)
        lemma = strip_suffixes_validated(word, check_harmony=True, strict=False)

        # Check if the suffix is valid
        # Extract likely suffix (last 3 chars for demo purposes)
        suffix = word[-3:] if len(word) > 3 else word[-2:]
        root_candidate = word[:-3] if len(word) > 3 else word[:-2]

        # Verify harmony
        harmony_valid = check_vowel_harmony_py(root_candidate, suffix)
        status = "✓" if harmony_valid else "✗"

        print(f"  {word:<20s} {lemma:<15s} {status:^13s}")

    # ============================================================================
    # Impact on NLP Accuracy
    # ============================================================================
    print_section("Impact on NLP Accuracy")

    print("""
Vowel harmony validation improves lemmatization accuracy by:

1. **Preventing Invalid Morphology**: Rejects morphologically impossible word forms
   - *evlar (front root + back suffix) is rejected as invalid Turkish

2. **Better Root Identification**: Ensures only valid suffixes are stripped
   - Helps distinguish true roots from incorrect parsing

3. **Domain Adaptation**: Works with custom dictionaries via `strict=True` mode
   - First checks dictionary, then validates remaining unknown words

Example usage in production:
    from durak import Lemmatizer

    lemmatizer = Lemmatizer()
    word = "kitaplardan"
    lemma = lemmatizer(word)  # Uses vowel harmony internally
    # Result: "kitap"
""")

    # ============================================================================
    # Research Value
    # ============================================================================
    print_section("Research Value")

    print("""
Vowel harmony is a research-critical feature for Turkish NLP:

• **Morphological Analysis**: Essential for accurate morpheme segmentation
• **Language Modeling**: Captures phonological regularities in Turkish
• **Cross-Lingual Transfer**: Demonstrates language-specific rules in multilingual models
• **Linguistic Studies**: Enables computational exploration of Turkish phonology

Reference Implementation:
  • src/vowel_harmony.rs - Rust core implementation
  • tests/test_vowel_harmony.py - Comprehensive test suite
  • Issue #108 - Original feature request
""")

    print("\n" + "=" * 70)
    print("Demo complete!".center(70))
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
