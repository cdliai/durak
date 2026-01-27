/// Turkish Morphotactics: Suffix Ordering Constraints
/// 
/// Implements Turkish morpheme sequence rules to validate suffix ordering.
/// Prevents morphologically invalid sequences like *"kitap+da+lar" (Case before Plural).
/// 
/// # Turkish Suffix Slot Sequence (Nominal):
/// 
/// ROOT → [Plural] → [Possessive] → [Case] → [Copula]
/// 
/// Examples:
/// - kitap+lar+ım+da (book+PL+1SG.POSS+LOC) ✓
/// - ev+im+de (house+1SG.POSS+LOC) ✓
/// - *kitap+da+lar (Case before Plural) ✗
/// - *ev+lar+da+im (Case before Possessive) ✗
/// 
/// # Turkish Suffix Slot Sequence (Verbal):
/// 
/// ROOT → [Voice] → [Negation] → [Tense/Aspect] → [Person] → [Copula]
/// 
/// Examples:
/// - gel+di+m (come+PAST+1SG) ✓
/// - yap+ıl+dı (do+PASS+PAST) ✓
/// - *gel+m+di (Person before Tense) ✗

use std::collections::HashMap;

/// Morpheme slot types for Turkish nominal morphology
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub enum NominalSlot {
    /// Plural markers: -lar, -ler
    Plural = 1,
    /// Possessive markers: -ım, -im, -um, -üm, etc.
    Possessive = 2,
    /// Case markers: -da, -de, -dan, -den, -ın, -in, etc.
    Case = 3,
    /// Copula (to be): -dır, -dir, etc.
    Copula = 4,
}

/// Morpheme slot types for Turkish verbal morphology
#[derive(Debug, Clone, Copy, PartialEq, Eq, Hash, PartialOrd, Ord)]
pub enum VerbalSlot {
    /// Voice markers: -ıl, -il (passive), -ın, -in (reflexive)
    Voice = 1,
    /// Negation: -ma, -me
    Negation = 2,
    /// Tense/Aspect: -di, -dı, -yor, -acak, etc.
    TenseAspect = 3,
    /// Person markers: -m, -n, -k, -z, etc.
    Person = 4,
    /// Copula: -dır, -dir
    Copula = 5,
}

/// Suffix classification for morphotactic validation
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SuffixSlot {
    Nominal(NominalSlot),
    Verbal(VerbalSlot),
    /// Unknown suffix (not validated)
    Unknown,
}

/// Map Turkish suffixes to their morphotactic slots
pub struct MorphotacticClassifier {
    nominal_map: HashMap<&'static str, NominalSlot>,
    verbal_map: HashMap<&'static str, VerbalSlot>,
}

impl MorphotacticClassifier {
    /// Create a new morphotactic classifier with predefined suffix rules
    pub fn new() -> Self {
        let mut nominal_map = HashMap::new();
        let mut verbal_map = HashMap::new();

        // Nominal Plural
        nominal_map.insert("lar", NominalSlot::Plural);
        nominal_map.insert("ler", NominalSlot::Plural);

        // Nominal Possessive
        nominal_map.insert("ım", NominalSlot::Possessive);
        nominal_map.insert("im", NominalSlot::Possessive);
        nominal_map.insert("um", NominalSlot::Possessive);
        nominal_map.insert("üm", NominalSlot::Possessive);
        nominal_map.insert("ımız", NominalSlot::Possessive);
        nominal_map.insert("imiz", NominalSlot::Possessive);
        nominal_map.insert("umuz", NominalSlot::Possessive);
        nominal_map.insert("ümüz", NominalSlot::Possessive);

        // Nominal Case (Locative, Ablative, Genitive, Dative, Accusative)
        nominal_map.insert("da", NominalSlot::Case);
        nominal_map.insert("de", NominalSlot::Case);
        nominal_map.insert("ta", NominalSlot::Case);
        nominal_map.insert("te", NominalSlot::Case);
        nominal_map.insert("dan", NominalSlot::Case);
        nominal_map.insert("den", NominalSlot::Case);
        nominal_map.insert("tan", NominalSlot::Case);
        nominal_map.insert("ten", NominalSlot::Case);
        nominal_map.insert("ın", NominalSlot::Case);
        nominal_map.insert("in", NominalSlot::Case);
        nominal_map.insert("un", NominalSlot::Case);
        nominal_map.insert("ün", NominalSlot::Case);
        nominal_map.insert("nın", NominalSlot::Case);
        nominal_map.insert("nin", NominalSlot::Case);
        nominal_map.insert("nun", NominalSlot::Case);
        nominal_map.insert("nün", NominalSlot::Case);
        nominal_map.insert("a", NominalSlot::Case);
        nominal_map.insert("e", NominalSlot::Case);
        nominal_map.insert("ya", NominalSlot::Case);
        nominal_map.insert("ye", NominalSlot::Case);
        nominal_map.insert("ı", NominalSlot::Case);
        nominal_map.insert("i", NominalSlot::Case);
        nominal_map.insert("u", NominalSlot::Case);
        nominal_map.insert("ü", NominalSlot::Case);

        // Verbal Voice
        verbal_map.insert("ıl", VerbalSlot::Voice);
        verbal_map.insert("il", VerbalSlot::Voice);
        verbal_map.insert("ul", VerbalSlot::Voice);
        verbal_map.insert("ül", VerbalSlot::Voice);
        verbal_map.insert("ın", VerbalSlot::Voice);
        verbal_map.insert("in", VerbalSlot::Voice);
        verbal_map.insert("un", VerbalSlot::Voice);
        verbal_map.insert("ün", VerbalSlot::Voice);

        // Verbal Negation
        verbal_map.insert("ma", VerbalSlot::Negation);
        verbal_map.insert("me", VerbalSlot::Negation);

        // Verbal Tense/Aspect
        verbal_map.insert("di", VerbalSlot::TenseAspect);
        verbal_map.insert("dı", VerbalSlot::TenseAspect);
        verbal_map.insert("du", VerbalSlot::TenseAspect);
        verbal_map.insert("dü", VerbalSlot::TenseAspect);
        verbal_map.insert("ti", VerbalSlot::TenseAspect);
        verbal_map.insert("tı", VerbalSlot::TenseAspect);
        verbal_map.insert("tu", VerbalSlot::TenseAspect);
        verbal_map.insert("tü", VerbalSlot::TenseAspect);
        verbal_map.insert("yor", VerbalSlot::TenseAspect);
        verbal_map.insert("acak", VerbalSlot::TenseAspect);
        verbal_map.insert("ecek", VerbalSlot::TenseAspect);
        verbal_map.insert("mış", VerbalSlot::TenseAspect);
        verbal_map.insert("miş", VerbalSlot::TenseAspect);
        verbal_map.insert("muş", VerbalSlot::TenseAspect);
        verbal_map.insert("müş", VerbalSlot::TenseAspect);

        // Verbal Person
        verbal_map.insert("m", VerbalSlot::Person);
        verbal_map.insert("n", VerbalSlot::Person);
        verbal_map.insert("k", VerbalSlot::Person);
        verbal_map.insert("z", VerbalSlot::Person);
        verbal_map.insert("ım", VerbalSlot::Person);
        verbal_map.insert("im", VerbalSlot::Person);
        verbal_map.insert("um", VerbalSlot::Person);
        verbal_map.insert("üm", VerbalSlot::Person);
        verbal_map.insert("nız", VerbalSlot::Person);
        verbal_map.insert("niz", VerbalSlot::Person);
        verbal_map.insert("nuz", VerbalSlot::Person);
        verbal_map.insert("nüz", VerbalSlot::Person);

        Self {
            nominal_map,
            verbal_map,
        }
    }

    /// Classify a suffix into its morphotactic slot
    /// Note: Some suffixes (e.g., -ım, -im, -um, -üm) can be both nominal possessive
    /// and verbal person markers. We prefer verbal interpretation when validating sequences.
    pub fn classify(&self, suffix: &str) -> SuffixSlot {
        // Check verbal first to handle ambiguous suffixes (e.g., -um can be both)
        if let Some(&slot) = self.verbal_map.get(suffix) {
            return SuffixSlot::Verbal(slot);
        }

        // Check nominal
        if let Some(&slot) = self.nominal_map.get(suffix) {
            return SuffixSlot::Nominal(slot);
        }

        SuffixSlot::Unknown
    }

    /// Validate a sequence of suffixes
    /// Returns true if the sequence is morphotactically valid
    /// 
    /// For ambiguous suffixes (e.g., -ım can be possessive or person marker),
    /// we try both nominal and verbal interpretations and accept if either is valid.
    pub fn validate_sequence(&self, suffixes: &[&str]) -> bool {
        if suffixes.is_empty() {
            return true;
        }

        // Check if any suffix appears in both paradigms (ambiguous)
        let has_ambiguous = suffixes.iter().any(|s| {
            self.nominal_map.contains_key(s) && self.verbal_map.contains_key(s)
        });

        if has_ambiguous {
            // Try both paradigms
            let nominal_valid = self.try_validate_as_nominal(suffixes);
            let verbal_valid = self.try_validate_as_verbal(suffixes);
            return nominal_valid || verbal_valid;
        }

        // No ambiguity: classify and validate normally
        let slots: Vec<SuffixSlot> = suffixes.iter().map(|s| self.classify(s)).collect();

        // If any suffix is unknown, we can't validate → allow (permissive mode)
        if slots.iter().any(|s| matches!(s, SuffixSlot::Unknown)) {
            return true;
        }

        // Check if all slots are from the same paradigm (nominal or verbal)
        let all_nominal = slots.iter().all(|s| matches!(s, SuffixSlot::Nominal(_)));
        let all_verbal = slots.iter().all(|s| matches!(s, SuffixSlot::Verbal(_)));

        if !all_nominal && !all_verbal {
            // Mixed nominal/verbal slots → invalid
            return false;
        }

        // Validate ordering within the paradigm
        if all_nominal {
            self.validate_nominal_sequence(&slots)
        } else {
            self.validate_verbal_sequence(&slots)
        }
    }

    /// Try to validate sequence as purely nominal
    fn try_validate_as_nominal(&self, suffixes: &[&str]) -> bool {
        let mut slots = Vec::new();
        for suffix in suffixes {
            if let Some(&slot) = self.nominal_map.get(suffix) {
                slots.push(SuffixSlot::Nominal(slot));
            } else {
                // Not in nominal paradigm
                return false;
            }
        }
        self.validate_nominal_sequence(&slots)
    }

    /// Try to validate sequence as purely verbal
    fn try_validate_as_verbal(&self, suffixes: &[&str]) -> bool {
        let mut slots = Vec::new();
        for suffix in suffixes {
            if let Some(&slot) = self.verbal_map.get(suffix) {
                slots.push(SuffixSlot::Verbal(slot));
            } else {
                // Not in verbal paradigm
                return false;
            }
        }
        self.validate_verbal_sequence(&slots)
    }

    /// Validate nominal suffix ordering
    fn validate_nominal_sequence(&self, slots: &[SuffixSlot]) -> bool {
        let mut last_slot_rank = 0;

        for slot in slots {
            if let SuffixSlot::Nominal(nominal_slot) = slot {
                let current_rank = *nominal_slot as usize;

                // Each slot must come after or equal to the previous one
                // (Equal allows multiple suffixes in the same slot, e.g., -lar-lar)
                if current_rank < last_slot_rank {
                    return false; // Out of order
                }

                last_slot_rank = current_rank;
            }
        }

        true
    }

    /// Validate verbal suffix ordering
    fn validate_verbal_sequence(&self, slots: &[SuffixSlot]) -> bool {
        let mut last_slot_rank = 0;

        for slot in slots {
            if let SuffixSlot::Verbal(verbal_slot) = slot {
                let current_rank = *verbal_slot as usize;

                if current_rank < last_slot_rank {
                    return false; // Out of order
                }

                last_slot_rank = current_rank;
            }
        }

        true
    }
}

impl Default for MorphotacticClassifier {
    fn default() -> Self {
        Self::new()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_suffix_classification() {
        let classifier = MorphotacticClassifier::new();

        // Nominal (unambiguous)
        assert!(matches!(
            classifier.classify("lar"),
            SuffixSlot::Nominal(NominalSlot::Plural)
        ));
        assert!(matches!(
            classifier.classify("da"),
            SuffixSlot::Nominal(NominalSlot::Case)
        ));

        // Verbal (unambiguous)
        assert!(matches!(
            classifier.classify("di"),
            SuffixSlot::Verbal(VerbalSlot::TenseAspect)
        ));
        assert!(matches!(
            classifier.classify("yor"),
            SuffixSlot::Verbal(VerbalSlot::TenseAspect)
        ));

        // Ambiguous suffixes (classified as verbal due to precedence)
        assert!(matches!(
            classifier.classify("ım"),
            SuffixSlot::Verbal(VerbalSlot::Person)
        ));
        assert!(matches!(
            classifier.classify("m"),
            SuffixSlot::Verbal(VerbalSlot::Person)
        ));

        // Unknown
        assert!(matches!(classifier.classify("xyz"), SuffixSlot::Unknown));
    }

    #[test]
    fn test_valid_nominal_sequences() {
        let classifier = MorphotacticClassifier::new();

        // kitap+lar+ım+da (Plural → Possessive → Case)
        assert!(classifier.validate_sequence(&["lar", "ım", "da"]));

        // ev+im+de (Possessive → Case)
        assert!(classifier.validate_sequence(&["im", "de"]));

        // masa+lar (Plural only)
        assert!(classifier.validate_sequence(&["lar"]));

        // Empty sequence
        assert!(classifier.validate_sequence(&[]));
    }

    #[test]
    fn test_invalid_nominal_sequences() {
        let classifier = MorphotacticClassifier::new();

        // *kitap+da+lar (Case before Plural - INVALID)
        assert!(!classifier.validate_sequence(&["da", "lar"]));

        // *ev+lar+im+da+ım (Case before Possessive - INVALID)
        assert!(!classifier.validate_sequence(&["lar", "da", "ım"]));

        // *masa+ım+lar (Possessive before Plural - INVALID)
        assert!(!classifier.validate_sequence(&["ım", "lar"]));
    }

    #[test]
    fn test_valid_verbal_sequences() {
        let classifier = MorphotacticClassifier::new();

        // gel+di+m (Tense → Person)
        assert!(classifier.validate_sequence(&["di", "m"]));

        // yap+ıl+dı (Voice → Tense)
        assert!(classifier.validate_sequence(&["ıl", "dı"]));

        // bak+ma+dı+m (Negation → Tense → Person)
        assert!(classifier.validate_sequence(&["ma", "dı", "m"]));
    }

    #[test]
    fn test_invalid_verbal_sequences() {
        let classifier = MorphotacticClassifier::new();

        // *gel+m+di (Person before Tense - INVALID)
        assert!(!classifier.validate_sequence(&["m", "di"]));

        // *yap+dı+ma (Tense before Negation - INVALID)
        assert!(!classifier.validate_sequence(&["dı", "ma"]));
    }

    #[test]
    fn test_mixed_paradigm_rejection() {
        let classifier = MorphotacticClassifier::new();

        // *kitap+lar+di (Nominal Plural + Verbal Tense - INVALID)
        assert!(!classifier.validate_sequence(&["lar", "di"]));

        // *gel+di+da (Verbal Tense + Nominal Case - INVALID)
        assert!(!classifier.validate_sequence(&["di", "da"]));
    }

    #[test]
    fn test_unknown_suffix_permissive() {
        let classifier = MorphotacticClassifier::new();

        // Unknown suffixes are allowed (permissive mode)
        assert!(classifier.validate_sequence(&["xyz"]));
        assert!(classifier.validate_sequence(&["lar", "xyz"]));
        assert!(classifier.validate_sequence(&["xyz", "lar"]));
    }

    #[test]
    fn test_real_world_examples() {
        let classifier = MorphotacticClassifier::new();

        // Valid Turkish morphology
        assert!(classifier.validate_sequence(&["lar", "ım", "da"])); // kitaplarımda
        assert!(classifier.validate_sequence(&["ler", "imiz", "den"])); // evlerimizden
        assert!(classifier.validate_sequence(&["di", "m"])); // geldim
        assert!(classifier.validate_sequence(&["yor", "um"])); // geliyorum

        // Invalid Turkish morphology
        assert!(!classifier.validate_sequence(&["da", "lar"])); // *kitapdalar
        assert!(!classifier.validate_sequence(&["m", "di"])); // *gelimdi (nonsense)
    }
}
