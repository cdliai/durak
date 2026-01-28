/// Turkish Vowel Harmony Checker
/// 
/// Implements vowel harmony rules for Turkish morphology:
/// - Front/Back harmony: Front vowels (e,i,ö,ü) vs Back vowels (a,ı,o,u)
/// - Rounded/Unrounded harmony: Rounded (o,ö,u,ü) vs Unrounded (a,e,ı,i)
/// 
/// Used to validate suffix attachment in lemmatization and morphological analysis.

#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum VowelClass {
    /// Front unrounded: e, i
    FrontUnrounded,
    /// Front rounded: ö, ü
    FrontRounded,
    /// Back unrounded: a, ı
    BackUnrounded,
    /// Back rounded: o, u
    BackRounded,
}

impl VowelClass {
    /// Check if this vowel class is front (e, i, ö, ü)
    pub fn is_front(&self) -> bool {
        matches!(self, VowelClass::FrontUnrounded | VowelClass::FrontRounded)
    }

    /// Check if this vowel class is back (a, ı, o, u)
    #[allow(dead_code)]
    pub fn is_back(&self) -> bool {
        !self.is_front()
    }

    /// Check if this vowel class is rounded (o, ö, u, ü)
    #[allow(dead_code)]
    pub fn is_rounded(&self) -> bool {
        matches!(self, VowelClass::FrontRounded | VowelClass::BackRounded)
    }
}

/// Get the vowel class of a character
/// Returns None if the character is not a Turkish vowel
pub fn get_vowel_class(c: char) -> Option<VowelClass> {
    match c.to_lowercase().next()? {
        'e' | 'i' => Some(VowelClass::FrontUnrounded),
        'ö' | 'ü' => Some(VowelClass::FrontRounded),
        'a' | 'ı' => Some(VowelClass::BackUnrounded),
        'o' | 'u' => Some(VowelClass::BackRounded),
        _ => None,
    }
}

/// Get the last vowel class in a word (used to determine suffix harmony)
pub fn get_last_vowel_class(word: &str) -> Option<VowelClass> {
    word.chars()
        .rev()
        .find_map(get_vowel_class)
}

/// Check if a suffix harmonizes with the given root vowel class
/// 
/// # Turkish Vowel Harmony Rules:
/// 
/// 1. **Front/Back Harmony** (applies to all suffixes):
///    - Front vowels (e, i, ö, ü) → Front suffixes
///    - Back vowels (a, ı, o, u) → Back suffixes
/// 
/// 2. **Rounding Harmony** (applies after front/back is determined):
///    - After rounded vowels: May use rounded suffixes
///    - After unrounded vowels: Typically use unrounded suffixes
/// 
/// # Examples:
/// - kitap (back) + -lar = kitaplar ✓ (back-back)
/// - kitap (back) + -ler = *kitapler ✗ (back-front, invalid!)
/// - ev (front) + -ler = evler ✓ (front-front)
/// - ev (front) + -lar = *evlar ✗ (front-back, invalid!)
pub fn check_harmony(root_vowel: VowelClass, suffix_vowel: VowelClass) -> bool {
    // Primary rule: Front/Back must match
    if root_vowel.is_front() != suffix_vowel.is_front() {
        return false;
    }

    // Secondary rule: Rounding harmony (more lenient)
    // In Turkish, rounding harmony is complex and has exceptions
    // For now, we allow any rounding combination within the same front/back class
    // (This can be refined with more specific rules later)
    true
}

/// Check if a suffix string harmonizes with a root string
/// 
/// Validates that all vowels in the suffix harmonize with the last vowel in the root.
/// 
/// # Arguments
/// * `root` - The root word (e.g., "kitap")
/// * `suffix` - The suffix to check (e.g., "lar")
/// 
/// # Returns
/// * `true` if the suffix harmonizes with the root
/// * `false` if harmony is violated
/// * `false` if root has no vowels (cannot determine harmony)
pub fn check_vowel_harmony(root: &str, suffix: &str) -> bool {
    // Get the last vowel in the root
    let root_vowel = match get_last_vowel_class(root) {
        Some(v) => v,
        None => return false, // No vowels in root = cannot validate
    };

    // Check all vowels in the suffix
    let suffix_vowels: Vec<VowelClass> = suffix
        .chars()
        .filter_map(get_vowel_class)
        .collect();

    // Empty suffix or suffix with no vowels = always valid
    if suffix_vowels.is_empty() {
        return true;
    }

    // All suffix vowels must harmonize with the root vowel
    suffix_vowels.iter().all(|&v| check_harmony(root_vowel, v))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_vowel_classification() {
        // Front unrounded
        assert_eq!(get_vowel_class('e'), Some(VowelClass::FrontUnrounded));
        assert_eq!(get_vowel_class('i'), Some(VowelClass::FrontUnrounded));
        assert_eq!(get_vowel_class('E'), Some(VowelClass::FrontUnrounded));
        assert_eq!(get_vowel_class('İ'), Some(VowelClass::FrontUnrounded));

        // Front rounded
        assert_eq!(get_vowel_class('ö'), Some(VowelClass::FrontRounded));
        assert_eq!(get_vowel_class('ü'), Some(VowelClass::FrontRounded));

        // Back unrounded
        assert_eq!(get_vowel_class('a'), Some(VowelClass::BackUnrounded));
        assert_eq!(get_vowel_class('ı'), Some(VowelClass::BackUnrounded));

        // Back rounded
        assert_eq!(get_vowel_class('o'), Some(VowelClass::BackRounded));
        assert_eq!(get_vowel_class('u'), Some(VowelClass::BackRounded));

        // Non-vowels
        assert_eq!(get_vowel_class('k'), None);
        assert_eq!(get_vowel_class('t'), None);
        assert_eq!(get_vowel_class('m'), None);
    }

    #[test]
    fn test_last_vowel_extraction() {
        assert_eq!(get_last_vowel_class("kitap"), Some(VowelClass::BackUnrounded));
        assert_eq!(get_last_vowel_class("ev"), Some(VowelClass::FrontUnrounded));
        assert_eq!(get_last_vowel_class("göz"), Some(VowelClass::FrontRounded));
        assert_eq!(get_last_vowel_class("yol"), Some(VowelClass::BackRounded));
        assert_eq!(get_last_vowel_class("xyz"), None); // No vowels
    }

    #[test]
    fn test_harmony_valid_cases() {
        // Back root + back suffix
        assert!(check_vowel_harmony("kitap", "lar")); // kitaplar ✓
        assert!(check_vowel_harmony("adam", "dan")); // adamdan ✓
        assert!(check_vowel_harmony("yol", "dan")); // yoldan ✓

        // Front root + front suffix
        assert!(check_vowel_harmony("ev", "ler")); // evler ✓
        assert!(check_vowel_harmony("şehir", "den")); // şehirden ✓
        assert!(check_vowel_harmony("göz", "ler")); // gözler ✓
    }

    #[test]
    fn test_harmony_invalid_cases() {
        // Back root + front suffix (INVALID)
        assert!(!check_vowel_harmony("kitap", "ler")); // *kitapler ✗
        assert!(!check_vowel_harmony("adam", "den")); // *adamden ✗

        // Front root + back suffix (INVALID)
        assert!(!check_vowel_harmony("ev", "lar")); // *evlar ✗
        assert!(!check_vowel_harmony("şehir", "dan")); // *şehirdan ✗
    }

    #[test]
    fn test_harmony_with_multi_vowel_suffixes() {
        // Test suffixes with multiple vowels
        assert!(check_vowel_harmony("kitap", "ların")); // kitapların ✓ (back-back)
        assert!(check_vowel_harmony("ev", "lerin")); // evlerin ✓ (front-front)
        assert!(!check_vowel_harmony("kitap", "lerin")); // *kitaplerin ✗ (back-front)
    }

    #[test]
    fn test_harmony_consonant_only_suffixes() {
        // Suffixes with no vowels should always pass
        assert!(check_vowel_harmony("kitap", "m")); // kitabım (possessive)
        assert!(check_vowel_harmony("ev", "m")); // evim
    }

    #[test]
    fn test_harmony_edge_cases() {
        // Root with no vowels
        assert!(!check_vowel_harmony("xyz", "lar")); // Cannot validate

        // Empty suffix
        assert!(check_vowel_harmony("kitap", "")); // Always valid

        // Single character root
        assert!(check_vowel_harmony("a", "lar")); // back-back ✓
        assert!(check_vowel_harmony("e", "ler")); // front-front ✓
    }

    #[test]
    fn test_real_world_examples() {
        // Real Turkish words with correct harmony
        let valid_pairs = vec![
            ("masa", "lar"), // masalar
            ("kalem", "ler"), // kalemler
            ("okul", "dan"), // okuldan
            ("öğrenci", "den"), // öğrenciden
            ("bilgisayar", "ların"), // bilgisayarların
            ("telefon", "lar"), // telefonlar
        ];

        for (root, suffix) in valid_pairs {
            assert!(
                check_vowel_harmony(root, suffix),
                "{} + {} should be valid",
                root,
                suffix
            );
        }

        // Real Turkish words with incorrect harmony (should fail)
        let invalid_pairs = vec![
            ("masa", "ler"), // *maseler
            ("kalem", "lar"), // *kalemlar
            ("okul", "den"), // *okulden
            ("öğrenci", "dan"), // *öğrencidan
        ];

        for (root, suffix) in invalid_pairs {
            assert!(
                !check_vowel_harmony(root, suffix),
                "{} + {} should be invalid",
                root,
                suffix
            );
        }
    }
}
