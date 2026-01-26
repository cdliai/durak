"""Tests for Turkish syllabification module."""

import pytest

from durak import Syllabifier, SyllableInfo, syllabify


class TestSyllabificationBasic:
    """Test basic syllabification functionality."""
    
    @pytest.mark.parametrize("word,expected", [
        # Single syllable
        ("ev", ["ev"]),
        ("at", ["at"]),
        ("üç", ["üç"]),
        
        # Two syllables
        ("kitap", ["ki", "tap"]),
        ("okul", ["o", "kul"]),
        ("ağaç", ["a", "ğaç"]),
        ("gece", ["ge", "ce"]),
        
        # Three syllables
        ("merhaba", ["mer", "ha", "ba"]),
        ("anlamak", ["an", "la", "mak"]),
        ("öğrenci", ["öğ", "ren", "ci"]),
        ("karmaşık", ["kar", "ma", "şık"]),
        
        # Four syllables
        ("bilgisayar", ["bil", "gi", "sa", "yar"]),
        ("çalışmak", ["ça", "lış", "mak"]),
        
        # Complex cases
        ("İstanbul", ["İs", "tan", "bul"]),
        ("Ankara", ["An", "ka", "ra"]),
        
        # Words with apostrophes (apostrof hece sınırı değil, morpheme boundary)
        ("Türkiye'nin", ["Tür", "ki", "ye'nin"]),
        
        # Edge cases
        ("a", ["a"]),
        ("I", ["I"]),
    ])
    def test_syllabification_basic(self, word, expected):
        """Test basic syllabification with various Turkish words."""
        result = syllabify(word)
        assert result == expected, f"Expected {expected}, got {result} for word '{word}'"
    
    def test_syllabification_with_separator(self):
        """Test syllabification with custom separator."""
        assert syllabify("merhaba", separator="-") == "mer-ha-ba"
        assert syllabify("kitap", separator="·") == "ki·tap"
        assert syllabify("okul", separator=" ") == "o kul"
        assert syllabify("ev", separator="-") == "ev"
    
    def test_syllabification_empty_word(self):
        """Test that empty word raises ValueError."""
        with pytest.raises(ValueError, match="Word cannot be empty"):
            syllabify("")
    
    def test_syllabification_preserves_case(self):
        """Test that syllabification preserves original case."""
        assert syllabify("İstanbul") == ["İs", "tan", "bul"]
        assert syllabify("ANKARA") == ["AN", "KA", "RA"]
        assert syllabify("Türkiye") == ["Tür", "ki", "ye"]


class TestSyllabifier:
    """Test Syllabifier class with advanced features."""
    
    def test_syllabifier_analyze(self):
        """Test detailed syllable analysis."""
        syl = Syllabifier()
        info = syl.analyze("kitap")
        
        assert isinstance(info, SyllableInfo)
        assert info.word == "kitap"
        assert info.syllables == ["ki", "tap"]
        assert info.count == 2
        assert info.structure == ["CV", "CVC"]
        assert info.stress_pattern == [0, 1]  # Final syllable stress
    
    def test_syllabifier_count(self):
        """Test syllable counting."""
        syl = Syllabifier()
        
        assert syl.count("ev") == 1
        assert syl.count("kitap") == 2
        assert syl.count("merhaba") == 3
        assert syl.count("bilgisayar") == 4
    
    @pytest.mark.parametrize("word,expected_structure", [
        ("ev", ["VC"]),
        ("okul", ["V", "CVC"]),
        ("kitap", ["CV", "CVC"]),
        ("merhaba", ["CVC", "CV", "CV"]),
        ("anlamak", ["VC", "CV", "CVC"]),
        ("İstanbul", ["VC", "CVC", "CVC"]),
    ])
    def test_syllabifier_structure(self, word, expected_structure):
        """Test syllable structure detection."""
        syl = Syllabifier()
        info = syl.analyze(word)
        assert info.structure == expected_structure
    
    def test_syllabifier_stress_pattern(self):
        """Test stress pattern detection (Turkish: final syllable)."""
        syl = Syllabifier()
        
        # Single syllable: stressed
        info = syl.analyze("ev")
        assert info.stress_pattern == [1]
        
        # Two syllables: final stressed
        info = syl.analyze("kitap")
        assert info.stress_pattern == [0, 1]
        
        # Three syllables: final stressed
        info = syl.analyze("merhaba")
        assert info.stress_pattern == [0, 0, 1]


class TestSyllabificationEdgeCases:
    """Test edge cases and special scenarios."""
    
    def test_vowel_sequences(self):
        """Test words with consecutive vowels."""
        # V.V pattern: always break
        assert syllabify("oa") == ["o", "a"]
        assert syllabify("süit") == ["sü", "it"]
    
    def test_consonant_clusters(self):
        """Test words with consonant clusters."""
        assert syllabify("tren") == ["tren"]  # Single syllable with cluster
        assert syllabify("program") == ["prog", "ram"]
        assert syllabify("anlamak") == ["an", "la", "mak"]
    
    def test_words_with_circumflex(self):
        """Test words with circumflex accents (â, î, û)."""
        assert syllabify("âlem") == ["â", "lem"]
        assert syllabify("kâr") == ["kâr"]
        assert syllabify("rûh") == ["rûh"]
    
    def test_single_character_words(self):
        """Test single character words."""
        assert syllabify("a") == ["a"]
        assert syllabify("o") == ["o"]
        assert syllabify("k") == ["k"]


class TestSyllabificationIntegration:
    """Test integration with other Durak features."""
    
    def test_syllabify_tokenized_text(self):
        """Test syllabification of tokenized text."""
        from durak import tokenize
        
        text = "Kitabı okudum."
        tokens = tokenize(text)
        
        # Syllabify alphabetic tokens only
        syllabified = {
            token: syllabify(token) 
            for token in tokens 
            if token.isalpha()
        }
        
        assert "Kitabı" in syllabified
        assert "okudum" in syllabified
        assert syllabified["okudum"] == ["o", "ku", "dum"]
    
    def test_filter_by_syllable_count(self):
        """Test filtering words by syllable count (poetry analysis)."""
        words = ["ev", "kitap", "merhaba", "bilgisayar", "okul"]
        
        # Filter for exactly 3 syllables
        three_syllable_words = [
            w for w in words 
            if syllabify(w).__len__() == 3
        ]
        
        assert three_syllable_words == ["merhaba"]
    
    def test_batch_syllabification(self):
        """Test batch processing of multiple words."""
        words = ["kitap", "okul", "öğrenci", "merhaba"]
        
        results = [syllabify(word) for word in words]
        
        assert len(results) == 4
        assert results[0] == ["ki", "tap"]
        assert results[1] == ["o", "kul"]
        assert results[2] == ["öğ", "ren", "ci"]
        assert results[3] == ["mer", "ha", "ba"]


class TestSyllabificationPerformance:
    """Test performance characteristics."""
    
    def test_large_word(self):
        """Test syllabification of long Turkish word."""
        # Muvaffakiyetsizleştiricileştiriveremeyebileceklerimizdenmişsinizcesine
        # (One of the longest Turkish words)
        long_word = "çekoslovakyalılaştıramadıklarımızdanmışsınızcasına"
        
        result = syllabify(long_word)
        
        # Should successfully syllabify without error
        assert isinstance(result, list)
        assert len(result) > 10  # Long word should have many syllables
        assert all(isinstance(syl, str) for syl in result)
    
    def test_batch_performance(self):
        """Test batch syllabification doesn't crash."""
        # Simulate processing a small corpus
        corpus = ["kitap", "okul", "merhaba"] * 100
        
        results = [syllabify(word) for word in corpus]
        
        assert len(results) == 300
        # Spot check
        assert results[0] == ["ki", "tap"]
        assert results[100] == ["o", "kul"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
