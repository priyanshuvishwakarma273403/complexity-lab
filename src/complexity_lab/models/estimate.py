"""Shared data contract for static and dynamic complexity estimates."""

from dataclasses import dataclass
from enum import Enum


class ComplexityClass(Enum):
    """A complexity growth class, ordered by ``rank``.

    Ranks are spaced by 10 so intermediate classes can be added without renumbering.
    """

    UNKNOWN = (-1, "unknown", "undetermined")
    CONSTANT = (0, "O(1)", "constant")
    LOGARITHMIC = (10, "O(log N)", "logarithmic")
    LINEAR = (20, "O(N)", "linear")
    LINEARITHMIC = (30, "O(N log N)", "linearithmic")
    QUADRATIC = (40, "O(N^2)", "quadratic")
    CUBIC = (50, "O(N^3)", "cubic")
    EXPONENTIAL = (60, "O(2^N)", "exponential")
    FACTORIAL = (70, "O(N!)", "factorial")

    def __init__(self, rank: int, label: str, plain_name: str) -> None:
        self._rank = rank
        self._label = label
        self._plain_name = plain_name
    
    @property
    def rank(self) -> int:
        """Ordering key. Higher means faster-growing; ``UNKNOWN`` sorts below everything."""
        return self._rank

    @property
    def label(self) -> str:
        """Big-O notation, e.g. ``"O(N^2)"``."""
        return self._label

    @property
    def plain_name(self) -> str:
        """Plain-English name, e.g. ``"quadratic"``."""
        return self._plain_name

    @property
    def is_known(self) -> bool:
        """False only for :attr:`UNKNOWN`."""
        return self is not ComplexityClass.UNKNOWN


@dataclass(frozen=True)
class LoopEvidence:
    """One iteration construct found by static analysis."""

    line: int
    depth: int
    iteration_desc: str


@dataclass(frozen=True)
class ComplexityEstimate:
    """A complexity estimate from one source.

    Static estimates populate :attr:`loops` and leave :attr:`r_squared` as ``None``; dynamic
    estimates do the inverse. A single type is used for both so that comparison and rendering
    need no per-source branching.
    """

    time_class: ComplexityClass
    space_class: ComplexityClass = ComplexityClass.UNKNOWN
    loops: tuple[LoopEvidence, ...] = ()
    r_squared: float | None = None
    source: str = "static"
