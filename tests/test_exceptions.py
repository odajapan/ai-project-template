import pytest

from your_project_name.exceptions import DataValidationError, LLMError, ProjectError


def test_exception_hierarchy() -> None:
    assert issubclass(LLMError, ProjectError)
    assert issubclass(DataValidationError, ProjectError)
    assert issubclass(ProjectError, Exception)


def test_llm_error_raises() -> None:
    with pytest.raises(LLMError, match="upstream error"):
        raise LLMError("upstream error")


def test_data_validation_error_raises() -> None:
    with pytest.raises(DataValidationError):
        raise DataValidationError("bad input")
