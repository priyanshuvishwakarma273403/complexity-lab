"""Core domain models for complexity analysis."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

DEFAULT_CONFIDENCE = 1.0


class ComplexityClass(Enum):
    """Canonical Big-O complexity classes."""

    CONSTANT = "O(1)"
    LOGARITHMIC = "O(log n)"
    LINEAR = "O(n)"
    LINEARITHMIC = "O(n log n)"
    QUADRATIC = "O(n^2)"
    EXPONENTIAL = "O(2^n)"
    UNKNOWN = "O(?)"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class SourceUnit:
    """A parsed function or code snippet under analysis."""

    name: str
    source: str
    language: str = "python"
    file_path: str | None = None


@dataclass(frozen=True, slots=True)
class ComplexityResult:
    """The outcome of a complexity analysis run.

    Args:
        best_case: Complexity of the most favourable input.
        worst_case: Complexity of the least favourable input.
        average_case: Expected complexity over all inputs.
        confidence: How certain the estimator is, in ``[0, 1]``.
        contributing_locations: Source locations (e.g. ``file.py:12`` or an
            expression) that drive the complexity.
    """

    best_case: ComplexityClass
    worst_case: ComplexityClass
    average_case: ComplexityClass
    confidence: float = DEFAULT_CONFIDENCE
    contributing_locations: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError(f"confidence must be in [0, 1], got {self.confidence!r}")
