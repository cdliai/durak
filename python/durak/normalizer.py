"""Text normalization utilities."""

from __future__ import annotations

from durak.exceptions import NormalizerError, RustExtensionError

try:
    from durak._durak_core import fast_normalize
except ImportError:
    # Fallback or initialization error handling
    def fast_normalize(text: str) -> str:
        raise RustExtensionError(
            "Rust extension not installed. Run: maturin develop"
        )

class Normalizer:
    """
    A configurable Normalizer module backed by Rust.
    
    Args:
        lowercase (bool): If True, lowercases the text (handling Turkish I/ı).
        handle_turkish_i (bool): If True, handles specific Turkish I/İ rules.
    """
    def __init__(self, lowercase: bool = True, handle_turkish_i: bool = True):
        self.lowercase = lowercase
        self.handle_turkish_i = handle_turkish_i

    def __call__(self, text: str) -> str:
        """
        Normalize the input text.
        
        Args:
            text (str): Input string.
            
        Returns:
            str: Normalized string.
            
        Raises:
            NormalizerError: If input is not a string
            RustExtensionError: If Rust extension is not available
        """
        if not isinstance(text, str):
            raise NormalizerError(
                f"Input must be a string, got {type(text).__name__}"
            )
        
        if not text:
            return ""
        
        # Pass configuration parameters to Rust core
        return fast_normalize(text, self.lowercase, self.handle_turkish_i)
        try:
            if self.lowercase and self.handle_turkish_i:
                return fast_normalize(text)
            
            # In the future, we can add more configuration options to the Rust core
            # and pass flags, but for now fast_normalize does both default behaviors.
            return fast_normalize(text)
        except RustExtensionError:
            raise  # Re-raise as-is
        except Exception as e:
            raise NormalizerError(f"Normalization failed: {e}") from e

    def __repr__(self) -> str:
        return (
            f"Normalizer(lowercase={self.lowercase}, "
            f"handle_turkish_i={self.handle_turkish_i})"
        )
