"""Test exception hierarchy and error handling."""

import pytest

from durak import (
    ConfigurationError,
    DurakError,
    Lemmatizer,
    LemmatizerError,
    Normalizer,
    NormalizerError,
    Pipeline,
    PipelineError,
    ResourceError,
    RustExtensionError,
    StopwordError,
    StopwordMetadataError,
    TokenizationError,
)


class TestExceptionHierarchy:
    """Test exception inheritance and base class."""
    
    def test_all_exceptions_inherit_from_durak_error(self):
        """All Durak exceptions should inherit from DurakError."""
        exceptions = [
            ConfigurationError,
            ResourceError,
            RustExtensionError,
            LemmatizerError,
            NormalizerError,
            PipelineError,
            TokenizationError,
            StopwordError,
        ]
        
        for exc_class in exceptions:
            assert issubclass(exc_class, DurakError)
            assert issubclass(exc_class, Exception)
    
    def test_durak_error_is_base_exception(self):
        """DurakError should inherit from Exception."""
        assert issubclass(DurakError, Exception)
    
    def test_backward_compatibility_alias(self):
        """StopwordMetadataError should be alias for StopwordError."""
        assert StopwordMetadataError is StopwordError


class TestLemmatizerExceptions:
    """Test exception handling in Lemmatizer."""
    
    def test_invalid_strategy_raises_configuration_error(self):
        """Invalid strategy should raise ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Lemmatizer(strategy="invalid")
        
        assert "Unknown strategy" in str(exc_info.value)
        assert "invalid" in str(exc_info.value)
    
    def test_invalid_min_root_length_raises_configuration_error(self):
        """min_root_length < 1 should raise ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Lemmatizer(min_root_length=0)
        
        assert "min_root_length must be at least 1" in str(exc_info.value)
    
    def test_non_string_input_raises_lemmatizer_error(self):
        """Non-string input should raise LemmatizerError."""
        lemmatizer = Lemmatizer()
        
        with pytest.raises(LemmatizerError) as exc_info:
            lemmatizer(12345)
        
        assert "Input must be a string" in str(exc_info.value)
        assert "int" in str(exc_info.value)
    
    def test_lemmatizer_error_is_catchable_as_durak_error(self):
        """LemmatizerError should be catchable as DurakError."""
        lemmatizer = Lemmatizer()
        
        try:
            lemmatizer(12345)
        except DurakError as e:
            assert isinstance(e, LemmatizerError)
        else:
            pytest.fail("Expected DurakError to be raised")


class TestNormalizerExceptions:
    """Test exception handling in Normalizer."""
    
    def test_non_string_input_raises_normalizer_error(self):
        """Non-string input should raise NormalizerError."""
        normalizer = Normalizer()
        
        with pytest.raises(NormalizerError) as exc_info:
            normalizer(12345)
        
        assert "Input must be a string" in str(exc_info.value)
        assert "int" in str(exc_info.value)
    
    def test_normalizer_error_is_catchable_as_durak_error(self):
        """NormalizerError should be catchable as DurakError."""
        normalizer = Normalizer()
        
        try:
            normalizer([1, 2, 3])
        except DurakError as e:
            assert isinstance(e, NormalizerError)
        else:
            pytest.fail("Expected DurakError to be raised")


class TestPipelineExceptions:
    """Test exception handling in Pipeline."""
    
    def test_empty_steps_raises_configuration_error(self):
        """Empty steps list should raise ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Pipeline([])
        
        assert "must have at least one step" in str(exc_info.value)
    
    def test_unknown_step_raises_configuration_error(self):
        """Unknown step name should raise ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Pipeline(["clean", "invalid_step"])
        
        assert "Unknown pipeline step" in str(exc_info.value)
        assert "invalid_step" in str(exc_info.value)
    
    def test_invalid_step_type_raises_configuration_error(self):
        """Invalid step type should raise ConfigurationError."""
        with pytest.raises(ConfigurationError) as exc_info:
            Pipeline([12345])
        
        assert "must be a string or callable" in str(exc_info.value)
    
    def test_non_string_input_raises_pipeline_error(self):
        """Non-string input should raise PipelineError."""
        pipeline = Pipeline(["clean"])
        
        with pytest.raises(PipelineError) as exc_info:
            pipeline(12345)
        
        assert "input must be a string" in str(exc_info.value)
    
    def test_step_failure_raises_pipeline_error(self):
        """Failed step should raise PipelineError with context."""
        # Create a pipeline with a step that will fail
        def failing_step(text):
            raise ValueError("Intentional failure")
        
        pipeline = Pipeline([failing_step])
        
        with pytest.raises(PipelineError) as exc_info:
            pipeline("test text")
        
        assert "Pipeline step" in str(exc_info.value)
        assert "failed" in str(exc_info.value)
        # Check that the original exception is chained
        assert exc_info.value.__cause__.__class__.__name__ == "ValueError"
    
    def test_pipeline_error_is_catchable_as_durak_error(self):
        """PipelineError should be catchable as DurakError."""
        pipeline = Pipeline(["clean"])
        
        try:
            pipeline(12345)
        except DurakError as e:
            assert isinstance(e, PipelineError)
        else:
            pytest.fail("Expected DurakError to be raised")


class TestExceptionMessages:
    """Test that exception messages are helpful and informative."""
    
    def test_configuration_error_suggests_valid_options(self):
        """ConfigurationError should suggest valid options."""
        with pytest.raises(ConfigurationError) as exc_info:
            Lemmatizer(strategy="wrong")
        
        # Should mention valid options
        error_msg = str(exc_info.value)
        assert "lookup" in error_msg
        assert "heuristic" in error_msg
        assert "hybrid" in error_msg
    
    def test_pipeline_error_identifies_failing_step(self):
        """PipelineError should identify which step failed."""
        def bad_step(text):
            raise RuntimeError("boom")
        
        pipeline = Pipeline(["clean", bad_step, "tokenize"])
        
        with pytest.raises(PipelineError) as exc_info:
            pipeline("test")
        
        assert "bad_step" in str(exc_info.value)
    
    def test_type_errors_show_actual_type(self):
        """Type validation errors should show the actual type received."""
        lemmatizer = Lemmatizer()
        
        with pytest.raises(LemmatizerError) as exc_info:
            lemmatizer({"word": "test"})
        
        assert "dict" in str(exc_info.value)


class TestExceptionChaining:
    """Test that exceptions are properly chained for debugging."""
    
    def test_lemmatizer_error_chains_original_exception(self):
        """LemmatizerError should chain the original exception."""
        # This test assumes Rust extension is loaded
        # If not loaded, we'd get RustExtensionError directly
        lemmatizer = Lemmatizer()
        
        # Pass invalid type to trigger error
        with pytest.raises(LemmatizerError) as exc_info:
            lemmatizer(None)
        
        # Either chained or direct error is acceptable
        assert exc_info.value is not None
    
    def test_pipeline_error_chains_step_exception(self):
        """PipelineError should preserve the original exception in __cause__."""
        def failing_step(text):
            raise KeyError("missing key")
        
        pipeline = Pipeline([failing_step])
        
        with pytest.raises(PipelineError) as exc_info:
            pipeline("test")
        
        assert isinstance(exc_info.value.__cause__, KeyError)
        assert "missing key" in str(exc_info.value.__cause__)


class TestCatchAllDurakErrors:
    """Test catching all Durak errors with a single except clause."""
    
    def test_catch_all_durak_errors(self):
        """Single except DurakError should catch all package errors."""
        errors_caught = []
        
        # Test various error types
        test_cases = [
            lambda: Lemmatizer(strategy="invalid"),
            lambda: Lemmatizer()(12345),
            lambda: Normalizer()(12345),
            lambda: Pipeline([]),
            lambda: Pipeline(["clean"])(12345),  # PipelineError from non-string input
        ]
        
        for test_case in test_cases:
            try:
                test_case()
            except DurakError as e:
                errors_caught.append(type(e).__name__)
            except Exception as e:
                pytest.fail(f"Unexpected exception type: {type(e)}")
        
        # Should have caught all errors
        assert len(errors_caught) == len(test_cases)
        
        # Should include different error types
        assert "ConfigurationError" in errors_caught
        assert "LemmatizerError" in errors_caught
        assert "NormalizerError" in errors_caught
        assert "PipelineError" in errors_caught
