"""Tests for the Markdown complexity explainer."""

from complexity_lab.analyzers.explainer import MIN_TRUSTWORTHY_FIT, ComplexityExplainer
from complexity_lab.models import ComplexityClass, ComplexityEstimate, LoopEvidence

NESTED_LOOPS = (
    LoopEvidence(line=8, depth=1, iteration_desc="N times", parent_id=None),
    LoopEvidence(line=9, depth=2, iteration_desc="N times", parent_id=8),
)


def _static(
    time_class: ComplexityClass = ComplexityClass.QUADRATIC,
    space_class: ComplexityClass = ComplexityClass.CONSTANT,
    loops: tuple[LoopEvidence, ...] = NESTED_LOOPS,
) -> ComplexityEstimate:
    return ComplexityEstimate(
        time_class=time_class,
        space_class=space_class,
        loops=loops,
    )


def _dynamic(
    time_class: ComplexityClass = ComplexityClass.QUADRATIC,
    space_class: ComplexityClass = ComplexityClass.CONSTANT,
    r_squared: float | None = 0.999,
) -> ComplexityEstimate:
    return ComplexityEstimate(
        time_class=time_class,
        space_class=space_class,
        r_squared=r_squared,
    )


def test_explain_returns_all_sections() -> None:
    report = ComplexityExplainer(_static(), _dynamic()).explain()

    assert isinstance(report, str)
    for heading in (
        "# Complexity Report",
        "## Summary",
        "## Time Complexity",
        "## Space Complexity",
        "## Verdict",
    ):
        assert heading in report
    assert report.endswith("\n")


def test_summary_table_shows_both_estimates() -> None:
    table = ComplexityExplainer(
        _static(time_class=ComplexityClass.QUADRATIC),
        _dynamic(time_class=ComplexityClass.LINEAR),
    )._render_summary_table()

    assert "| Aspect | Static (AST) | Empirical (measured) |" in table
    assert "| --- | --- | --- |" in table
    assert "| Time | O(N^2) | O(N) |" in table
    assert "| Space | O(1) | O(1) |" in table
    assert "| Fit (R^2) | n/a | 0.999 |" in table


def test_summary_table_without_dynamic_estimate() -> None:
    table = ComplexityExplainer(_static())._render_summary_table()

    assert "| Time | O(N^2) | not measured |" in table
    assert "| Fit (R^2) | n/a | n/a |" in table


def test_narrate_loops_without_loops() -> None:
    narration = ComplexityExplainer(
        _static(time_class=ComplexityClass.CONSTANT, loops=())
    )._narrate_loops()

    assert "No iteration constructs were detected" in narration
    assert "O(1)" in narration


def test_narrate_loops_with_single_loop() -> None:
    loops = (LoopEvidence(line=3, depth=1, iteration_desc="N times", parent_id=None),)
    narration = ComplexityExplainer(
        _static(time_class=ComplexityClass.LINEAR, loops=loops)
    )._narrate_loops()

    assert "an outer loop at line 3 iterating N times" in narration
    assert "implies O(N) (linear) complexity" in narration
    assert "add together rather than multiply" not in narration


def test_narrate_loops_with_nested_pair() -> None:
    narration = ComplexityExplainer(_static())._narrate_loops()

    assert (
        "We detected an outer loop at line 8 iterating N times, and an inner loop at line 9 "
        "running N times." in narration
    )
    assert "implies O(N^2) (quadratic) complexity" in narration


def test_narrate_loops_labels_third_level_by_depth() -> None:
    loops = (
        LoopEvidence(line=1, depth=1, iteration_desc="N times", parent_id=None),
        LoopEvidence(line=2, depth=2, iteration_desc="N times", parent_id=1),
        LoopEvidence(line=3, depth=3, iteration_desc="N times", parent_id=2),
    )
    narration = ComplexityExplainer(
        _static(time_class=ComplexityClass.CUBIC, loops=loops)
    )._narrate_loops()

    assert "a loop nested at depth 3 at line 3 running N times" in narration


def test_narrate_loops_flags_sibling_loops_as_additive() -> None:
    loops = (
        LoopEvidence(line=2, depth=1, iteration_desc="N times", parent_id=1),
        LoopEvidence(line=9, depth=1, iteration_desc="N times", parent_id=1),
    )
    narration = ComplexityExplainer(
        _static(time_class=ComplexityClass.LINEAR, loops=loops)
    )._narrate_loops()

    assert "add together rather than multiply" in narration
    assert "a top-level loop at line 2 running N times" in narration
    assert "inner loop" not in narration


def test_time_section_reports_curve_fit() -> None:
    section = ComplexityExplainer(_static(), _dynamic())._render_time_section()

    assert (
        "Our runtime curve-fitting tests matched the O(N^2) (quadratic) model with an R^2 of 0.999."
        in section
    )


def test_time_section_reports_match_without_r_squared() -> None:
    section = ComplexityExplainer(
        _static(),
        _dynamic(
            time_class=ComplexityClass.QUADRATIC,
            r_squared=None,
        ),
    )._render_time_section()

    assert "Our runtime measurements matched the O(N^2) (quadratic) model." in section
    assert "R^2" not in section


def test_verdict_on_agreement_confirms_bound() -> None:
    verdict = ComplexityExplainer(_static(), _dynamic())._narrate_verdict()

    assert "agree on O(N^2)" in verdict
    assert "confirming the theoretical bounds" in verdict


def test_verdict_when_static_is_looser_explains_early_exit() -> None:
    verdict = ComplexityExplainer(
        _static(time_class=ComplexityClass.QUADRATIC),
        _dynamic(time_class=ComplexityClass.LINEAR),
    )._narrate_verdict()

    assert "Static analysis predicted O(N^2) but measurement showed the faster O(N)." in verdict
    assert "`break`" in verdict
    assert "worst case" in verdict
    assert "Treat O(N^2) as the guarantee and O(N) as the typical case." in verdict


def test_verdict_when_static_is_tighter_points_at_hidden_cost() -> None:
    verdict = ComplexityExplainer(
        _static(time_class=ComplexityClass.LINEAR),
        _dynamic(time_class=ComplexityClass.QUADRATIC),
    )._narrate_verdict()

    assert "grows faster than the O(N) predicted" in verdict
    assert "amortized container resize" in verdict


def test_verdict_on_poor_fit_reports_unreliable_measurement() -> None:
    verdict = ComplexityExplainer(
        _static(time_class=ComplexityClass.LINEAR),
        _dynamic(time_class=ComplexityClass.QUADRATIC, r_squared=0.42),
    )._narrate_verdict()

    assert "did not fit any growth model closely (R^2 of 0.420)" in verdict
    assert "unreliable" in verdict
    # A bad fit must not be narrated as a real complexity disagreement.
    assert "grows faster than" not in verdict
    assert "hidden" not in verdict


def test_poor_fit_threshold_boundary_is_trusted() -> None:
    verdict = ComplexityExplainer(
        _static(time_class=ComplexityClass.LINEAR),
        _dynamic(time_class=ComplexityClass.LINEAR, r_squared=MIN_TRUSTWORTHY_FIT),
    )._narrate_verdict()

    assert "unreliable" not in verdict
    assert "confirming the theoretical bounds" in verdict


def test_verdict_without_dynamic_estimate_is_theoretical_only() -> None:
    verdict = ComplexityExplainer(_static(time_class=ComplexityClass.LINEAR))._narrate_verdict()

    assert "static analysis alone" in verdict
    assert "theoretical worst-case bound" in verdict


def test_verdict_with_unknown_static_class() -> None:
    verdict = ComplexityExplainer(
        _static(time_class=ComplexityClass.UNKNOWN),
        _dynamic(time_class=ComplexityClass.LINEAR),
    )._narrate_verdict()

    assert "Static analysis could not determine a growth class" in verdict
    assert "O(N)" in verdict


def test_verdict_with_unknown_dynamic_class() -> None:
    verdict = ComplexityExplainer(
        _static(time_class=ComplexityClass.LINEAR),
        _dynamic(time_class=ComplexityClass.UNKNOWN, r_squared=None),
    )._narrate_verdict()

    assert "Measurement could not determine a growth class" in verdict
    assert "O(N) bound stands unconfirmed" in verdict


def test_verdict_with_both_unknown() -> None:
    verdict = ComplexityExplainer(
        _static(time_class=ComplexityClass.UNKNOWN),
        _dynamic(time_class=ComplexityClass.UNKNOWN, r_squared=None),
    )._narrate_verdict()

    assert "Neither static analysis nor measurement" in verdict


def test_space_section_describes_constant_memory() -> None:
    section = ComplexityExplainer(_static(), _dynamic())._render_space_section()

    assert (
        "Peak memory allocations remained constant (O(1)) across all profiled sizes, indicating "
        "no auxiliary storage scaling." in section
    )


def test_space_section_describes_growing_memory() -> None:
    section = ComplexityExplainer(
        _static(space_class=ComplexityClass.LINEAR),
        _dynamic(space_class=ComplexityClass.LINEAR),
    )._render_space_section()

    assert "grew as O(N) (linear)" in section
    assert "scales with the input" in section


def test_space_section_falls_back_to_static_when_unprofiled() -> None:
    explainer = ComplexityExplainer(_static(space_class=ComplexityClass.LINEAR))
    section = explainer._render_space_section()

    assert "Static analysis expects O(N) (linear) auxiliary space" in section
    assert "Memory was not profiled" in section


def test_space_section_when_undetermined() -> None:
    section = ComplexityExplainer(
        _static(space_class=ComplexityClass.UNKNOWN)
    )._render_space_section()

    assert "Space complexity could not be determined from static analysis." in section
