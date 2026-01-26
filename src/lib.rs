use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::OnceLock;
use regex::Regex;

/// Token with offset mapping to original text.
/// Used for NER and other tasks requiring exact alignment with raw input.
/// Note: start and end are BYTE offsets (not character offsets) for efficiency.
/// This matches how Rust string slicing works and is compatible with modern NLP tools.
#[pyclass]
#[derive(Debug, Clone)]
pub struct Token {
    /// The token text (may be normalized)
    #[pyo3(get)]
    pub text: String,
    /// Start byte offset in the original raw text
    #[pyo3(get)]
    pub start: usize,
    /// End byte offset in the original raw text
    #[pyo3(get)]
    pub end: usize,
}

#[pymethods]
impl Token {
    #[new]
    fn new(text: String, start: usize, end: usize) -> Self {
        Token { text, start, end }
    }

    fn __repr__(&self) -> String {
        format!("Token(text='{}', start={}, end={})", self.text, self.start, self.end)
    }
}

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

/// Tokenize and normalize text while preserving offset mapping to the original raw text.
/// This is the key function for NER and other research tasks where you need both
/// normalized tokens AND their exact position in the original input.
/// Returns a list of Token objects with { text: normalized_token, start, end }.
/// Note: start/end are BYTE offsets (compatible with Rust slicing and modern NLP tools).
#[pyfunction]
fn tokenize_normalized(text: &str) -> Vec<Token> {
    let re = get_token_regex();
    let mut results = Vec::new();

    for caps in re.captures_iter(text) {
        if let Some(mat) = caps.get(0) {
            let original_token = mat.as_str();
            
            // Normalize the token text while keeping original byte offsets
            let normalized_text = fast_normalize(original_token);
            
            // Use byte offsets directly from regex (efficient and correct for Rust slicing)
            let byte_start = mat.start();
            let byte_end = mat.end();
            
            results.push(Token {
                text: normalized_text,
                start: byte_start,
                end: byte_end,
            });
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

/// The internal Rust part of the Durak library.
/// High-performance Turkish NLP operations with embedded resources.
#[pymodule]
fn _durak_core(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
    // Token class
    m.add_class::<Token>()?;

    // Core text processing functions
    m.add_function(wrap_pyfunction!(fast_normalize, m)?)?;
    m.add_function(wrap_pyfunction!(tokenize_with_offsets, m)?)?;
    m.add_function(wrap_pyfunction!(tokenize_normalized, m)?)?;

    // Lemmatization functions
    m.add_function(wrap_pyfunction!(lookup_lemma, m)?)?;
    m.add_function(wrap_pyfunction!(strip_suffixes, m)?)?;

    // Embedded resource accessors
    m.add_function(wrap_pyfunction!(get_detached_suffixes, m)?)?;
    m.add_function(wrap_pyfunction!(get_stopwords_base, m)?)?;
    m.add_function(wrap_pyfunction!(get_stopwords_metadata, m)?)?;
    m.add_function(wrap_pyfunction!(get_stopwords_social_media, m)?)?;

    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_tokenize_normalized_preserves_offsets() {
        // Test case: "İstanbul'da" should normalize to "istanbul'da"
        // but keep original byte offsets pointing to raw text
        let text = "İstanbul'da güzel";
        let tokens = tokenize_normalized(text);
        
        assert_eq!(tokens.len(), 2);
        
        // First token: "İstanbul'da" → "istanbul'da"
        assert_eq!(tokens[0].text, "istanbul'da");
        assert_eq!(tokens[0].start, 0);
        // "İstanbul'da" = İ(2) + s(1) + t(1) + a(1) + n(1) + b(1) + u(1) + l(1) + '(1) + d(1) + a(1) = 12 bytes
        assert_eq!(tokens[0].end, 12);
        
        // Verify we can extract original from byte offsets
        let original_token = &text[tokens[0].start..tokens[0].end];
        assert_eq!(original_token, "İstanbul'da");
        
        // Second token: "güzel" → "güzel"
        assert_eq!(tokens[1].text, "güzel");
        assert_eq!(tokens[1].start, 13); // After space (byte 12)
        // "güzel" = g(1) + ü(2) + z(1) + e(1) + l(1) = 6 bytes
        assert_eq!(tokens[1].end, 19);
    }

    #[test]
    fn test_turkish_i_normalization_with_offsets() {
        // Critical test: Turkish I/İ and i/ı handling
        let text = "IŞIK İNSAN";
        let tokens = tokenize_normalized(text);
        
        assert_eq!(tokens.len(), 2);
        
        // "IŞIK" should normalize to "ışık"
        assert_eq!(tokens[0].text, "ışık");
        assert_eq!(tokens[0].start, 0);
        // I=1, Ş=2, I=1, K=1 = 5 bytes
        assert_eq!(tokens[0].end, 5);
        
        // "İNSAN" should normalize to "insan"
        assert_eq!(tokens[1].text, "insan");
        assert_eq!(tokens[1].start, 6); // After space
        // İ=2, N=1, S=1, A=1, N=1 = 6 bytes
        assert_eq!(tokens[1].end, 12);
        
        // Verify original extraction using byte offsets
        assert_eq!(&text[tokens[0].start..tokens[0].end], "IŞIK");
        assert_eq!(&text[tokens[1].start..tokens[1].end], "İNSAN");
    }

    #[test]
    fn test_offset_mapping_with_whitespace() {
        // Whitespace should not be tokenized, byte offsets should skip it correctly
        let text = "  Merhaba   dünya  ";
        let tokens = tokenize_normalized(text);
        
        assert_eq!(tokens.len(), 2);
        assert_eq!(tokens[0].text, "merhaba");
        assert_eq!(tokens[0].start, 2); // Skips leading whitespace
        assert_eq!(tokens[0].end, 9); // "Merhaba" = 7 bytes
        
        assert_eq!(tokens[1].text, "dünya");
        assert_eq!(tokens[1].start, 12); // Accounts for whitespace between tokens
        // "dünya" = d(1) + ü(2) + n(1) + y(1) + a(1) = 6 bytes
        assert_eq!(tokens[1].end, 18);
    }

    #[test]
    fn test_ner_use_case() {
        // Realistic NER scenario: extract entities with their byte positions
        let text = "Ahmet İstanbul'a gitti.";
        let tokens = tokenize_normalized(text);
        
        // Should tokenize: ["ahmet", "istanbul'a", "gitti", "."]
        assert_eq!(tokens.len(), 4);
        
        // Entity: "Ahmet" at byte position 0-5
        assert_eq!(tokens[0].text, "ahmet");
        assert_eq!(&text[tokens[0].start..tokens[0].end], "Ahmet");
        
        // Entity: "İstanbul'a" 
        assert_eq!(tokens[1].text, "istanbul'a");
        assert_eq!(&text[tokens[1].start..tokens[1].end], "İstanbul'a");
        
        // Verify we can label entities with original case preserved
        let entity_label = format!("{} (PER)", &text[tokens[0].start..tokens[0].end]);
        assert_eq!(entity_label, "Ahmet (PER)");
    }
}
