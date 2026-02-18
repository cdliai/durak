"""Tests for the pipeline module."""

import pytest
import warnings

from durak.normalizer import Normalizer
from durak.pipeline import Pipeline, process_text, process_text_with_steps
from durak.exceptions import ConfigurationError, PipelineError


class TestNormalizer:
    """Tests for Normalizer class."""

    def test_normalizer_importable(self):
        norm = Normalizer()
        assert norm is not None

    def test_normalizer_repr(self):
        norm = Normalizer()
        assert "Normalizer" in repr(norm)


class TestPipeline:
    """Tests for Pipeline class."""

    def test_pipeline_creation_with_callables(self):
        pipe = Pipeline([Normalizer()])
        assert len(pipe.steps) == 1
        assert len(pipe.step_names) == 1

    def test_pipeline_creation_with_strings(self):
        pipe = Pipeline(["clean", "tokenize"])
        assert len(pipe.steps) == 2
        assert pipe.step_names == ["clean", "tokenize"]

    def test_pipeline_creation_mixed(self):
        pipe = Pipeline(["clean", Normalizer()])
        assert len(pipe.steps) == 2

    def test_pipeline_empty_steps_raises(self):
        with pytest.raises(ConfigurationError, match="at least one step"):
            Pipeline([])

    def test_pipeline_unknown_step_raises(self):
        with pytest.raises(ConfigurationError, match="Unknown pipeline step"):
            Pipeline(["unknown_step"])

    def test_pipeline_invalid_step_type_raises(self):
        with pytest.raises(ConfigurationError, match="string or callable"):
            Pipeline([123])  # type: ignore[list-item]

    def test_pipeline_repr(self):
        pipe = Pipeline(["clean", "tokenize"])
        assert "Pipeline" in repr(pipe)
        assert "clean" in repr(pipe)

    def test_pipeline_execution_normalizer(self):
        try:
            from durak import _durak_core
        except ImportError:
            pytest.skip("Rust extension not installed")

        pipe = Pipeline([Normalizer()])
        result = pipe("İSTANBUL ve IĞDIR")
        assert result == "istanbul ve ığdır"

    def test_pipeline_execution_clean_tokenize(self):
        try:
            from durak import _durak_core
        except ImportError:
            pytest.skip("Rust extension not installed")

        pipe = Pipeline(["clean", "tokenize"])
        result = pipe("Hello World!")
        assert isinstance(result, list)
        assert "hello" in result
        assert "world" in result

    def test_pipeline_invalid_input_type(self):
        pipe = Pipeline(["clean"])
        with pytest.raises(PipelineError, match="must be a string"):
            pipe(12345)  # type: ignore[arg-type]

    def test_pipeline_step_failure_wrapped(self):
        def bad_step(text: str):
            raise ValueError("Intentional error")

        pipe = Pipeline([bad_step])
        with pytest.raises(PipelineError, match="failed"):
            pipe("test")


class TestProcessTextWithSteps:
    """Tests for process_text_with_steps function."""

    def test_basic_usage(self):
        try:
            from durak import _durak_core
        except ImportError:
            pytest.skip("Rust extension not installed")

        result = process_text_with_steps("Hello World!", ["clean", "tokenize"])
        assert isinstance(result, list)
        assert len(result) > 0


class TestProcessTextDeprecated:
    """Tests for deprecated process_text function."""

    def test_deprecation_warning(self):
        try:
            from durak import _durak_core
        except ImportError:
            pytest.skip("Rust extension not installed")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            process_text("test text")
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "deprecated" in str(w[0].message).lower()

    def test_basic_processing(self):
        try:
            from durak import _durak_core
        except ImportError:
            pytest.skip("Rust extension not installed")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = process_text("Türkiye'de NLP zor!")
            assert isinstance(result, list)
            assert len(result) > 0

    def test_remove_stopwords(self):
        try:
            from durak import _durak_core
        except ImportError:
            pytest.skip("Rust extension not installed")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = process_text("Bu bir test", remove_stopwords=True)
            assert "bu" not in result
            assert "bir" not in result
            assert "test" in result

    def test_rejoin_suffixes(self):
        try:
            from durak import _durak_core
        except ImportError:
            pytest.skip("Rust extension not installed")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = process_text("Ankara ' da kaldım.", rejoin_suffixes=True)
            assert "ankara'da" in result

    def test_strip_punct(self):
        try:
            from durak import _durak_core
        except ImportError:
            pytest.skip("Rust extension not installed")

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = process_text("Hello!", strip_punct=True)
            assert "!" not in result
            assert "hello" in result

    def test_empty_string(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = process_text("")
            assert result == []

    def test_invalid_input_type(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            with pytest.raises(PipelineError, match="must be a string"):
                process_text(12345)  # type: ignore[arg-type]
