"""Advanced pipeline example with custom configuration.

Demonstrates creating custom text processing pipelines with
domain-specific stopwords, suffix attachment, and lemmatization.
"""

import durak


def main():
    print("=" * 60)
    print("Advanced Pipeline Example")
    print("=" * 60)

    # Sample text
    text = """
    Ankara'da bugün hava çok güzel. Ankara'nın tarihi yerlerini
    gezmeye gittik. İstanbul'dan gelen arkadaşlarımız da vardı.
    """

    print(f"\nOriginal text:\n{text}")

    # 1. Custom Stopword Management
    print("\n1. Custom Stopword Management")
    print("-" * 60)

    # Create a stopword manager with custom additions
    stopword_mgr = durak.StopwordManager(
        additions=["bugün", "çok"],  # Add custom stopwords
        keep=["var", "git"],  # Keep these even if they're stopwords
    )

    tokens = durak.tokenize(durak.clean_text(text))
    print(f"Tokens: {tokens}")

    filtered = [t for t in tokens if not stopword_mgr.is_stopword(t)]
    print(f"Filtered: {filtered}")

    # 2. Suffix Attachment
    print("\n2. Detached Suffix Attachment")
    print("-" * 60)

    # Tokenize preserving apostrophes
    text_with_suffixes = "Ankara'da İstanbul'dan geldi"
    tokens_raw = durak.tokenize(text_with_suffixes)
    print(f"Raw tokens: {tokens_raw}")

    # Attach detached suffixes
    attached = durak.attach_detached_suffixes(tokens_raw)
    print(f"With attached suffixes: {attached}")

    # 3. Custom Pipeline
    print("\n3. Building a Custom Pipeline")
    print("-" * 60)

    class CustomTurkishPipeline:
        """Custom pipeline for Turkish text processing."""

        def __init__(
            self,
            attach_suffixes=True,
            remove_stopwords=True,
            normalize=True,
            custom_stopwords=None,
        ):
            self.attach_suffixes = attach_suffixes
            self.remove_stopwords = remove_stopwords
            self.normalize = normalize

            if custom_stopwords:
                self.stopword_mgr = durak.StopwordManager(additions=custom_stopwords)
            else:
                self.stopword_mgr = durak.StopwordManager()

        def __call__(self, text):
            """Process text through the pipeline."""
            # Clean and normalize
            processed = durak.clean_text(text)

            if self.normalize:
                processed = durak.normalize_case(processed)

            # Tokenize
            tokens = durak.tokenize(processed)

            # Attach suffixes
            if self.attach_suffixes:
                tokens = durak.attach_detached_suffixes(tokens)

            # Remove stopwords
            if self.remove_stopwords:
                tokens = [t for t in tokens if not self.stopword_mgr.is_stopword(t)]

            return tokens

    # Use the custom pipeline
    custom_pipeline = CustomTurkishPipeline(
        attach_suffixes=True,
        remove_stopwords=True,
        normalize=True,
        custom_stopwords=["bugün"],
    )

    result = custom_pipeline(text)
    print(f"Custom pipeline result: {result}")

    # 4. Resource Loading Strategies
    print("\n4. Resource Loading Strategies")
    print("-" * 60)

    # Load from embedded Rust resources (zero file I/O)
    try:
        from durak import _durak_core

        rust_stopwords = set(_durak_core.get_stopwords_base())
        print(f"Loaded {len(rust_stopwords)} stopwords from Rust (embedded)")
    except ImportError:
        print("Rust extension not available")

    # Load from file resources (traditional)
    file_stopwords = durak.load_stopword_resource("base/turkish")
    print(f"Loaded {len(file_stopwords)} stopwords from file")

    # Load multiple resources
    combined = durak.load_stopword_resources(["base/turkish", "domains/social_media"])
    print(f"Combined {len(combined)} stopwords from multiple sources")

    print("\n" + "=" * 60)
    print("Advanced example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
