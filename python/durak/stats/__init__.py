"""Statistics module for Turkish NLP analysis.

Provides frequency counters and n-gram analysis for processed texts.

Example:
    >>> from durak.stats import FrequencyCounter
    >>> from durak import TextProcessor
    >>> 
    >>> processor = TextProcessor()
    >>> texts = ["Birinci text.", "İkinci text.", "Üçüncü text."]
    >>> tokens = [processor.process(t).tokens for t in texts]
    >>> 
    >>> counter = FrequencyCounter()
    >>> counter.add_documents(tokens)
    >>> print(counter.most_common(5))
"""

from .frequencies import FrequencyCounter, ngrams

__all__ = [
    "FrequencyCounter",
    "ngrams",
]