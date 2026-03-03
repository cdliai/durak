//! Shared Turkish suffix inventory used by lemmatization stages.

/// Nominal plural suffixes.
pub const NOMINAL_PLURAL_SUFFIXES: &[&str] = &["lar", "ler"];

/// Nominal possessive suffixes.
pub const NOMINAL_POSSESSIVE_SUFFIXES: &[&str] = &[
    "ım", "im", "um", "üm", "ımız", "imiz", "umuz", "ümüz",
];

/// Nominal case suffixes.
pub const NOMINAL_CASE_SUFFIXES: &[&str] = &[
    "da", "de", "ta", "te", "dan", "den", "tan", "ten", "ın", "in", "un", "ün", "nın", "nin",
    "nun", "nün", "a", "e", "ya", "ye", "ı", "i", "u", "ü",
];

/// Verbal voice suffixes.
pub const VERBAL_VOICE_SUFFIXES: &[&str] = &["ıl", "il", "ul", "ül", "ın", "in", "un", "ün"];

/// Verbal negation suffixes.
pub const VERBAL_NEGATION_SUFFIXES: &[&str] = &["ma", "me"];

/// Verbal tense/aspect suffixes.
pub const VERBAL_TENSE_ASPECT_SUFFIXES: &[&str] = &[
    "di", "dı", "du", "dü", "ti", "tı", "tu", "tü", "yor", "acak", "ecek", "mış", "miş", "muş",
    "müş",
];

/// Verbal person suffixes.
pub const VERBAL_PERSON_SUFFIXES: &[&str] = &[
    "m", "n", "k", "z", "ım", "im", "um", "üm", "nız", "niz", "nuz", "nüz",
];

/// Compound suffixes that should be stripped as a unit before individual suffixes.
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

/// Nominal suffixes (attached to nouns, adjectives).
/// Order: Plural -> Possessive -> Case.
pub const NOMINAL_SUFFIXES: &[&str] = &[
    // Plural (Slot 1)
    "lar", "ler",
    // Possessive (Slot 2) - 1st person
    "ım", "im", "um", "üm", "ımız", "imiz", "umuz", "ümüz",
    // Possessive (Slot 2) - 2nd person
    "ın", "in", "un", "ün", "ınız", "iniz", "unuz", "ünüz",
    // Possessive (Slot 2) - 3rd person
    "ı", "i", "u", "ü", "sı", "si", "su", "sü",
    // Case (Slot 3) - Accusative
    "ı", "i", "u", "ü",
    // Case (Slot 3) - Dative
    "a", "e", "ya", "ye",
    // Case (Slot 3) - Locative
    "da", "de", "ta", "te",
    // Case (Slot 3) - Ablative
    "dan", "den", "tan", "ten",
    // Case (Slot 3) - Genitive
    "ın", "in", "un", "ün", "nın", "nin", "nun", "nün",
];

/// Verbal suffixes (attached to verbs).
/// Order: Voice -> Negation -> Tense/Aspect -> Person.
pub const VERBAL_SUFFIXES: &[&str] = &[
    // Voice (Slot 1) - Passive, Causative, Reflexive, Reciprocal
    "ıl", "il", "ul", "ül", "n", "ın", "in", "un", "ün", "dir", "dır", "dur", "dür", "tir", "tır",
    "tur", "tür", "ş", "ış", "iş", "uş", "üş",
    // Negation (Slot 2)
    "me", "ma",
    // Tense/Aspect (Slot 3)
    "di", "dı", "du", "dü", "ti", "tı", "tu", "tü",
    "miş", "mış", "muş", "müş",
    "ecek", "acak",
    "iyor",
    "er", "ar",
    "mekte", "makta",
    // Person (Slot 4)
    "m", "n", "k", "z", "ım", "im", "um", "üm", "ın", "in", "un", "ün", "ız", "iz", "uz", "üz",
    "sın", "sin", "sun", "sün", "sınız", "siniz", "sunuz", "sünüz", "lar", "ler",
    // Infinitive
    "mek", "mak",
];

/// Fixed morphemes that do not follow standard vowel harmony.
pub const FIXED_MORPHEMES: &[&str] = &[
    "iyor",  // Present continuous
    "ken",   // While
    "ki",    // Relative
    "leyin", // Time
];
