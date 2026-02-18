//! Root Validity Checker for Turkish morphological analysis
//!
//! Validates candidate roots after suffix stripping to prevent
//! over-stripping and ensure linguistically valid outputs.

use std::collections::HashSet;
use std::sync::OnceLock;

/// Turkish vowels (both lowercase and uppercase)
const TURKISH_VOWELS: &[char] = &[
    'a', 'e', 'ı', 'i', 'o', 'ö', 'u', 'ü', 'A', 'E', 'I', 'İ', 'O', 'Ö', 'U', 'Ü',
];

/// Turkish sonorant consonants (can end words naturally)
const SONORANT_CONSONANTS: &[char] = &['l', 'r', 'n', 'm', 'y', 'L', 'R', 'N', 'M', 'Y'];

/// Turkish voiceless stops (words typically don't end in these without specific patterns)
const VOICELESS_STOPS: &[char] = &['p', 'ç', 't', 'k', 'P', 'Ç', 'T', 'K'];

/// Impossible Turkish consonant clusters at word end
const INVALID_FINAL_CLUSTERS: &[&str] = &[
    "çk", "çp", "çt", "ğk", "ğp", "ğt", "kb", "kc", "kç", "kg", "kğ", "kj", "pb", "pc", "pç", "pg",
    "pğ", "pj", "tb", "tc", "tç", "tg", "tğ", "tj", "nd", "nt", "nk", "ng",
];

/// Common Turkish bound stems - these look like valid roots but aren't free words
const BOUND_STEMS: &[&str] = &[
    "öğrenc", "öğret", "tanı", "yapı", "bili", "geli", "gidi", "kali", "veri", "alı", "olı",
    "görü", "bilü",
];

/// Embedded valid roots from lemma dictionary
static LEMMA_DICT_DATA: &str = include_str!("../resources/tr/lemmas/turkish_lemma_dict.txt");
static VALID_ROOTS: OnceLock<HashSet<String>> = OnceLock::new();

/// Get valid root words from lemma dictionary
pub fn get_valid_roots() -> &'static HashSet<String> {
    VALID_ROOTS.get_or_init(|| {
        let mut roots = HashSet::new();

        for line in LEMMA_DICT_DATA.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }

            if let Some((_, lemma)) = line.split_once('\t') {
                roots.insert(lemma.trim().to_string());
            }
        }

        roots
    })
}

/// Root validity checker for Turkish morphology
pub struct RootValidator {
    /// Minimum acceptable root length (characters)
    pub min_root_length: usize,
    /// Whether to use strict dictionary checking
    pub strict: bool,
}

impl Default for RootValidator {
    fn default() -> Self {
        Self {
            min_root_length: 2,
            strict: false,
        }
    }
}

impl RootValidator {
    /// Create a new validator with custom settings
    pub fn new(min_root_length: usize, strict: bool) -> Self {
        Self {
            min_root_length,
            strict,
        }
    }

    /// Check if a candidate root is valid
    pub fn is_valid_root(&self, candidate: &str) -> bool {
        // 1. Minimum length check
        if candidate.chars().count() < self.min_root_length {
            return false;
        }

        // 2. Check if it's a known bound stem (never valid)
        let candidate_lower = candidate.to_lowercase();
        for bound_stem in BOUND_STEMS {
            if candidate_lower == *bound_stem || candidate_lower.ends_with(bound_stem) {
                return false;
            }
        }

        // 3. Strict mode: must be in known roots dictionary
        if self.strict {
            return get_valid_roots().contains(candidate);
        }

        // 4. Lenient mode: check linguistic constraints
        self.check_phonotactics(candidate)
    }

    /// Check Turkish phonotactic constraints
    fn check_phonotactics(&self, word: &str) -> bool {
        if word.is_empty() {
            return false;
        }

        let chars: Vec<char> = word.chars().collect();
        let word_lower: String = word.to_lowercase();
        let lower_chars: Vec<char> = word_lower.chars().collect();

        // Must contain at least one vowel
        if !chars.iter().any(|c| TURKISH_VOWELS.contains(c)) {
            return false;
        }

        // Check for invalid final consonant clusters
        for cluster in INVALID_FINAL_CLUSTERS {
            if word_lower.ends_with(cluster) {
                return false;
            }
        }

        // Check if last char is a vowel - always valid
        let last_char = lower_chars.last().unwrap();
        if TURKISH_VOWELS.contains(last_char) {
            return true;
        }

        // Check if last char is a sonorant - usually valid
        if SONORANT_CONSONANTS.contains(last_char) {
            return self.has_valid_syllable_structure(&lower_chars);
        }

        // Voiceless stops at word end are valid in Turkish
        if VOICELESS_STOPS.contains(last_char) {
            return lower_chars.len() >= 3 && self.has_valid_syllable_structure(&lower_chars);
        }

        true
    }

    /// Check if the word has a valid Turkish syllable structure
    fn has_valid_syllable_structure(&self, chars: &[char]) -> bool {
        if chars.len() < 2 {
            return false;
        }

        let vowel_count = chars.iter().filter(|c| TURKISH_VOWELS.contains(c)).count();

        if vowel_count == 0 {
            return false;
        }

        if chars.len() <= 3 {
            return vowel_count >= 1;
        }

        let vowel_ratio = vowel_count as f32 / chars.len() as f32;
        vowel_ratio >= 0.2 && vowel_ratio <= 0.7
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_min_length() {
        let validator = RootValidator::new(2, false);
        assert!(!validator.is_valid_root("k"));
        assert!(validator.is_valid_root("ki"));
        assert!(validator.is_valid_root("kitap"));
    }

    #[test]
    fn test_vowel_requirement() {
        let validator = RootValidator::default();
        assert!(!validator.is_valid_root("krm"));
        assert!(validator.is_valid_root("karma"));
    }

    #[test]
    fn test_invalid_clusters() {
        let validator = RootValidator::default();
        assert!(!validator.is_valid_root("kitaçk"));
        assert!(validator.is_valid_root("kitap"));
    }

    #[test]
    fn test_bound_stems_rejected() {
        let validator = RootValidator::default();
        assert!(!validator.is_valid_root("öğrenc"));
        assert!(!validator.is_valid_root("ÖĞRENC"));
    }

    #[test]
    fn test_valid_word_endings() {
        let validator = RootValidator::default();
        assert!(validator.is_valid_root("kita"));
        assert!(validator.is_valid_root("evi"));
        assert!(validator.is_valid_root("kal"));
        assert!(validator.is_valid_root("gel"));
        assert!(validator.is_valid_root("gün"));
        assert!(validator.is_valid_root("kitap"));
        assert!(validator.is_valid_root("at"));
    }

    #[test]
    fn test_strict_mode() {
        let validator = RootValidator::new(2, true);
        assert!(validator.is_valid_root("kitap"));
        assert!(validator.is_valid_root("ev"));
        assert!(!validator.is_valid_root("xyzabc"));
    }

    #[test]
    fn test_known_roots() {
        let roots = get_valid_roots();
        assert!(roots.contains("kitap"));
        assert!(roots.contains("ev"));
        assert!(roots.contains("gel"));
        assert!(roots.contains("git"));
    }
}
