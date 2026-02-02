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

        try:
            # Fast path: lowercase + Turkish I handling (default)
            if self.lowercase and self.handle_turkish_i:
                return fast_normalize(text)

            # Slow path: custom configurations
            if not self.lowercase:
                # Preserve case, but optionally handle Turkish I/İ conversion
                if self.handle_turkish_i:
                    # Handle Turkish I/İ only, preserve other characters
                    result = []
                    for c in text:
                        if c == 'İ':
                            result.append('i')
                        elif c == 'I':
                            result.append('ı')
                        else:
                            result.append(c)
                    return ''.join(result)
                else:
                    # No transformation at all
                    return text

            # lowercase=True, handle_turkish_i=False
            # Standard lowercase without Turkish I handling
            # Need to handle İ manually to avoid combining characters
            result = []
            for c in text:
                if c == 'İ':
                    result.append('i')
                else:
                    result.append(c.lower())
            return ''.join(result)

        except RustExtensionError:
            raise  # Re-raise as-is
        except Exception as e:
            raise NormalizerError(f"Normalization failed: {e}") from e

    def __repr__(self) -> str:
        return (
            f"Normalizer(lowercase={self.lowercase}, "
            f"handle_turkish_i={self.handle_turkish_i})"
        )
