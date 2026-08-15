"""Tests for core domain models."""

from typing import Any

import pytest

from complexity_lab.models import ComplexityClass, ComplexityResult, SourceUnit


class TestComplexityClass:
    def test_members_cover_common_classes(self) -> None:
        expected = {
            ComplexityClass.CONSTANT,
            ComplexityClass.LOGARITHMIC,
            ComplexityClass.LINEAR,
            ComplexityClass.LINEARITHMIC,
            ComplexityClass.QUADRATIC,
            ComplexityClass.EXPONENTIAL,
            ComplexityClass.UNKNOWN,
        }
        assert set(ComplexityClass) == expected

    def test_value_matches_big_o_notation(self) -> None:
        assert ComplexityClass.LINEAR.value == "O(n)"
        assert ComplexityClass.QUADRATIC.value == "O(n^2)"

    def test_str_returns_big_o_notation(self) -> None:
        assert str(ComplexityClass.EXPONENTIAL) == "O(2^n)"


class TestSourceUnit:
    def test_construction_with_defaults(self) -> None:
        unit = SourceUnit(name="linear_scan", source="def f(x): ...")
        assert unit.name == "linear_scan"
        assert unit.language == "python"
        assert unit.file_path is None

    def test_equality(self) -> None:
        unit_a = SourceUnit(name="f", source="...", language="python", file_path="a.py")
        unit_b = SourceUnit(name="f", source="...", language="python", file_path="a.py")
        assert unit_a == unit_b
        assert hash(unit_a) == hash(unit_b)

    def test_inequality(self) -> None:
        unit_a = SourceUnit(name="f", source="...")
        unit_b = SourceUnit(name="g", source="...")
        assert unit_a != unit_b


class TestComplexityResult:
    def test_construction(self) -> None:
        result = ComplexityResult(
            best_case=ComplexityClass.LINEAR,
            worst_case=ComplexityClass.QUADRATIC,
            average_case=ComplexityClass.LINEAR,
            confidence=0.95,
            contributing_locations=("a.py:7", "a.py:12"),
        )
        assert result.best_case is ComplexityClass.LINEAR
        assert result.worst_case is ComplexityClass.QUADRATIC
        assert result.average_case is ComplexityClass.LINEAR
        assert result.confidence == 0.95
        assert result.contributing_locations == ("a.py:7", "a.py:12")

    def test_defaults(self) -> None:
        result = ComplexityResult(
            best_case=ComplexityClass.CONSTANT,
            worst_case=ComplexityClass.CONSTANT,
            average_case=ComplexityClass.CONSTANT,
        )
        assert result.confidence == pytest.approx(1.0)
        assert result.contributing_locations == ()

    def test_equality(self) -> None:
        kwargs: dict[str, Any] = {
            "best_case": ComplexityClass.LINEAR,
            "worst_case": ComplexityClass.QUADRATIC,
            "average_case": ComplexityClass.LINEAR,
            "confidence": 0.9,
            "contributing_locations": ("a.py:7",),
        }
        assert ComplexityResult(**kwargs) == ComplexityResult(**kwargs)
        assert hash(ComplexityResult(**kwargs)) == hash(ComplexityResult(**kwargs))

    def test_inequality_on_case(self) -> None:
        assert ComplexityResult(
            best_case=ComplexityClass.LINEAR,
            worst_case=ComplexityClass.QUADRATIC,
            average_case=ComplexityClass.LINEAR,
        ) != ComplexityResult(
            best_case=ComplexityClass.LINEAR,
            worst_case=ComplexityClass.EXPONENTIAL,
            average_case=ComplexityClass.LINEAR,
        )

    def test_inequality_on_confidence(self) -> None:
        assert ComplexityResult(
            best_case=ComplexityClass.LINEAR,
            worst_case=ComplexityClass.LINEAR,
            average_case=ComplexityClass.LINEAR,
            confidence=0.9,
        ) != ComplexityResult(
            best_case=ComplexityClass.LINEAR,
            worst_case=ComplexityClass.LINEAR,
            average_case=ComplexityClass.LINEAR,
            confidence=1.0,
        )

    @pytest.mark.parametrize("confidence", [-0.01, 1.01, 5.0])
    def test_confidence_out_of_range_rejected(self, confidence: float) -> None:
        with pytest.raises(ValueError, match="confidence"):
            ComplexityResult(
                best_case=ComplexityClass.LINEAR,
                worst_case=ComplexityClass.LINEAR,
                average_case=ComplexityClass.LINEAR,
                confidence=confidence,
            )

    def test_confidence_boundaries_accepted(self) -> None:
        for confidence in (0.0, 1.0):
            ComplexityResult(
                best_case=ComplexityClass.LINEAR,
                worst_case=ComplexityClass.LINEAR,
                average_case=ComplexityClass.LINEAR,
                confidence=confidence,
            )
