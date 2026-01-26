/// Core Turkish NLP functionality (pure Rust, no PyO3 dependencies)
/// This module is shared between the Python bindings (lib.rs) and CLI (bin/durak.rs)

use regex::Regex;
use std::collections::HashMap;
use std::sync::OnceLock;

// Embedded resources using include_str! for zero-overhead loading
static DETACHED_SUFFIXES_DATA: &str = include_str!("../resources/tr/labels/DETACHED_SUFFIXES.txt");
static STOPWORDS_TR_DATA: &str = include_str!("../resources/tr/stopwords/base/turkish.txt");
static STOPWORDS_METADATA_DATA: &str = include_str!("../resources/tr/stopwords/metadata.json");
static STOPWORDS_SOCIAL_MEDIA_DATA: &str = include_str!("../resources/tr/stopwords/domains/social_media.txt");
static RESOURCE_METADATA: &str = include_str!("../resources/metadata.json");

static LEMMA_DICT: OnceLock<HashMap<&'static str, &'static str>> = OnceLock::new();
static TOKEN_REGEX: OnceLock<Regex> = OnceLock::new();
static DETACHED_SUFFIXES: OnceLock<Vec<&'static str>> = OnceLock::new();
static STOPWORDS_BASE: OnceLock<Vec<&'static str>> = OnceLock::new();

pub fn get_lemma_dict() -> &'static HashMap<&'static str, &'static str> {
    LEMMA_DICT.get_or_init(|| {
        let mut m = HashMap::new();
        m.insert("kitaplar", "kitap");
        m.insert("geliyorum", "gel");
        m.insert("gittim", "git");
        m
    })
}

pub fn get_token_regex() -> &'static Regex {
    TOKEN_REGEX.get_or_init(|| {
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
pub fn fast_normalize(text: &str) -> String {
    text.chars().map(|c| match c {
        'İ' => 'i',
        'I' => 'ı',
        _ => c.to_lowercase().next().unwrap_or(c)
    }).collect()
}

/// Tokenize text and return tokens with their start and end character offsets.
pub fn tokenize_with_offsets(text: &str) -> Vec<(String, usize, usize)> {
    let re = get_token_regex();
    let mut results = Vec::new();

    for caps in re.captures_iter(text) {
        if let Some(mat) = caps.get(0) {
            let token = mat.as_str().to_string();
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
pub fn tokenize_with_normalized_offsets(text: &str) -> Vec<(String, usize, usize)> {
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

/// Simple tokenization without offsets (for CLI usage)
pub fn tokenize(text: &str) -> Vec<String> {
    tokenize_with_offsets(text)
        .into_iter()
        .map(|(token, _, _)| token)
        .collect()
}

/// Tier 1: Exact Lookup
pub fn lookup_lemma(word: &str) -> Option<String> {
    let dict = get_lemma_dict();
    dict.get(word).map(|s| s.to_string())
}

/// Tier 2: Heuristic Suffix Stripping
pub fn strip_suffixes(word: &str) -> String {
    let suffixes = ["lar", "ler", "nin", "nın", "den", "dan", "du", "dün"];
    let mut current = word.to_string();
    
    let mut changed = true;
    while changed {
        changed = false;
        for suffix in suffixes {
            if current.ends_with(suffix) && current.len() > suffix.len() + 2 {
                current = current[..current.len() - suffix.len()].to_string();
                changed = true;
                break;
            }
        }
    }
    current
}

/// Get embedded detached suffixes list
pub fn get_detached_suffixes() -> Vec<String> {
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
pub fn get_stopwords_base() -> Vec<String> {
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
pub fn get_stopwords_metadata() -> String {
    STOPWORDS_METADATA_DATA.to_string()
}

/// Get embedded social media stopwords
pub fn get_stopwords_social_media() -> Vec<String> {
    STOPWORDS_SOCIAL_MEDIA_DATA
        .lines()
        .map(|line| line.trim())
        .filter(|line| !line.is_empty() && !line.starts_with('#'))
        .map(|s| s.to_string())
        .collect()
}

/// Get build information
pub fn get_build_info() -> HashMap<String, String> {
    let mut info = HashMap::new();
    info.insert("durak_version".to_string(), env!("CARGO_PKG_VERSION").to_string());
    info.insert("package_name".to_string(), env!("CARGO_PKG_NAME").to_string());
    
    if let Ok(metadata) = serde_json::from_str::<serde_json::Value>(RESOURCE_METADATA) {
        if let Some(build_date) = metadata.get("build_date").and_then(|v| v.as_str()) {
            info.insert("build_date".to_string(), build_date.to_string());
        }
    }
    
    info
}

/// Get embedded resource info
pub fn get_resource_info() -> HashMap<String, HashMap<String, String>> {
    let metadata: serde_json::Value = serde_json::from_str(RESOURCE_METADATA)
        .expect("Failed to parse embedded resource metadata");
    
    let mut result = HashMap::new();
    if let Some(resources) = metadata.get("resources").and_then(|v| v.as_object()) {
        for (key, info) in resources {
            let mut resource_map = HashMap::new();
            if let Some(obj) = info.as_object() {
                for (k, v) in obj {
                    if let Some(s) = v.as_str() {
                        resource_map.insert(k.clone(), s.to_string());
                    } else if let Some(n) = v.as_i64() {
                        resource_map.insert(k.clone(), n.to_string());
                    } else if let Some(n) = v.as_u64() {
                        resource_map.insert(k.clone(), n.to_string());
                    }
                }
            }
            result.insert(key.clone(), resource_map);
        }
    }
    result
}
