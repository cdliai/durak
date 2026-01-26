use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::OnceLock;
use regex::Regex;
use serde::{Deserialize, Serialize};

// Embedded resources using include_str! for zero-overhead loading
// Resources are compiled directly into the binary at build time
static DETACHED_SUFFIXES_DATA: &str = include_str!("../resources/tr/labels/DETACHED_SUFFIXES.txt");
static STOPWORDS_TR_DATA: &str = include_str!("../resources/tr/stopwords/base/turkish.txt");
static STOPWORDS_METADATA_DATA: &str = include_str!("../resources/tr/stopwords/metadata.json");
static STOPWORDS_SOCIAL_MEDIA_DATA: &str = include_str!("../resources/tr/stopwords/domains/social_media.txt");
static RESOURCE_METADATA: &str = include_str!("../resources/metadata.json");

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

// ============================================================================
// Reproducibility & Versioning API
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
    
    // Rust version (optional, may not be available in all builds)
    #[cfg(feature = "rust_version")]
    info.insert("rust_version".to_string(), env!("CARGO_PKG_RUST_VERSION").to_string());
    
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
fn get_resource_info() -> HashMap<String, HashMap<String, String>> {
    let metadata: ResourceMetadata = serde_json::from_str(RESOURCE_METADATA)
        .expect("Failed to parse embedded resource metadata");
    
    // Convert to Python-friendly format (all strings for simplicity)
    let mut result = HashMap::new();
    for (key, info) in metadata.resources {
        let mut resource_map = HashMap::new();
        resource_map.insert("name".to_string(), info.name);
        resource_map.insert("version".to_string(), info.version);
        resource_map.insert("source".to_string(), info.source);
        resource_map.insert("checksum".to_string(), info.checksum);
        resource_map.insert("item_count".to_string(), info.item_count.to_string());
        resource_map.insert("last_updated".to_string(), info.last_updated);
        result.insert(key, resource_map);
    }
    result
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
