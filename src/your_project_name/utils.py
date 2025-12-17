"""Utility helpers for your_project_name.

These functions are intentionally small and well-typed so that they can serve
as examples of how to write unit-testable, type-annotated code in projects
derived from this template.
"""

from __future__ import annotations

import re
from typing import Sequence


def normalize_scores(scores: Sequence[float]) -> list[float]:
    """Normalize numeric scores to the 0–1 range.

    * An empty input sequence results in an empty list.
    * A constant input sequence results in a list of zeros.
    """

    values = list(scores)
    if not values:
        return []

    minimum = min(values)
    maximum = max(values)

    if minimum == maximum:
        return [0.0 for _ in values]

    scale = maximum - minimum
    return [(score - minimum) / scale for score in values]


def slugify(text: str) -> str:
    """Convert *text* into a simple slug.

    The result contains only lowercase ASCII letters, digits, and single
    dashes, making it suitable for use in file names or identifiers.
    """

    normalized = text.strip().lower()
    normalized = re.sub(r"\s+", "-", normalized)
    normalized = re.sub(r"[^a-z0-9\-]", "", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized)
    return normalized.strip("-")
