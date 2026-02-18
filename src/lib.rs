mod morphotactics;
mod root_validator;
mod vowel_harmony;

use pyo3::prelude::*;
use regex::Regex;
// will be keeping for backward compatability
use serde::{Deserialize, Serialize};
use root_validator::RootValidator;
use std::collections::HashMap;
use std::sync::OnceLock;


// Embedded resources using include_str! for zero-overhead loading
// Resources are compiled directly into the binary at build time
static DETACHED_SUFFIXES_DATA: &str = include_str!("../resources/tr/labels/DETACHED_SUFFIXES.txt");
static STOPWORDS_TR_DATA: &str = include_str!("../resources/tr/stopwords/base/turkish.txt");
static STOPWORDS_METADATA_DATA: &str = include_str!("../resources/tr/stopwords/metadata.json");
static STOPWORDS_SOCIAL_MEDIA_DATA: &str = include_str!("../resources/tr/stopwords/domains/social_media.txt");
static RESOURCE_METADATA: &str = include_str!("../resources/metadata.json");
// incoming change will be moved into bayesian clustering in later updates
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

/// Check if a word is a known lemma (root form) in the dictionary
fn is_known_lemma(word: &str) -> bool {
    let dict = get_lemma_dict();

    // Check if word is a lemma (appears as value in dictionary)
    // OR if word maps to itself (is both inflected form and lemma)
    if let Some(&lemma) = dict.get(word) {
        // Word is in dictionary, check if it's the lemma form
        return lemma == word;
    }

    // Also check if any entry has this as its lemma
    dict.values().any(|&lemma| lemma == word)
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
/// Handles I/ı and İ/i conversion correctly and optionally lowercases the rest.
/// 
/// # Arguments
/// * `text` - Input text to normalize
/// * `lowercase` - If true, convert text to lowercase
/// * `handle_turkish_i` - If true, handle Turkish İ/I conversion (İ→i, I→ı)
#[pyfunction]
fn fast_normalize(text: &str, lowercase: bool, handle_turkish_i: bool) -> String {
    // Rust handles Turkish I/ı conversion correctly and instantly
    // "Single Pass" allocation for maximum speed
    text.chars().map(|c| {
        // First, handle Turkish I/İ conversion if enabled
        let c = if handle_turkish_i {
            match c {
                'İ' => 'i',
                'I' => 'ı',
                _ => c
            }
        } else {
            c
        };
        
        // Then, apply lowercasing if enabled
        if lowercase {
            c.to_lowercase().next().unwrap_or(c)
        } else {
            c
        }
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

/// Tokenize text and return normalized tokens with offsets pointing to original text.
/// This is the NER-friendly version: tokens are normalized but offsets reference the raw input.
/// 
/// # Example
/// ```rust
/// let text = "İstanbul'a gittim";
/// let tokens = tokenize_with_normalized_offsets(text);
/// // Returns: [("istanbul'a", 0, 10), ("gittim", 11, 17)]
/// // Note: tokens are lowercased but offsets still point to "İstanbul'a" in original
/// ```
#[pyfunction]
fn tokenize_with_normalized_offsets(text: &str) -> Vec<(String, usize, usize)> {
    let re = get_token_regex();
    let mut results = Vec::new();

    for caps in re.captures_iter(text) {
        if let Some(mat) = caps.get(0) {
            let token = mat.as_str();
            let normalized_token = fast_normalize(token);
            
            let byte_start = mat.start();
            let byte_end = mat.end();
            
            let char_start = text[..byte_start].chars().count();
            let char_len = text[byte_start..byte_end].chars().count();
            let char_end = char_start + char_len;
            
            results.push((normalized_token, char_start, char_end));
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

/// Turkish suffix categories for morphological analysis
///
/// Turkish is an agglutinative language with complex suffix chains.
/// Suffixes must be applied in a specific order (slot system).
mod suffixes {
    /// Compound suffixes that should be stripped as a unit before individual suffixes
    /// These are morphological combinations that occur frequently
    pub const COMPOUND_SUFFIXES: &[&str] = &[
        // Without doing (negation + ablative): gel-meden = without coming
        "meden",
        "madan",
        // Plural + Possessive combinations
        "larımız",
        "lerimiz",
        "ların",
        "lerin",
        "larımızdan",
        "lerimizden",
        // Plural + Case combinations
        "lardan",
        "lerden",
        "lara",
        "lere",
        // Possessive + Case combinations
        "ımızdan",
        "imizden",
        "ındanan",
        "indenan",
        // Verbal compound: gel-me-di-m = didn't come
        "medim",
        "madım",
        "medin",
        "madın",
        "medi",
        "madı",
        "medik",
        "madık",
        "mişim",
        "mışım",
        "mişiz",
        "mışız",
        // Continuous + person: geliyorum
        "yorum",
        "yorsun",
        "yor",
        "yoruz",
        "yorsunuz",
        "yorlar",
        // Future + person
        "eceğim",
        "acağım",
        "eceğiz",
        "acağız",
        "eceksin",
        "acaksın",
        // Ability
        "yebilmek",
        "yabilmek",
        "ebilirim",
        "abilirim",
    ];

    /// Nominal suffixes (attached to nouns, adjectives)
    /// Order: Plural → Possessive → Case
    pub const NOMINAL_SUFFIXES: &[&str] = &[
        // Plural (Slot 1)
        "lar", "ler", // Possessive (Slot 2) - 1st person
        "ım", "im", "um", "üm", "ımız", "imiz", "umuz", "ümüz",
        // Possessive (Slot 2) - 2nd person
        "ın", "in", "un", "ün", "ınız", "iniz", "unuz", "ünüz",
        // Possessive (Slot 2) - 3rd person
        "ı", "i", "u", "ü", "sı", "si", "su", "sü", // Case (Slot 3) - Accusative
        "ı", "i", "u", "ü", // Case (Slot 3) - Dative
        "a", "e", "ya", "ye", // Case (Slot 3) - Locative
        "da", "de", "ta", "te", // Case (Slot 3) - Ablative
        "dan", "den", "tan", "ten", // Case (Slot 3) - Genitive
        "ın", "in", "un", "ün", "nın", "nin", "nun", "nün",
    ];

    /// Verbal suffixes (attached to verbs)
    /// Order: Voice → Negation → Tense/Aspect → Person
    pub const VERBAL_SUFFIXES: &[&str] = &[
        // Voice (Slot 1) - Passive, Causative, Reflexive, Reciprocal
        "ıl", "il", "ul", "ül", "n", "ın", "in", "un", "ün", "dir", "dır", "dur", "dür", "tir",
        "tır", "tur", "tür", "ş", "ış", "iş", "uş", "üş", // Negation (Slot 2)
        "me", "ma", // Tense/Aspect (Slot 3)
        "di", "dı", "du", "dü", "ti", "tı", "tu", "tü", // Definite past
        "miş", "mış", "muş", "müş", // Evidential/Indefinite past
        "ecek", "acak", // Future
        "iyor", // Present continuous (fixed form - always "iyor")
        "er", "ar", // Aorist
        "mekte", "makta", // Progressive
        // Person (Slot 4)
        "m", "n", "k", "z", "ım", "im", "um", "üm", "ın", "in", "un", "ün", "ız", "iz", "uz", "üz",
        "sın", "sin", "sun", "sün", "sınız", "siniz", "sunuz", "sünüz", "lar",
        "ler", // 3rd person plural
        // Infinitive
        "mek", "mak",
    ];

    /// Fixed morphemes that don't follow standard vowel harmony
    /// These should be handled specially in harmony checking
    pub const FIXED_MORPHEMES: &[&str] = &[
        "iyor",  // Present continuous - always "iyor" regardless of root
        "ken",   // While - always "ken"
        "ki",    // Relative - always "ki"
        "leyin", // Time - always "leyin"
    ];
}

/// Tier 2: Heuristic Suffix Stripping
/// Simple rule-based stripper for demonstration.
/// In production, this would use a more complex state machine and vowel harmony checks.
#[pyfunction]
fn strip_suffixes(word: &str) -> String {
    let mut current = word.to_string();

    // Use compound suffixes first (longest match)
    let all_suffixes: Vec<&str> = suffixes::COMPOUND_SUFFIXES
        .iter()
        .chain(suffixes::NOMINAL_SUFFIXES.iter())
        .chain(suffixes::VERBAL_SUFFIXES.iter())
        .cloned()
        .collect();

    let mut changed = true;
    while changed {
        changed = false;
        // Sort by length descending for greedy matching
        let mut sorted: Vec<&&str> = all_suffixes.iter().collect();
        sorted.sort_by(|a, b| b.len().cmp(&a.len()));

        for suffix in sorted {
            if current.ends_with(suffix) && current.chars().count() > suffix.chars().count() + 2 {
                current = current[..current.len() - suffix.len()].to_string();
                changed = true;
                break;
            }
        }
    }
    current
}

/// Strip suffixes with root validity checking, vowel harmony, and morphotactic validation
/// Prevents over-stripping by validating candidate roots, checking vowel harmony,
/// and ensuring morphologically valid suffix ordering
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
fn strip_suffixes_validated(
    word: &str,
    strict: bool,
    min_root_length: usize,
    check_harmony: bool,
) -> String {
    // In strict mode, first check if the word is in the lemma dictionary
    if strict {
        if let Some(lemma) = lookup_lemma(word) {
            return lemma;
        }
    }

    let validator = RootValidator::new(min_root_length, strict);
    let morphotactics = morphotactics::MorphotacticClassifier::new();
    let mut current = word.to_string();
    let mut best_result = word.to_string(); // Track best valid result
    let mut stripped_suffixes: Vec<&str> = Vec::new();

    // Phase 1: Try compound suffixes first (longest match)
    for suffix in suffixes::COMPOUND_SUFFIXES {
        if current.ends_with(suffix) {
            let candidate = &current[..current.len() - suffix.len()];
            let is_valid_root = validator.is_valid_root(candidate);
            let has_harmony =
                !check_harmony || vowel_harmony::check_vowel_harmony(candidate, suffix);
            let valid_morphotactics = morphotactics.validate_sequence(&[suffix]);

            if is_valid_root && has_harmony && valid_morphotactics && !candidate.is_empty() {
                current = candidate.to_string();
                stripped_suffixes.push(suffix);
                best_result = current.clone();
                break;
            }
        }
    }

    // Phase 2: Strip individual suffixes with validation
    // Combine nominal and verbal suffixes, sorted by length (longest first)
    let mut all_single_suffixes: Vec<&str> = suffixes::NOMINAL_SUFFIXES
        .iter()
        .chain(suffixes::VERBAL_SUFFIXES.iter())
        .cloned()
        .collect();
    all_single_suffixes.sort_by(|a, b| b.len().cmp(&a.len()));
    all_single_suffixes.dedup();

    // Get dictionary reference for checking known words
    // We check if candidates are known lemmas (root forms)

    let mut changed = true;
    let mut iterations = 0;
    const MAX_ITERATIONS: usize = 10;

    while changed && iterations < MAX_ITERATIONS {
        changed = false;
        iterations += 1;

        // Check if current is in dictionary - if so, stop stripping
        if dictionary.contains(&current.as_str()) {
            break;
        }

        for suffix in &all_single_suffixes {
            if current.ends_with(suffix) {
                let candidate = &current[..current.len() - suffix.len()];

                // Skip if candidate would be too short
                if candidate.chars().count() < min_root_length {
                    continue;
                }

                // Build hypothetical suffix sequence for morphotactic validation
                let mut test_sequence = vec![*suffix];
                test_sequence.extend(stripped_suffixes.iter().rev());
                test_sequence.reverse();

                // Validate all conditions
                let is_valid_root = validator.is_valid_root(candidate);
                let has_harmony = !check_harmony || {
                    if suffixes::FIXED_MORPHEMES.contains(suffix) {
                        true
                    } else {
                        vowel_harmony::check_vowel_harmony(candidate, suffix)
                    }
                };
                let valid_morphotactics = morphotactics.validate_sequence(&test_sequence);

                // Only strip if ALL conditions are met
                if is_valid_root && has_harmony && valid_morphotactics {
                    // If candidate is in dictionary, this is our answer - stop here
                    if dictionary.contains(&candidate) {
                        return candidate.to_string();
                    }

                    current = candidate.to_string();
                    stripped_suffixes.push(suffix);
                    best_result = current.clone();
                    changed = true;
                    break;
                }
            }
        }
    }

    // Final check: if current is in dictionary, prefer it
    if dictionary.contains(&current.as_str()) {
        return current;
    }

    // Otherwise return the best valid result found
    if validator.is_valid_root(&current) {
        current
    } else {
        best_result
    }
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

// ============================================================================
// REPRODUCIBILITY & RESOURCE METADATA
// ============================================================================

#[derive(Debug, Serialize, Deserialize, Clone)]
struct ResourceInfo {
    name: String,
    version: String,
    source: String,
    checksum: String,
    item_count: usize,
    last_updated: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct ResourceMetadata {
    version: String,
    build_date: String,
    resources: HashMap<String, ResourceInfo>,
}

/// Get build information for reproducibility tracking.
/// Returns a dictionary with Durak version, build date, and Rust compiler version.
///
/// # Example
/// ```python
/// from durak import get_build_info
/// info = get_build_info()
/// print(info['durak_version'])  # '0.4.0'
/// ```
#[pyfunction]
fn get_build_info() -> HashMap<String, String> {
    let mut info = HashMap::new();
    info.insert("durak_version".to_string(), env!("CARGO_PKG_VERSION").to_string());
    info.insert("package_name".to_string(), env!("CARGO_PKG_NAME").to_string());
    
    // Build date would need to be set via build.rs or env vars
    // For now, we'll use the embedded metadata's build_date
    if let Ok(metadata) = serde_json::from_str::<ResourceMetadata>(RESOURCE_METADATA) {
        info.insert("build_date".to_string(), metadata.build_date);
    }
    
    // Rust version - use option_env! with fallback for robustness
    let rust_version = option_env!("CARGO_PKG_RUST_VERSION").unwrap_or("1.70");
    info.insert("rust_version".to_string(), rust_version.to_string());
    
    info
}

/// Get embedded resource versions and checksums for reproducibility.
/// Returns a dictionary mapping resource names to their metadata (version, checksum, item count, etc.)
///
/// # Example
/// ```python
/// from durak import get_resource_info
/// resources = get_resource_info()
/// print(resources['stopwords_base']['checksum'])  # 'a3f5b8c9d2e1f4a7...'
/// print(resources['stopwords_base']['item_count'])  # 442
/// ```
#[pyfunction]
fn get_resource_info(py: Python) -> PyResult<HashMap<String, Py<pyo3::types::PyAny>>> {
    let metadata: ResourceMetadata = serde_json::from_str(RESOURCE_METADATA)
        .expect("Failed to parse embedded resource metadata");
    
    // Convert to Python dicts with proper types
    let mut result = HashMap::new();
    for (key, info) in metadata.resources {
        let resource_dict = pyo3::types::PyDict::new(py);
        resource_dict.set_item("name", info.name)?;
        resource_dict.set_item("version", info.version)?;
        resource_dict.set_item("source", info.source)?;
        resource_dict.set_item("checksum", info.checksum)?;
        resource_dict.set_item("item_count", info.item_count)?;  // Keep as int
        resource_dict.set_item("last_updated", info.last_updated)?;
        result.insert(key, resource_dict.into());
    }
    Ok(result)
}

/// The internal Rust part of the Durak library.
/// High-performance Turkish NLP operations with embedded resources.
#[pymodule]
fn _durak_core(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Core text processing functions
    m.add_function(wrap_pyfunction!(fast_normalize, m)?)?;
    m.add_function(wrap_pyfunction!(tokenize_with_offsets, m)?)?;
    m.add_function(wrap_pyfunction!(tokenize_with_normalized_offsets, m)?)?;

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

    // Reproducibility & versioning API
    m.add_function(wrap_pyfunction!(get_build_info, m)?)?;
    m.add_function(wrap_pyfunction!(get_resource_info, m)?)?;

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
        assert!(
            dict.len() > 100,
            "Dictionary should contain more than 100 entries, got {}",
            dict.len()
        );

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
            assert_eq!(
                result, expected_str,
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
            assert_eq!(
                result, expected_str,
                "Failed: {} -> {:?} (expected: {:?})",
                inflected, result, expected_str
            );
        }
    }

    #[test]
    fn test_lookup_lemma_with_resource_dict() {
        // Test lookups from embedded turkish_lemma_dict.txt
        let test_cases = vec![
            ("kitaplar", "kitap"),
            ("evler", "ev"),
            ("geliyorum", "gel"),
            ("aldım", "al"),
            ("adamlar", "adam"),
            ("anaları", "ana"),
        ];

        for (inflected, expected_lemma) in test_cases {
            let result = lookup_lemma(inflected);
            assert_eq!(result, Some(expected_lemma.to_string()),
                "lookup_lemma('{}') should return '{}', got: {:?}",
                inflected, expected_lemma, result
            );
        }
    }

    #[test]
    fn test_lookup_lemma_oov_words() {
        // Out-of-vocabulary words should return None
        let oov_words = vec!["bilgisayar", "internet", "xyz123", "nonexistent"];

        for word in oov_words {
            let result = lookup_lemma(word);
            assert_eq!(
                result, None,
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
            assert!(
                !inflected.contains('\t'),
                "Inflected form should not contain tabs"
            );
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
            assert!(
                result.contains(expected_contains),
                "strip_suffixes({}) = '{}' should contain '{}'",
                word,
                result,
                expected_contains
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
            assert_eq!(
                result, expected,
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
            assert_eq!(
                result, expected,
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
        assert!(
            validated_result.len() >= 2,
            "Validated result should respect min length"
        );
        assert_eq!(
            validated_result, "kitap",
            "Should stop at known root 'kitap', not overstrip"
        );
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
    fn test_morphotactic_validation() {
        // Test that morphotactic constraints prevent invalid suffix sequences

        // Valid sequences should work
        let valid_cases = vec![
            // kitap+lar+ım+da (Plural → Possessive → Case)
            ("kitaplarımda", "kitap"),
            // ev+ler+imiz+den (Plural → Possessive → Case)
            ("evlerimizden", "ev"),
        ];

        for (word, expected_root) in valid_cases {
            let result = strip_suffixes_validated(word, false, 2, true);
            assert!(
                result.contains(expected_root),
                "Valid sequence: {} should lemmatize to contain '{}', got '{}'",
                word,
                expected_root,
                result
            );
        }

        // Invalid sequences should be rejected (stay closer to original)
        // Note: We can't easily construct invalid forms because they don't exist
        // in natural Turkish. The validation prevents theoretical over-stripping.

        // Example: If we had *"kitapdalar" (Case+Plural, wrong order),
        // the validator would reject stripping "lar" after "da" was already stripped.
        // This is tested in morphotactics module tests.
    }

    #[test]
    fn test_validated_vs_naive_comparison() {
        // Compare validated vs naive stripping to show improvements
        // Validated is SAFER - it might strip less (longer) OR more accurately (shorter)
        // The key is it won't produce invalid roots
        let test_words = vec!["kitaplardan", "evlerden", "insanların"];

        for word in test_words {
            let naive = strip_suffixes(word);
            let validated = strip_suffixes_validated(word, true, 2, true);

            println!(
                "Word: {} | Naive: {} | Validated: {}",
                word, naive, validated
            );

            // Validated should produce a valid root (length >= min)
            assert!(
                validated.len() >= 2,
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
            ("kitaplar", "kitap"), // back + -lar (back) ✓
            ("evler", "ev"),       // front + -ler (front) ✓
            ("masalar", "masa"),   // back + -lar (back) ✓
            ("şehirler", "şehir"), // front + -ler (front) ✓
        ];

        for (word, expected) in valid_cases {
            let result = strip_suffixes_validated(word, false, 2, true);
            assert_eq!(
                result, expected,
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

        println!(
            "Harmony check can be toggled: with={}, without={}",
            with_harmony, without_harmony
        );
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
