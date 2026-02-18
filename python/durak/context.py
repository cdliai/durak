from dataclasses import dataclass, field


@dataclass
class ProcessingContext:
    """
    Central context object for managing state that flows through the pipeline.
    Contains text, tokens, and metadata about transformation steps.
    """

    text: str
    metadata: list[str] = field(default_factory=list)
    tokens: list[str] = field(default_factory=list)
    normalized_tokens: list[str] = field(default_factory=list)

    def add_metadata(self, info: str) -> None:
        self.metadata.append(info)

    def clone(self) -> "ProcessingContext":
        """Create a deep copy of the context for branching pipelines."""
        return ProcessingContext(
            text=self.text,
            metadata=self.metadata.copy(),
            tokens=self.tokens.copy(),
            normalized_tokens=self.normalized_tokens.copy(),
        )
