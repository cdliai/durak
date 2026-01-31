//! Root Validity Checker for Turkish morphological analysis
//! 
//! Validates candidate roots after suffix stripping to prevent
//! over-stripping and ensure linguistically valid outputs.

use std::collections::HashSet;
use std::sync::OnceLock;

/// Turkish vowels (both lowercase and uppercase)
const TURKISH_VOWELS: &[char] = &['a', 'e', 'ı', 'i', 'o', 'ö', 'u', 'ü', 'A', 'E', 'I', 'İ', 'O', 'Ö', 'U', 'Ü'];

/// Impossible Turkish consonant clusters at word end
const INVALID_FINAL_CLUSTERS: &[&str] = &[
    "çk", "çp", "çt", "ğk", "ğp", "ğt",
    "kb", "kc", "kç", "kg", "kğ", "kj",
    "pb", "pc", "pç", "pg", "pğ", "pj",
    "tb", "tc", "tç", "tg", "tğ", "tj",
];

/// Embedded valid roots from lemma dictionary
static LEMMA_DICT_DATA: &str = include_str!("../resources/tr/lemmas/turkish_lemma_dict.txt");
static VALID_ROOTS: OnceLock<HashSet<String>> = OnceLock::new();

/// Get valid root words from lemma dictionary
fn get_valid_roots() -> &'static HashSet<String> {
    VALID_ROOTS.get_or_init(|| {
        let mut roots = HashSet::new();
        
        for line in LEMMA_DICT_DATA.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            
            // Format: inflected_form<TAB>lemma
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
    /// 
    /// # Arguments
    /// * `candidate` - The potential root word to validate
    /// 
    /// # Returns
    /// `true` if the candidate passes all validity checks
    pub fn is_valid_root(&self, candidate: &str) -> bool {
        // 1. Minimum length check
        if candidate.chars().count() < self.min_root_length {
            return false;
        }
        
        // 2. Strict mode: must be in known roots
        if self.strict {
            return get_valid_roots().contains(candidate);
        }
        
        // 3. Lenient mode: check linguistic constraints
        self.check_phonotactics(candidate)
    }
    
    /// Check Turkish phonotactic constraints
    /// 
    /// Rules:
    /// - Must contain at least one vowel
    /// - Should not end with invalid consonant clusters
    /// - Should follow basic Turkish syllable structure
    fn check_phonotactics(&self, word: &str) -> bool {
        if word.is_empty() {
            return false;
        }
        
        // Must contain at least one vowel
        if !word.chars().any(|c| TURKISH_VOWELS.contains(&c)) {
            return false;
        }
        
        // Check for invalid final consonant clusters
        let word_lower = word.to_lowercase();
        for cluster in INVALID_FINAL_CLUSTERS {
            if word_lower.ends_with(cluster) {
                return false;
            }
        }
        
        true
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
        assert!(!validator.is_valid_root("krm"));  // No vowels
        assert!(validator.is_valid_root("karma")); // Has vowels
    }
    
    #[test]
    fn test_invalid_clusters() {
        let validator = RootValidator::default();
        assert!(!validator.is_valid_root("kitaçk")); // Invalid final cluster
        assert!(validator.is_valid_root("kitap"));   // Valid
    }
    
    #[test]
    fn test_strict_mode() {
        let validator = RootValidator::new(2, true);
        // Should be in dictionary
        assert!(validator.is_valid_root("kitap"));
        assert!(validator.is_valid_root("ev"));
        // Should not be in dictionary (made up word)
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
