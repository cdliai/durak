"""Frequency analysis and n-gram computation for Turkish texts.

This module provides:
- FrequencyCounter: Count token frequencies across documents
- ngrams: Generate n-grams from token sequences
- Support for filtering stopwords and lemmas
- Bigram/trigram collocations

Example:
    >>> from durak.stats import FrequencyCounter, ngrams
    >>> from durak import TextProcessor
    >>> 
    >>> processor = TextProcessor(ProcessorConfig(lemmatize=True))
    >>> texts = ["Kitap okuyorum.", "Kitap yazıyorum."]
    >>> 
    >>> counter = FrequencyCounter()
    >>> for text in texts:
    ...     result = processor.process(text)
    ...     counter.add(result.tokens)
    >>> 
    >>> print(counter.most_common())
    [('kitap', 2), ('okuyorum', 1), ('yazıyorum', 1)]
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Literal

from durak.stopwords import BASE_STOPWORDS


def ngrams(
    tokens: list[str],
    n: int = 2,
    pad_left: bool = False,
    pad_right: bool = False,
    pad_symbol: str = "</s>",
) -> list[tuple[str, ...]]:
    """Generate n-grams from a token sequence.
    
    Args:
        tokens: List of tokens
        n: Size of n-grams (default: 2 for bigrams)
        pad_left: Whether to pad at the beginning (default: False)
        pad_right: Whether to pad at the end (default: False)
        pad_symbol: Symbol to use for padding (default: "</s>")
        
    Returns:
        List of n-gram tuples
        
    Example:
        >>> tokens = ["bir", "iki", "üç", "dört"]
        >>> ngrams(tokens, n=2)
        [('bir', 'iki'), ('iki', 'üç'), ('üç', 'dört')]
        >>> ngrams(tokens, n=3)
        [('bir', 'iki', 'üç'), ('iki', 'üç', 'dört')]
        >>> ngrams(tokens, n=2, pad_left=True, pad_right=True)
        [('</s>', 'bir'), ('bir', 'iki'), ('iki', 'üç'), ('üç', 'dört'), ('dört', '</s>')]
    """
    if n < 1:
        raise ValueError("n must be at least 1")
    
    if not tokens:
        return []
    
    # Create padding
    pads = []
    if pad_left:
        pads = [pad_symbol] * (n - 1)
    
    padded_tokens = pads + list(tokens)
    
    if pad_right:
        padded_tokens = padded_tokens + [pad_symbol] * (n - 1)
    
    # Generate n-grams
    result = []
    for i in range(len(padded_tokens) - n + 1):
        result.append(tuple(padded_tokens[i:i + n]))
    
    return result


class FrequencyCounter:
    """Counter for token frequencies across documents.
    
    Supports unigram, bigram, and trigram analysis with optional
    stopword filtering. Can work with raw tokens or lemmas.
    
    Args:
        filter_stopwords: Whether to filter out stopwords (default: False)
        min_length: Minimum token length to count (default: 1)
        ngram_size: Size of n-grams: 1 (unigram), 2 (bigram), or 3 (trigram)
        
    Example:
        >>> counter = FrequencyCounter(ngram_size=1)
        >>> counter.add(["kitap", "okumak", "güzel"])
        >>> counter.add(["kitap", "yazmak", "zor"])
        >>> print(counter.most_common(2))
        [('kitap', 2), ('okumak', 1)]
        
        >>> # Bigrams
        >>> counter = FrequencyCounter(ngram_size=2)
        >>> counter.add(["kitap", "okumak", "güzel"])
        >>> print(counter.most_common())
        [(('kitap', 'okumak'), 1), (('okumak', 'güzel'), 1)]
    """
    
    def __init__(
        self,
        filter_stopwords: bool = False,
        min_length: int = 1,
        ngram_size: Literal[1, 2, 3] = 1,
    ):
        """Initialize the frequency counter.
        
        Args:
            filter_stopwords: Whether to filter out stopwords
            min_length: Minimum token length to count
            ngram_size: Size of n-grams (1, 2, or 3)
        """
        if ngram_size not in (1, 2, 3):
            raise ValueError("ngram_size must be 1, 2, or 3")
        
        self.filter_stopwords = filter_stopwords
        self.min_length = min_length
        self.ngram_size = ngram_size
        self._counter: Counter = Counter()
        self._document_count = 0
        self._token_count = 0
        
        if filter_stopwords:
            self._stopwords = set(BASE_STOPWORDS)
        else:
            self._stopwords = set()
    
    def _should_include(self, item: str | tuple[str, ...]) -> bool:
        """Check if an item should be included in counting.
        
        Args:
            item: Token or n-gram tuple
            
        Returns:
            True if item should be counted
        """
        if isinstance(item, tuple):
            # For n-grams, check each component
            if self.filter_stopwords:
                # Exclude n-grams containing stopwords
                for token in item:
                    if token.lower() in self._stopwords:
                        return False
            # Check minimum length for all components
            for token in item:
                if len(token) < self.min_length:
                    return False
        else:
            # For single tokens
            if self.filter_stopwords and item.lower() in self._stopwords:
                return False
            if len(item) < self.min_length:
                return False
        
        return True
    
    def add(self, tokens: list[str]) -> None:
        """Add a single document's tokens to the counter.
        
        Args:
            tokens: List of tokens from a document
            
        Example:
            >>> counter = FrequencyCounter()
            >>> counter.add(["bir", "iki", "üç"])
        """
        self._document_count += 1
        
        if self.ngram_size == 1:
            # Unigrams
            for token in tokens:
                self._token_count += 1
                if self._should_include(token):
                    self._counter[token] += 1
        else:
            # N-grams
            grams = ngrams(tokens, n=self.ngram_size)
            for gram in grams:
                self._token_count += 1
                if self._should_include(gram):
                    self._counter[gram] += 1
    
    def add_documents(self, documents: Iterable[list[str]]) -> None:
        """Add multiple documents at once.
        
        Args:
            documents: Iterable of token lists
            
        Example:
            >>> counter = FrequencyCounter()
            >>> docs = [["bir", "iki"], ["üç", "dört"]]
            >>> counter.add_documents(docs)
        """
        for tokens in documents:
            self.add(tokens)
    
    def most_common(self, n: int | None = None) -> list[tuple[str | tuple[str, ...], int]]:
        """Get the most common items.
        
        Args:
            n: Number of top items to return (default: all)
            
        Returns:
            List of (item, count) tuples, sorted by count descending
            
        Example:
            >>> counter = FrequencyCounter()
            >>> counter.add(["a", "b", "a", "c", "a", "b"])
            >>> counter.most_common(2)
            [('a', 3), ('b', 2)]
        """
        return self._counter.most_common(n)
    
    def get_count(self, item: str | tuple[str, ...]) -> int:
        """Get the count of a specific item.
        
        Args:
            item: Token or n-gram to look up
            
        Returns:
            Count of the item (0 if not found)
            
        Example:
            >>> counter = FrequencyCounter()
            >>> counter.add(["bir", "iki", "bir"])
            >>> counter.get_count("bir")
            2
        """
        return self._counter[item]
    
    def __contains__(self, item: str | tuple[str, ...]) -> bool:
        """Check if an item has been counted.
        
        Example:
            >>> counter = FrequencyCounter()
            >>> counter.add(["bir", "iki"])
            >>> "bir" in counter
            True
            >>> "üç" in counter
            False
        """
        return item in self._counter
    
    def __len__(self) -> int:
        """Return the number of unique items."""
        return len(self._counter)
    
    @property
    def total_tokens(self) -> int:
        """Total number of tokens processed (including filtered)."""
        return self._token_count
    
    @property
    def unique_count(self) -> int:
        """Number of unique items after filtering."""
        return len(self._counter)
    
    @property
    def document_count(self) -> int:
        """Number of documents processed."""
        return self._document_count
    
    def get_frequency_table(self, min_count: int = 1) -> dict[str | tuple[str, ...], int]:
        """Get a dictionary of all frequencies.
        
        Args:
            min_count: Minimum count threshold (default: 1)
            
        Returns:
            Dictionary mapping items to counts
            
        Example:
            >>> counter = FrequencyCounter()
            >>> counter.add(["a", "b", "a"])
            >>> counter.get_frequency_table()
            {'a': 2, 'b': 1}
        """
        return {
            item: count
            for item, count in self._counter.items()
            if count >= min_count
        }
    
    def to_tsv(self, path: str, min_count: int = 1) -> None:
        """Export frequencies to a TSV file.
        
        Args:
            path: Output file path
            min_count: Minimum count threshold (default: 1)
            
        Example:
            >>> counter = FrequencyCounter()
            >>> counter.add(["bir", "iki", "bir"])
            >>> counter.to_tsv("frequencies.tsv")
        """
        with open(path, "w", encoding="utf-8") as f:
            f.write("item\tcount\n")
            for item, count in self.most_common():
                if count >= min_count:
                    # Handle n-grams by joining with space
                    if isinstance(item, tuple):
                        item_str = " ".join(item)
                    else:
                        item_str = str(item)
                    f.write(f"{item_str}\t{count}\n")
    
    def __repr__(self) -> str:
        parts = [f"ngram_size={self.ngram_size}"]
        if self.filter_stopwords:
            parts.append("filter_stopwords=True")
        if self.min_length > 1:
            parts.append(f"min_length={self.min_length}")
        return f"FrequencyCounter({', '.join(parts)})"


# Convenience functions

def count_unigrams(
    texts: list[list[str]],
    filter_stopwords: bool = False,
    min_length: int = 1,
) -> Counter:
    """Count unigrams across multiple texts.
    
    Args:
        texts: List of tokenized texts
        filter_stopwords: Whether to filter stopwords
        min_length: Minimum token length
        
    Returns:
        Counter with frequency counts
        
    Example:
        >>> texts = [["bir", "iki"], ["bir", "üç"]]
        >>> count_unigrams(texts)
        Counter({'bir': 2, 'iki': 1, 'üç': 1})
    """
    counter = FrequencyCounter(
        filter_stopwords=filter_stopwords,
        min_length=min_length,
        ngram_size=1,
    )
    counter.add_documents(texts)
    return counter._counter


def count_bigrams(
    texts: list[list[str]],
    filter_stopwords: bool = False,
    min_length: int = 1,
) -> Counter:
    """Count bigrams across multiple texts.
    
    Args:
        texts: List of tokenized texts
        filter_stopwords: Whether to filter stopwords
        min_length: Minimum token length
        
    Returns:
        Counter with bigram frequency counts
        
    Example:
        >>> texts = [["bir", "iki", "üç"], ["bir", "iki", "dört"]]
        >>> count_bigrams(texts)
        Counter({('bir', 'iki'): 2, ('iki', 'üç'): 1, ('iki', 'dört'): 1})
    """
    counter = FrequencyCounter(
        filter_stopwords=filter_stopwords,
        min_length=min_length,
        ngram_size=2,
    )
    counter.add_documents(texts)
    return counter._counter


__all__ = [
    "FrequencyCounter",
    "ngrams",
    "count_unigrams",
    "count_bigrams",
]