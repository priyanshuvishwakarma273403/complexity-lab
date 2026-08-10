"""Tests for estimator interfaces."""

from collections.abc import Callable
from typing import Any

import pytest

from complexity_lab.interfaces import BaseDynamicEstimator, BaseStaticEstimator
from complexity_lab.models import ComplexityClass, ComplexityResult, SourceUnit


class ConcreteStaticEstimator(BaseStaticEstimator):
    def analyze(self, unit: SourceUnit) -> ComplexityResult:
        self.last_unit = unit
        return ComplexityResult(
            best_case=ComplexityClass.CONSTANT,
            worst_case=ComplexityClass.EXPONENTIAL,
            average_case=ComplexityClass.LINEAR,
        )


class ConcreteDynamicEstimator(BaseDynamicEstimator):
    def analyze(
        self,
        target: Callable[..., Any],
        input_generator: Callable[[int], Any],
    ) -> ComplexityResult:
        self.last_target = target
        self.last_generator = input_generator
        return ComplexityResult(
            best_case=ComplexityClass.LINEAR,
            worst_case=ComplexityClass.QUADRATIC,
            average_case=ComplexityClass.LINEAR,
        )


def test_static_estimator_is_abstract() -> None:
    with pytest.raises(TypeError, match="abstract"):
        BaseStaticEstimator()  # type: ignore[abstract]


def test_dynamic_estimator_is_abstract() -> None:
    with pytest.raises(TypeError, match="abstract"):
        BaseDynamicEstimator()  # type: ignore[abstract]


def test_static_estimator_accepts_source_unit() -> None:
    unit = SourceUnit(name="f", source="def f(x): return x")
    estimator = ConcreteStaticEstimator()
    result = estimator.analyze(unit)
    assert isinstance(result, ComplexityResult)
    assert estimator.last_unit == unit


def test_dynamic_estimator_is_invoked_with_target_and_generator() -> None:
    estimator = ConcreteDynamicEstimator()

    def target(xs: list[int]) -> int:
        return sum(xs)

    def generator(n: int) -> list[int]:
        return list(range(n))

    result = estimator.analyze(target, generator)
    assert isinstance(result, ComplexityResult)
    assert estimator.last_target is target
    assert estimator.last_generator is generator
