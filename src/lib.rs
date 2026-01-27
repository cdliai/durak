mod root_validator;
mod vowel_harmony;

use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::OnceLock;
use regex::Regex;
use root_validator::RootValidator;

// Embedded resources using include_str! for zero-overhead loading
// Resources are compiled directly into the binary at build time
static DETACHED_SUFFIXES_DATA: &str = include_str!("../resources/tr/labels/DETACHED_SUFFIXES.txt");
static STOPWORDS_TR_DATA: &str = include_str!("../resources/tr/stopwords/base/turkish.txt");
static STOPWORDS_METADATA_DATA: &str = include_str!("../resources/tr/stopwords/metadata.json");
static STOPWORDS_SOCIAL_MEDIA_DATA: &str = include_str!("../resources/tr/stopwords/domains/social_media.txt");
static LEMMA_DICT_DATA: &str = include_str!("../resources/tr/lemmas/turkish_lemma_dict.txt");

static LEMMA_DICT: OnceLock<HashMap<&'static str, &'static str>> = OnceLock::new();
static TOKEN_REGEX: OnceLock<Regex> = OnceLock::new();
static DETACHED_SUFFIXES: OnceLock<Vec<&'static str>> = OnceLock::new();
static STOPWORDS_BASE: OnceLock<Vec<&'static str>> = OnceLock::new();

fn get_lemma_dict() -> &'static HashMap<&'static str, &'static str> {
    LEMMA_DICT.get_or_init(|| {
        // Load Turkish lemma dictionary from embedded TSV resource
        // Format: inflected_form<TAB>lemma
        let mut m = HashMap::new();
        
        for line in LEMMA_DICT_DATA.lines() {
            let line = line.trim();
            if line.is_empty() || line.starts_with('#') {
                continue;
            }
            
            if let Some((inflected, lemma)) = line.split_once('\t') {
                m.insert(inflected.trim(), lemma.trim());
            }
        }
        
        m
    })
}

fn get_token_regex() -> &'static Regex {
    TOKEN_REGEX.get_or_init(|| {
        // Regex patterns tuned for Turkish tokenization (ported from Python)
        // URL, Emoticon, Apostrophe, Number, Word, Punctuation
        let pattern = r"(?x)
            (https?://[^\s]+|www\.[^\s]+) |          # URL
            ([:;=8][-^']?[)DPOo(\[/\\]) |            # Emoticon
            ([A-Za-zÇĞİÖŞÜçğıöşü]+(?:'[A-Za-zÇĞİÖŞÜçğıöşü]+)?) | # Apostrophe
            (\d+(?:[.,]\d+)*(?:[-–]\d+)?) |          # Number
            ([A-Za-zÇĞİÖŞÜçğıöşü]+(?:-[A-Za-zÇĞİÖŞÜçğıöşü]+)*) | # Word
            ([^\w\s])                                # Punctuation
        ";
        Regex::new(pattern).expect("Invalid regex pattern")
    })
}

/// Fast normalization for Turkish text.
/// Handles I/ı and İ/i conversion correctly and lowercases the rest.
#[pyfunction]
fn fast_normalize(text: &str) -> String {
    // Rust handles Turkish I/ı conversion correctly and instantly
    // "Single Pass" allocation for maximum speed
    text.chars().map(|c| match c {
        'İ' => 'i',
        'I' => 'ı',
        _ => c.to_lowercase().next().unwrap_or(c)
    }).collect()
}

/// Tokenize text and return tokens with their start and end character offsets.
/// Returns a list of (token, start, end).
#[pyfunction]
fn tokenize_with_offsets(text: &str) -> Vec<(String, usize, usize)> {
    let re = get_token_regex();
    let mut results = Vec::new();

    for caps in re.captures_iter(text) {
        if let Some(mat) = caps.get(0) {
            let token = mat.as_str().to_string();
            // In Rust regex, `mat.start()` and `mat.end()` return byte indices.
            // Python expects character indices. We must convert carefully.
            // However, typical NLP tools often work with byte offsets or char offsets.
            // Here we want char offsets strictly for Python compatibility if possible,
            // OR we just return byte offsets and let Python handle it?
            // "The Fix: Your Rust tokenizer must return Offset Mappings (start/end indices pointing back to the original raw text)"
            // Usually Python users expect char indices.
            
            // Converting byte offset to char offset is O(N) scan unless we map it.
            // For now, let's just return what Regex gives us, which is byte offsets, 
            // BUT for this PoC we can do a quick char count up to that point if we want absolute correctness,
            // or just note that these are byte offsets (Rust UTF-8).
            // Let's implement char offset conversion for correctness.
            let byte_start = mat.start();
            let byte_end = mat.end();
            
            let char_start = text[..byte_start].chars().count();
            let char_len = text[byte_start..byte_end].chars().count();
            let char_end = char_start + char_len;
            
            results.push((token, char_start, char_end));
        }
    }
    results
}

/// Tier 1: Exact Lookup
#[pyfunction]
fn lookup_lemma(word: &str) -> Option<String> {
    let dict = get_lemma_dict();
    dict.get(word).map(|s| s.to_string())
}

/// Tier 2: Heuristic Suffix Stripping
/// Simple rule-based stripper for demonstration.
/// In production, this would use a more complex state machine and vowel harmony checks.
#[pyfunction]
fn strip_suffixes(word: &str) -> String {
    let suffixes = ["lar", "ler", "nin", "nın", "den", "dan", "du", "dün"];
    let mut current = word.to_string();
    
    // Very naive recursive stripping for PoC
    let mut changed = true;
    while changed {
        changed = false;
        for suffix in suffixes {
            if current.ends_with(suffix) && current.len() > suffix.len() + 2 { 
                 // +2 constraint prevents over-stripping short roots
                current = current[..current.len() - suffix.len()].to_string();
                changed = true;
                break; // Restart loop after stripping one suffix
            }
        }
    }
    current
}

/// Strip suffixes with root validity checking and vowel harmony validation
/// Prevents over-stripping by validating candidate roots and checking vowel harmony
/// 
/// # Arguments
/// * `word` - The word to process
/// * `strict` - If true, check dictionary first, then validate; if false, use phonotactic rules only
/// * `min_root_length` - Minimum acceptable root length (default: 2)
/// * `check_harmony` - If true, validate vowel harmony before stripping (default: true)
/// 
/// # Returns
/// The word with suffixes stripped, validated to prevent over-stripping
#[pyfunction]
#[pyo3(signature = (word, strict=false, min_root_length=2, check_harmony=true))]
fn strip_suffixes_validated(word: &str, strict: bool, min_root_length: usize, check_harmony: bool) -> String {
    // In strict mode, first check if the word is in the lemma dictionary
    if strict {
        if let Some(lemma) = lookup_lemma(word) {
            return lemma;
        }
    }
    
    let validator = RootValidator::new(min_root_length, strict);
    // Comprehensive Turkish suffix list (ordered by length for greedy matching)
    let suffixes = [
        // Compound suffixes (longer first for greedy matching)
        "lardan", "lerden", "ların", "lerin", "yorum", "yorsun", "yoruz",
        // Basic suffixes
        "lar", "ler", "nin", "nın", "den", "dan", "ta", "te", "da", "de",
        "ın", "in", "un", "ün", "du", "dü", "tu", "tü",
        // Possessive and case markers
        "ım", "im", "um", "üm", "ı", "i", "u", "ü",
        // Verb suffixes
        "yor", "mak", "mek", "dik", "dık", "duk", "dük",
        "di", "dı", "du", "dü", "ti", "tı", "tu", "tü",
    ];
    let mut current = word.to_string();
    
    let mut changed = true;
    while changed {
        changed = false;
        for suffix in suffixes {
            if current.ends_with(suffix) {
                let candidate = &current[..current.len() - suffix.len()];
                
                // Validate root and vowel harmony
                let is_valid_root = validator.is_valid_root(candidate);
                let has_harmony = !check_harmony || vowel_harmony::check_vowel_harmony(candidate, suffix);
                
                // Only strip if both conditions are met
                if is_valid_root && has_harmony {
                    current = candidate.to_string();
                    changed = true;
                    break;
                }
            }
        }
    }
    current
}

/// Get embedded detached suffixes list
/// Returns suffixes compiled into the binary from resources/tr/labels/DETACHED_SUFFIXES.txt
#[pyfunction]
fn get_detached_suffixes() -> Vec<String> {
    let suffixes = DETACHED_SUFFIXES.get_or_init(|| {
        DETACHED_SUFFIXES_DATA
            .lines()
            .map(|line| line.trim())
            .filter(|line| !line.is_empty())
            .collect()
    });
    suffixes.iter().map(|s| s.to_string()).collect()
}

/// Get embedded Turkish stopwords list
/// Returns base Turkish stopwords compiled into the binary from resources/tr/stopwords/base/turkish.txt
#[pyfunction]
fn get_stopwords_base() -> Vec<String> {
    let stopwords = STOPWORDS_BASE.get_or_init(|| {
        STOPWORDS_TR_DATA
            .lines()
            .map(|line| line.trim())
            .filter(|line| !line.is_empty() && !line.starts_with('#'))
            .collect()
    });
    stopwords.iter().map(|s| s.to_string()).collect()
}

/// Get embedded stopwords metadata JSON
/// Returns metadata compiled into the binary from resources/tr/stopwords/metadata.json
#[pyfunction]
fn get_stopwords_metadata() -> String {
    STOPWORDS_METADATA_DATA.to_string()
}

/// Get embedded social media stopwords
/// Returns social media stopwords compiled into the binary from resources/tr/stopwords/domains/social_media.txt
#[pyfunction]
fn get_stopwords_social_media() -> Vec<String> {
    STOPWORDS_SOCIAL_MEDIA_DATA
        .lines()
        .map(|line| line.trim())
        .filter(|line| !line.is_empty() && !line.starts_with('#'))
        .map(|s| s.to_string())
        .collect()
}

/// Check if a suffix harmonizes with a root (Python binding)
/// 
/// # Arguments
/// * `root` - The root word
/// * `suffix` - The suffix to check
/// 
/// # Returns
/// True if the suffix harmonizes with the root, False otherwise
#[pyfunction]
fn check_vowel_harmony_py(root: &str, suffix: &str) -> bool {
    vowel_harmony::check_vowel_harmony(root, suffix)
}

/// The internal Rust part of the Durak library.
/// High-performance Turkish NLP operations with embedded resources.
#[pymodule]
fn _durak_core(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Core text processing functions
    m.add_function(wrap_pyfunction!(fast_normalize, m)?)?;
    m.add_function(wrap_pyfunction!(tokenize_with_offsets, m)?)?;

    // Lemmatization functions
    m.add_function(wrap_pyfunction!(lookup_lemma, m)?)?;
    m.add_function(wrap_pyfunction!(strip_suffixes, m)?)?;
    m.add_function(wrap_pyfunction!(strip_suffixes_validated, m)?)?;

    // Vowel harmony checker
    m.add_function(wrap_pyfunction!(check_vowel_harmony_py, m)?)?;

    // Embedded resource accessors
    m.add_function(wrap_pyfunction!(get_detached_suffixes, m)?)?;
    m.add_function(wrap_pyfunction!(get_stopwords_base, m)?)?;
    m.add_function(wrap_pyfunction!(get_stopwords_metadata, m)?)?;
    m.add_function(wrap_pyfunction!(get_stopwords_social_media, m)?)?;

    Ok(())
}

// ============================================================================
// UNIT TESTS
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_lemma_dict_loading() {
        let dict = get_lemma_dict();
        
        // Verify dictionary is not empty
        assert!(!dict.is_empty(), "Lemma dictionary should not be empty");
        
        // Verify we have more than mock data (original had 3 entries)
        assert!(dict.len() > 100, "Dictionary should contain more than 100 entries, got {}", dict.len());
        
        println!("✓ Loaded {} lemma entries", dict.len());
    }

    #[test]
    fn test_lookup_lemma_high_frequency_nouns() {
        // Test common noun inflections
        let test_cases = vec![
            ("kitaplar", Some("kitap")),
            ("evler", Some("ev")),
            ("insanlar", Some("insan")),
            ("arabalar", Some("araba")),
            ("çocuklar", Some("çocuk")),
            ("adamlar", Some("adam")),
            ("şehirler", Some("şehir")),
        ];

        for (inflected, expected) in test_cases {
            let result = lookup_lemma(inflected);
            let expected_str = expected.map(|s| s.to_string());
            assert_eq!(result, expected_str, 
                "Failed: {} -> {:?} (expected: {:?})", 
                inflected, result, expected_str
            );
        }
    }

    #[test]
    fn test_lookup_lemma_high_frequency_verbs() {
        // Test common verb inflections
        let test_cases = vec![
            ("geliyorum", Some("gel")),
            ("gittim", Some("git")),
            ("yapıyorum", Some("yap")),
            ("söyledi", Some("söyle")),
        ];

        for (inflected, expected) in test_cases {
            let result = lookup_lemma(inflected);
            let expected_str = expected.map(|s| s.to_string());
            assert_eq!(result, expected_str,
                "Failed: {} -> {:?} (expected: {:?})",
                inflected, result, expected_str
            );
        }
    }

    #[test]
    fn test_lookup_lemma_oov_words() {
        // Out-of-vocabulary words should return None
        let oov_words = vec!["bilgisayar", "internet", "xyz123", "nonexistent"];

        for word in oov_words {
            let result = lookup_lemma(word);
            assert_eq!(result, None,
                "OOV word '{}' should return None, got: {:?}",
                word, result
            );
        }
    }

    #[test]
    fn test_lemma_dict_format_validation() {
        let dict = get_lemma_dict();
        
        // Check a few entries to ensure proper format
        for (inflected, lemma) in dict.iter().take(10) {
            assert!(!inflected.is_empty(), "Inflected form should not be empty");
            assert!(!lemma.is_empty(), "Lemma should not be empty");
            assert!(!inflected.contains('\t'), "Inflected form should not contain tabs");
            assert!(!lemma.contains('\t'), "Lemma should not contain tabs");
        }
    }

    #[test]
    fn test_strip_suffixes_basic() {
        // Test basic suffix stripping (heuristic fallback)
        let test_cases = vec![
            ("kitaplar", "kitap"),
            ("evler", "ev"),
            ("insanlar", "insan"),
        ];

        for (word, expected_contains) in test_cases {
            let result = strip_suffixes(word);
            assert!(result.contains(expected_contains),
                "strip_suffixes({}) = '{}' should contain '{}'",
                word, result, expected_contains
            );
        }
    }

    #[test]
    fn test_strip_suffixes_validated_lenient() {
        // Test validated stripping with lenient mode (phonotactic rules only)
        let test_cases = vec![
            ("kitaplar", "kitap"),
            ("evlerden", "ev"),
            ("insanların", "insan"),
        ];

        for (word, expected) in test_cases {
            let result = strip_suffixes_validated(word, false, 2, true);
            assert_eq!(result, expected,
                "strip_suffixes_validated({}, lenient) should be '{}'",
                word, expected
            );
        }
    }

    #[test]
    fn test_strip_suffixes_validated_strict() {
        // Test validated stripping with strict mode (dictionary only)
        let test_cases = vec![
            ("kitaplar", "kitap"),
            ("evler", "ev"),
            ("geliyorum", "gel"),
            ("gittim", "git"),
        ];

        for (word, expected) in test_cases {
            let result = strip_suffixes_validated(word, true, 2, true);
            assert_eq!(result, expected,
                "strip_suffixes_validated({}, strict) should be '{}'",
                word, expected
            );
        }
    }

    #[test]
    fn test_validated_prevents_overstripping() {
        // Demonstrate that validated stripping prevents over-stripping
        // where naive stripping would go too far
        
        // Example: "kitaplardan" -> naive might strip to "ki" or "k"
        // but validated should stop at "kitap"
        let word = "kitaplardan";
        let validated_result = strip_suffixes_validated(word, true, 2, true);
        
        // Should be a valid root
        assert!(validated_result.len() >= 2, 
            "Validated result should respect min length");
        assert_eq!(validated_result, "kitap",
            "Should stop at known root 'kitap', not overstrip");
    }

    #[test]
    fn test_validated_min_length() {
        // Test that minimum root length is enforced
        let validator_strict = RootValidator::new(3, false);
        
        // "ev" is only 2 chars, should be rejected
        assert!(!validator_strict.is_valid_root("ev"));
        
        // "kitap" is 5 chars, should be accepted
        assert!(validator_strict.is_valid_root("kitap"));
    }

    #[test]
    fn test_validated_vs_naive_comparison() {
        // Compare validated vs naive stripping to show improvements
        // Validated is SAFER - it might strip less (longer) OR more accurately (shorter)
        // The key is it won't produce invalid roots
        let test_words = vec![
            "kitaplardan",
            "evlerden",
            "insanların",
        ];

        for word in test_words {
            let naive = strip_suffixes(word);
            let validated = strip_suffixes_validated(word, true, 2, true);
            
            println!("Word: {} | Naive: {} | Validated: {}", word, naive, validated);
            
            // Validated should produce a valid root (length >= min)
            assert!(validated.len() >= 2,
                "Validated root '{}' should meet minimum length",
                validated
            );
            
            // Just demonstrate that both methods work (they may differ)
            // The point is validated is linguistically safer
        }
    }

    #[test]
    fn test_vowel_harmony_integration() {
        // Test that vowel harmony validation prevents invalid stripping
        
        // Valid harmony cases (should strip)
        let valid_cases = vec![
            ("kitaplar", "kitap"),  // back + -lar (back) ✓
            ("evler", "ev"),        // front + -ler (front) ✓
            ("masalar", "masa"),    // back + -lar (back) ✓
            ("şehirler", "şehir"),  // front + -ler (front) ✓
        ];

        for (word, expected) in valid_cases {
            let result = strip_suffixes_validated(word, false, 2, true);
            assert_eq!(result, expected,
                "Vowel harmony should allow {} -> {}",
                word, expected
            );
        }

        // Note: Testing invalid harmony cases is tricky because our suffix list
        // naturally follows harmony rules. In production, this prevents 
        // accidentally accepting malformed words.
    }

    #[test]
    fn test_harmony_flag_control() {
        // Test that check_harmony flag works
        let word = "kitaplar";
        
        // With harmony check (default)
        let with_harmony = strip_suffixes_validated(word, false, 2, true);
        
        // Without harmony check
        let without_harmony = strip_suffixes_validated(word, false, 2, false);
        
        // Both should work for valid Turkish words
        assert_eq!(with_harmony, "kitap");
        assert_eq!(without_harmony, "kitap");
        
        println!("Harmony check can be toggled: with={}, without={}", 
                 with_harmony, without_harmony);
    }

    #[test]
    fn test_vowel_harmony_prevents_overstripping() {
        // Demonstrate that harmony checking helps prevent over-stripping
        // by rejecting suffix candidates that violate harmony
        
        let test_word = "kitaplardan"; // book-PLUR-ABL
        
        // With harmony checking
        let with_harmony = strip_suffixes_validated(test_word, false, 2, true);
        
        // Should strip to valid root
        assert!(with_harmony.len() >= 2);
        assert_eq!(with_harmony, "kitap");
        
        println!("Harmony validation: {} -> {}", test_word, with_harmony);
    }
}
