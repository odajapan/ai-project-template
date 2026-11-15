import pytest

from your_project_name.utils import chunked, normalize_scores, slugify


def test_normalize_scores_empty() -> None:
    assert normalize_scores([]) == []


def test_normalize_scores_scales_between_zero_and_one() -> None:
    scores = [10.0, 20.0, 30.0]
    normalized = normalize_scores(scores)

    assert normalized[0] == 0.0
    assert normalized[-1] == 1.0
    assert all(0.0 <= value <= 1.0 for value in normalized)


def test_normalize_scores_constant_input() -> None:
    scores = [5.0, 5.0, 5.0]
    normalized = normalize_scores(scores)

    assert normalized == [0.0, 0.0, 0.0]


def test_slugify_basic() -> None:
    assert slugify("Hello World") == "hello-world"


def test_slugify_strips_and_simplifies() -> None:
    assert slugify("  Hello,   World!!  ") == "hello-world"


def test_chunked_even_split() -> None:
    assert chunked([1, 2, 3, 4], 2) == [[1, 2], [3, 4]]


def test_chunked_rejects_non_positive_size() -> None:
    with pytest.raises(ValueError):
        chunked([1, 2], 0)
