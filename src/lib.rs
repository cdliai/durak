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

// ========== Turkish Syllabification ==========

/// Check if a character is a Turkish vowel
fn is_vowel(c: char) -> bool {
    matches!(
        c.to_lowercase().next().unwrap_or(c),
        'a' | 'e' | 'ı' | 'i' | 'o' | 'ö' | 'u' | 'ü' | 'â' | 'î' | 'û'
    )
}

/// Check if a character is a Turkish consonant
fn is_consonant(c: char) -> bool {
    c.is_alphabetic() && !is_vowel(c)
}

/// Syllabify a Turkish word according to linguistic rules.
/// Returns a vector of syllables.
/// 
/// Turkish syllable structure follows (C)(C)V(C)(C) where V is mandatory.
/// 
/// Rules (based on Turkish phonotactics):
/// - V.V       → always break between vowels (o-ku)
/// - V.CV      → break before consonant (a-çık)
/// - VC.CV     → break between consonants (kit-ap, mer-ha-ba)
/// - VCC.V     → take first consonant (an-la-mak, İs-tan-bul)
/// - VCCC.V    → split at sonority boundary (typically VC.CCV)
/// 
/// # Examples
/// ```
/// syllabify("kitap")    → ["ki", "tap"]
/// syllabify("merhaba")  → ["mer", "ha", "ba"]
/// syllabify("okul")     → ["o", "kul"]
/// syllabify("İstanbul") → ["İs", "tan", "bul"]
/// syllabify("anlamak")  → ["an", "la", "mak"]
/// ```
#[pyfunction]
fn syllabify(word: &str) -> Vec<String> {
    if word.is_empty() {
        return vec![];
    }

    let chars: Vec<char> = word.chars().collect();
    let len = chars.len();
    
    if len == 0 {
        return vec![];
    }
    
    // Single character words return as-is
    if len == 1 {
        return vec![word.to_string()];
    }

    let mut syllables: Vec<String> = Vec::new();
    let mut current = String::new();
    let mut i = 0;

    while i < len {
        current.push(chars[i]);
        
        // Check if current character is a vowel
        if is_vowel(chars[i]) {
            // Look ahead to determine syllable boundary
            if i + 1 >= len {
                // End of word, close syllable
                syllables.push(current.clone());
                current.clear();
                break;
            }
            
            let next_char = chars[i + 1];
            
            // V.V pattern: always break after current vowel
            if is_vowel(next_char) {
                syllables.push(current.clone());
                current.clear();
                i += 1;
                continue;
            }
            
            // Next is consonant, need to look further
            if is_consonant(next_char) {
                // Count consecutive consonants ahead
                let mut consonant_count = 0;
                let mut j = i + 1;
                while j < len && is_consonant(chars[j]) {
                    consonant_count += 1;
                    j += 1;
                }
                
                // If no vowel after consonants, take all remaining
                if j >= len {
                    // Reached end, add all remaining consonants to current syllable
                    while i + 1 < len {
                        i += 1;
                        current.push(chars[i]);
                    }
                    syllables.push(current.clone());
                    current.clear();
                    break;
                }
                
                // There's a vowel after consonants
                // Apply Turkish syllabification rules:
                match consonant_count {
                    1 => {
                        // VCV pattern → V.CV (break before consonant)
                        // The consonant goes with the next syllable
                        syllables.push(current.clone());
                        current.clear();
                    }
                    2 => {
                        // VCCV pattern → VC.CV (split between consonants)
                        // Take first consonant with current syllable
                        i += 1;
                        current.push(chars[i]);
                        syllables.push(current.clone());
                        current.clear();
                    }
                    _ => {
                        // VCC...V pattern (3+ consonants) → VC.C...V
                        // Take first consonant with current syllable
                        i += 1;
                        current.push(chars[i]);
                        syllables.push(current.clone());
                        current.clear();
                    }
                }
            }
        }
        
        i += 1;
    }
    
    // Add any remaining characters
    if !current.is_empty() {
        syllables.push(current);
    }

    syllables
}

/// Syllabify a Turkish word and join with a separator.
/// 
/// # Examples
/// ```
/// syllabify_with_separator("merhaba", "-")  → "mer-ha-ba"
/// syllabify_with_separator("kitap", "·")    → "ki·tap"
/// ```
#[pyfunction]
fn syllabify_with_separator(word: &str, separator: &str) -> String {
    syllabify(word).join(separator)
}

/// Count syllables in a Turkish word.
/// Useful for poetry analysis and filtering.
/// 
/// # Examples
/// ```
/// syllable_count("ev")       → 1
/// syllable_count("kitap")    → 2
/// syllable_count("merhaba")  → 3
/// ```
#[pyfunction]
fn syllable_count(word: &str) -> usize {
    syllabify(word).len()
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

    // Syllabification functions
    m.add_function(wrap_pyfunction!(syllabify, m)?)?;
    m.add_function(wrap_pyfunction!(syllabify_with_separator, m)?)?;
    m.add_function(wrap_pyfunction!(syllable_count, m)?)?;

    // Embedded resource accessors
    m.add_function(wrap_pyfunction!(get_detached_suffixes, m)?)?;
    m.add_function(wrap_pyfunction!(get_stopwords_base, m)?)?;
    m.add_function(wrap_pyfunction!(get_stopwords_metadata, m)?)?;
    m.add_function(wrap_pyfunction!(get_stopwords_social_media, m)?)?;

    Ok(())
}
