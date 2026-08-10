"""Interfaces for complexity estimators."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from complexity_lab.models.complexity import ComplexityResult, SourceUnit


class BaseStaticEstimator(ABC):
    """Analyses source code without executing it.

    Implementations inspect the parsed source (e.g. via an AST) and derive
    the expected complexity statically.
    """

    @abstractmethod
    def analyze(self, unit: SourceUnit) -> ComplexityResult:
        """Estimate the complexity of ``unit`` without running it.

        Args:
            unit: The source unit (function or snippet) to analyse.

        Returns:
            A ``ComplexityResult`` describing best, worst and average case.
        """


class BaseDynamicEstimator(ABC):
    """Analyses the complexity of a callable via instrumented execution.

    Implementations run the target against inputs of varying sizes, measure
    runtime and memory, and derive the complexity from the measurements.
    """

    @abstractmethod
    def analyze(
        self,
        target: Callable[..., Any],
        input_generator: Callable[[int], Any],
    ) -> ComplexityResult:
        """Estimate the complexity of ``target`` by executing it.

        Args:
            target: The callable to profile.
            input_generator: Builds a valid input of a given size.

        Returns:
            A ``ComplexityResult`` describing best, worst and average case.
        """
