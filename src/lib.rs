use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::OnceLock;
use regex::Regex;

// Embedded resources using include_str! for zero-overhead loading
// Resources are compiled directly into the binary at build time
static DETACHED_SUFFIXES_DATA: &str = include_str!("../resources/tr/labels/DETACHED_SUFFIXES.txt");
static STOPWORDS_TR_DATA: &str = include_str!("../resources/tr/stopwords/base/turkish.txt");
static STOPWORDS_METADATA_DATA: &str = include_str!("../resources/tr/stopwords/metadata.json");
static STOPWORDS_SOCIAL_MEDIA_DATA: &str = include_str!("../resources/tr/stopwords/domains/social_media.txt");

static LEMMA_DICT: OnceLock<HashMap<&'static str, &'static str>> = OnceLock::new();
static TOKEN_REGEX: OnceLock<Regex> = OnceLock::new();
static DETACHED_SUFFIXES: OnceLock<Vec<&'static str>> = OnceLock::new();
static STOPWORDS_BASE: OnceLock<Vec<&'static str>> = OnceLock::new();

fn get_lemma_dict() -> &'static HashMap<&'static str, &'static str> {
    LEMMA_DICT.get_or_init(|| {
        let mut m = HashMap::new();
        // Tier 1: Dictionary Lookup (Mock Data for PoC)
        m.insert("kitaplar", "kitap");
        m.insert("geliyorum", "gel");
        m.insert("gittim", "git");
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

// ============================================================================
// Vowel Harmony Functions
// ============================================================================

/// Turkish vowels for phonological analysis
const BACK_VOWELS: [char; 4] = ['a', 'ı', 'o', 'u'];
const FRONT_VOWELS: [char; 4] = ['e', 'i', 'ö', 'ü'];

/// Check if a character is a back vowel (a, ı, o, u)
fn is_back_vowel(c: char) -> bool {
    BACK_VOWELS.contains(&c)
}

/// Check if a character is a front vowel (e, i, ö, ü)
fn is_front_vowel(c: char) -> bool {
    FRONT_VOWELS.contains(&c)
}

/// Get the last vowel from a word
/// Returns None if no vowel is found
fn get_last_vowel(word: &str) -> Option<char> {
    word.chars().rev().find(|&c| is_back_vowel(c) || is_front_vowel(c))
}

/// Get the first vowel from a word/suffix
/// Returns None if no vowel is found
fn get_first_vowel(word: &str) -> Option<char> {
    word.chars().find(|&c| is_back_vowel(c) || is_front_vowel(c))
}

/// Check vowel harmony between stem and suffix
/// Turkish backness harmony: both vowels must be back OR both front
/// 
/// Examples:
/// - kitap + lar → ✅ (a-a: both back)
/// - ev + ler → ✅ (e-e: both front)
/// - kitap + ler → ❌ (a-e: back-front mismatch)
/// - ev + lar → ❌ (e-a: front-back mismatch)
fn check_vowel_harmony(stem: &str, suffix: &str) -> bool {
    match (get_last_vowel(stem), get_first_vowel(suffix)) {
        (Some(stem_vowel), Some(suffix_vowel)) => {
            // Both must be back OR both must be front
            (is_back_vowel(stem_vowel) && is_back_vowel(suffix_vowel))
                || (is_front_vowel(stem_vowel) && is_front_vowel(suffix_vowel))
        }
        // If either has no vowel, cannot verify harmony → reject stripping
        _ => false,
    }
}

/// Expose vowel harmony checker to Python API
#[pyfunction]
fn check_vowel_harmony_py(stem: &str, suffix: &str) -> bool {
    check_vowel_harmony(stem, suffix)
}

// ============================================================================
// Suffix Stripping
// ============================================================================

/// Tier 2: Heuristic Suffix Stripping with Vowel Harmony Validation
/// 
/// Strips common Turkish suffixes ONLY if they respect vowel harmony rules.
/// Prevents false positives like "kitapLER" (harmony violation) from being stripped.
/// 
/// Turkish vowel harmony constraint:
/// - Backness harmony: Suffix vowel must match stem's last vowel backness
/// - Back vowels: a, ı, o, u
/// - Front vowels: e, i, ö, ü
/// 
/// Examples:
/// - kitaplar → kitap ✅ (a-a harmony)
/// - evler → ev ✅ (e-e harmony)
/// - kitapler → kitapler ❌ (a-e violation, not stripped)
#[pyfunction]
fn strip_suffixes(word: &str) -> String {
    let suffixes = ["lar", "ler", "nin", "nın", "den", "dan", "du", "dün"];
    let mut current = word.to_string();
    
    // Iterative stripping with vowel harmony validation
    let mut changed = true;
    while changed {
        changed = false;
        for suffix in suffixes {
            if current.ends_with(suffix) {
                let potential_stem = &current[..current.len() - suffix.len()];
                
                // Prevent over-stripping: stem must be at least 2 characters
                if potential_stem.len() < 2 {
                    continue;
                }
                
                // ✅ Vowel harmony check before stripping
                if check_vowel_harmony(potential_stem, suffix) {
                    current = potential_stem.to_string();
                    changed = true;
                    break; // Restart loop after stripping one suffix
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
// Tests
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    // Vowel Detection Tests
    #[test]
    fn test_is_back_vowel() {
        assert!(is_back_vowel('a'));
        assert!(is_back_vowel('ı'));
        assert!(is_back_vowel('o'));
        assert!(is_back_vowel('u'));
        
        assert!(!is_back_vowel('e'));
        assert!(!is_back_vowel('i'));
        assert!(!is_back_vowel('ö'));
        assert!(!is_back_vowel('ü'));
        assert!(!is_back_vowel('k'));
    }

    #[test]
    fn test_is_front_vowel() {
        assert!(is_front_vowel('e'));
        assert!(is_front_vowel('i'));
        assert!(is_front_vowel('ö'));
        assert!(is_front_vowel('ü'));
        
        assert!(!is_front_vowel('a'));
        assert!(!is_front_vowel('ı'));
        assert!(!is_front_vowel('o'));
        assert!(!is_front_vowel('u'));
        assert!(!is_front_vowel('t'));
    }

    #[test]
    fn test_get_last_vowel() {
        assert_eq!(get_last_vowel("kitap"), Some('a'));
        assert_eq!(get_last_vowel("ev"), Some('e'));
        assert_eq!(get_last_vowel("okul"), Some('u'));
        assert_eq!(get_last_vowel("gül"), Some('ü'));
        assert_eq!(get_last_vowel("xyz"), None); // No vowels
        assert_eq!(get_last_vowel(""), None); // Empty string
    }

    #[test]
    fn test_get_first_vowel() {
        assert_eq!(get_first_vowel("lar"), Some('a'));
        assert_eq!(get_first_vowel("ler"), Some('e'));
        assert_eq!(get_first_vowel("nın"), Some('ı'));
        assert_eq!(get_first_vowel("dün"), Some('ü'));
        assert_eq!(get_first_vowel("xyz"), None);
        assert_eq!(get_first_vowel(""), None);
    }

    // Vowel Harmony Validation Tests
    #[test]
    fn test_vowel_harmony_back_back_valid() {
        // Back vowel stem + back vowel suffix = ✅
        assert!(check_vowel_harmony("kitap", "lar")); // a-a
        assert!(check_vowel_harmony("okul", "dan")); // u-a
        assert!(check_vowel_harmony("masa", "nın")); // a-ı
    }

    #[test]
    fn test_vowel_harmony_front_front_valid() {
        // Front vowel stem + front vowel suffix = ✅
        assert!(check_vowel_harmony("ev", "ler")); // e-e
        assert!(check_vowel_harmony("gül", "den")); // ü-e
        assert!(check_vowel_harmony("şehir", "nin")); // i-i
    }

    #[test]
    fn test_vowel_harmony_back_front_invalid() {
        // Back vowel stem + front vowel suffix = ❌
        assert!(!check_vowel_harmony("kitap", "ler")); // a-e mismatch
        assert!(!check_vowel_harmony("okul", "den")); // u-e mismatch
        assert!(!check_vowel_harmony("masa", "nin")); // a-i mismatch
    }

    #[test]
    fn test_vowel_harmony_front_back_invalid() {
        // Front vowel stem + back vowel suffix = ❌
        assert!(!check_vowel_harmony("ev", "lar")); // e-a mismatch
        assert!(!check_vowel_harmony("gül", "dan")); // ü-a mismatch
        assert!(!check_vowel_harmony("şehir", "nın")); // i-ı mismatch
    }

    #[test]
    fn test_vowel_harmony_no_vowel_edge_cases() {
        // Edge case: no vowels in stem or suffix
        assert!(!check_vowel_harmony("xyz", "lar")); // No vowel in stem
        assert!(!check_vowel_harmony("kitap", "xyz")); // No vowel in suffix
        assert!(!check_vowel_harmony("xyz", "abc")); // No vowels at all
    }

    // Suffix Stripping with Harmony Tests
    #[test]
    fn test_strip_suffixes_with_harmony_valid() {
        // Should strip when harmony is valid
        assert_eq!(strip_suffixes("kitaplar"), "kitap"); // a-a harmony ✅
        assert_eq!(strip_suffixes("evler"), "ev"); // e-e harmony ✅
        assert_eq!(strip_suffixes("okuldan"), "okul"); // u-a harmony ✅
        assert_eq!(strip_suffixes("gülden"), "gül"); // ü-e harmony ✅
    }

    #[test]
    fn test_strip_suffixes_with_harmony_invalid() {
        // Should NOT strip when harmony is violated
        assert_eq!(strip_suffixes("kitapler"), "kitapler"); // a-e violation ❌
        assert_eq!(strip_suffixes("evlar"), "evlar"); // e-a violation ❌
        assert_eq!(strip_suffixes("okulden"), "okulden"); // u-e violation ❌
        assert_eq!(strip_suffixes("güldan"), "güldan"); // ü-a violation ❌
    }

    #[test]
    fn test_strip_suffixes_recursive_with_harmony() {
        // Multiple suffixes should respect harmony at each step
        // "kitaplardan" → "kitaplar" (strip "dan" with a-a harmony)
        //              → "kitap" (strip "lar" with a-a harmony)
        assert_eq!(strip_suffixes("kitaplardan"), "kitap");
        
        // "evlerden" → "evler" (strip "den" with e-e harmony)
        //           → "ev" (strip "ler" with e-e harmony)
        assert_eq!(strip_suffixes("evlerden"), "ev");
    }

    #[test]
    fn test_strip_suffixes_min_length_constraint() {
        // Should not over-strip short words (min stem length = suffix + 2)
        assert_eq!(strip_suffixes("lar"), "lar"); // Too short to strip
        assert_eq!(strip_suffixes("evler"), "ev"); // Long enough, strips
    }

    #[test]
    fn test_strip_suffixes_no_suffix() {
        // Words without recognized suffixes should remain unchanged
        assert_eq!(strip_suffixes("masa"), "masa");
        assert_eq!(strip_suffixes("bilgisayar"), "bilgisayar");
        assert_eq!(strip_suffixes("xyz"), "xyz");
    }
}
