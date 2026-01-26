/// PyO3 bindings for Durak's Rust core
/// This module wraps the core functionality for Python interoperability

// Core module is always available (for both Python bindings and CLI)
pub mod core;

// Python bindings only when pyo3 feature is enabled
#[cfg(feature = "pyo3")]
mod python_bindings {
    use pyo3::prelude::*;
    use std::collections::HashMap;
    use crate::core;

    /// Fast normalization for Turkish text.
    #[pyfunction]
    fn fast_normalize(text: &str) -> String {
        core::fast_normalize(text)
    }

    /// Tokenize text and return tokens with offsets.
    #[pyfunction]
    fn tokenize_with_offsets(text: &str) -> Vec<(String, usize, usize)> {
        core::tokenize_with_offsets(text)
    }

    /// Tokenize text and return normalized tokens with offsets.
    #[pyfunction]
    fn tokenize_with_normalized_offsets(text: &str) -> Vec<(String, usize, usize)> {
        core::tokenize_with_normalized_offsets(text)
    }

    /// Tier 1: Exact Lookup
    #[pyfunction]
    fn lookup_lemma(word: &str) -> Option<String> {
        core::lookup_lemma(word)
    }

    /// Tier 2: Heuristic Suffix Stripping
    #[pyfunction]
    fn strip_suffixes(word: &str) -> String {
        core::strip_suffixes(word)
    }

    /// Get embedded detached suffixes list
    #[pyfunction]
    fn get_detached_suffixes() -> Vec<String> {
        core::get_detached_suffixes()
    }

    /// Get embedded Turkish stopwords list
    #[pyfunction]
    fn get_stopwords_base() -> Vec<String> {
        core::get_stopwords_base()
    }

    /// Get embedded stopwords metadata JSON
    #[pyfunction]
    fn get_stopwords_metadata() -> String {
        core::get_stopwords_metadata()
    }

    /// Get embedded social media stopwords
    #[pyfunction]
    fn get_stopwords_social_media() -> Vec<String> {
        core::get_stopwords_social_media()
    }

    /// Get build information for reproducibility tracking.
    #[pyfunction]
    fn get_build_info() -> HashMap<String, String> {
        core::get_build_info()
    }

    /// Get embedded resource versions and checksums for reproducibility.
    #[pyfunction]
    fn get_resource_info() -> HashMap<String, HashMap<String, String>> {
        core::get_resource_info()
    }

    /// The internal Rust part of the Durak library.
    #[pymodule]
    fn _durak_core(_py: Python, m: &Bound<'_, PyModule>) -> PyResult<()> {
        m.add_function(wrap_pyfunction!(fast_normalize, m)?)?;
        m.add_function(wrap_pyfunction!(tokenize_with_offsets, m)?)?;
        m.add_function(wrap_pyfunction!(tokenize_with_normalized_offsets, m)?)?;
        m.add_function(wrap_pyfunction!(lookup_lemma, m)?)?;
        m.add_function(wrap_pyfunction!(strip_suffixes, m)?)?;
        m.add_function(wrap_pyfunction!(get_detached_suffixes, m)?)?;
        m.add_function(wrap_pyfunction!(get_stopwords_base, m)?)?;
        m.add_function(wrap_pyfunction!(get_stopwords_metadata, m)?)?;
        m.add_function(wrap_pyfunction!(get_stopwords_social_media, m)?)?;
        m.add_function(wrap_pyfunction!(get_build_info, m)?)?;
        m.add_function(wrap_pyfunction!(get_resource_info, m)?)?;
        Ok(())
    }
}

// Re-export the pymodule when pyo3 feature is enabled
#[cfg(feature = "pyo3")]
pub use python_bindings::_durak_core;
