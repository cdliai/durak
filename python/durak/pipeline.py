"""Pipeline module for composing text processing steps."""

from __future__ import annotations

from durak.cleaning import clean_text, normalize_case
from durak.exceptions import ConfigurationError, PipelineError
from durak.normalizer import Normalizer
from durak.stopwords import remove_stopwords
from durak.tokenizer import split_sentences, tokenize

STEP_REGISTRY = {
    "clean": clean_text,
    "normalize": Normalizer(),
    "normalize_case": normalize_case,
    "tokenize": tokenize,
    "split_sentences": split_sentences,
    "remove_stopwords": remove_stopwords,
}


class Pipeline:
    """
    Composable text processing pipeline.
    
    Args:
        steps: List of step names or callables
        
    Raises:
        ConfigurationError: If steps list is empty or contains unknown step names
        
    Examples:
        >>> pipeline = Pipeline(["clean", "tokenize"])
        >>> tokens = pipeline("Hello world!")
        ['Hello', 'world', '!']
    """
    
    def __init__(self, steps: list[str | callable]):
        if not steps:
            raise ConfigurationError("Pipeline must have at least one step")
        
        self.step_names = []
        self.steps = []
        
        for step in steps:
            if callable(step):
                # Use __name__ for functions, class name for instances
                step_name = getattr(step, '__name__', step.__class__.__name__)
                self.step_names.append(step_name)
                self.steps.append(step)
            elif isinstance(step, str):
                if step not in STEP_REGISTRY:
                    raise ConfigurationError(
                        f"Unknown pipeline step: '{step}'. "
                        f"Available steps: {', '.join(STEP_REGISTRY.keys())}"
                    )
                self.step_names.append(step)
                self.steps.append(STEP_REGISTRY[step])
            else:
                raise ConfigurationError(
                    f"Pipeline step must be a string or callable, got {type(step).__name__}"
                )

    def __call__(self, text: str) -> str | list[str]:
        """
        Process text through the pipeline.
        
        Args:
            text: Input text to process
            
        Returns:
            Processed result (type depends on pipeline steps)
            
        Raises:
            PipelineError: If input is not a string or step execution fails
        """
        if not isinstance(text, str):
            raise PipelineError(
                f"Pipeline input must be a string, got {type(text).__name__}"
            )
        
        doc = text
        for step_name, step in zip(self.step_names, self.steps):
            try:
                doc = step(doc)
            except Exception as e:
                raise PipelineError(
                    f"Pipeline step '{step_name}' failed: {e}"
                ) from e
        return doc

    def __repr__(self) -> str:
        return f"Pipeline([{', '.join(repr(name) for name in self.step_names)}])"


def process_text(text: str, steps: list[str | callable]) -> str | list[str]:
    """
    Convenience function for one-off pipeline processing.
    
    Args:
        text: Input text
        steps: List of step names or callables
        
    Returns:
        Processed result
        
    Examples:
        >>> result = process_text("Hello world!", ["clean", "tokenize"])
        ['Hello', 'world', '!']
    """
    pipeline = Pipeline(steps)
    return pipeline(text)
