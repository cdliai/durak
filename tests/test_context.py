"""Tests for the context module."""

import pytest

from durak.context import ProcessingContext


class TestProcessingContext:
    """Tests for ProcessingContext dataclass."""

    def test_init_with_text(self):
        ctx = ProcessingContext(text="Hello world")
        assert ctx.text == "Hello world"
        assert ctx.metadata == []
        assert ctx.tokens == []
        assert ctx.normalized_tokens == []

    def test_init_with_all_fields(self):
        ctx = ProcessingContext(
            text="test",
            metadata=["step1"],
            tokens=["hello", "world"],
            normalized_tokens=["hello", "world"],
        )
        assert ctx.text == "test"
        assert ctx.metadata == ["step1"]
        assert ctx.tokens == ["hello", "world"]
        assert ctx.normalized_tokens == ["hello", "world"]

    def test_add_metadata(self):
        ctx = ProcessingContext(text="test")
        ctx.add_metadata("cleaned")
        assert ctx.metadata == ["cleaned"]
        ctx.add_metadata("tokenized")
        assert ctx.metadata == ["cleaned", "tokenized"]

    def test_clone(self):
        ctx = ProcessingContext(
            text="original",
            metadata=["step1"],
            tokens=["token1"],
            normalized_tokens=["norm1"],
        )
        cloned = ctx.clone()

        assert cloned.text == ctx.text
        assert cloned.metadata == ctx.metadata
        assert cloned.tokens == ctx.tokens
        assert cloned.normalized_tokens == ctx.normalized_tokens

        cloned.metadata.append("step2")
        cloned.tokens.append("token2")
        assert ctx.metadata == ["step1"]
        assert ctx.tokens == ["token1"]

    def test_clone_independence(self):
        ctx = ProcessingContext(text="test", metadata=["a"])
        cloned = ctx.clone()
        cloned.text = "modified"
        assert ctx.text == "test"
