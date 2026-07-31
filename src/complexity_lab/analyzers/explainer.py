"""Natural-language Markdown explanations of complexity estimates."""

from complexity_lab.models import ComplexityClass, ComplexityEstimate, LoopEvidence
from collections import Counter

MIN_TRUSTWORTHY_FIT = 0.9
"""Below this R-squared, the fit is reported as unreliable rather than as a bound."""

_ORDINALS = ("outer", "inner")


class ComplexityExplainer:
    """Turns a static and an optional dynamic estimate into a Markdown report.

    The report explains *why* a bound holds -- which loops drove it, and whether measurement
    agreed -- rather than only stating the result.
    """

    def __init__(
        self,
        static: ComplexityEstimate,
        dynamic: ComplexityEstimate | None = None,
    ) -> None:
        self.static = static
        self.dynamic = dynamic

    def explain(self) -> str:
        """Render the full report."""
        sections = [
            self._render_header(),
            self._render_summary_table(),
            self._render_time_section(),
            self._render_space_section(),
            self._render_verdict(),
        ]
        return "\n\n".join(sections) + "\n"

    def _render_header(self) -> str:
        return "# Complexity Report"

    def _render_summary_table(self) -> str:
        measured = self.dynamic
        empirical_time = measured.time_class.label if measured is not None else "not measured"
        empirical_space = measured.space_class.label if measured is not None else "not measured"
        return "\n".join(
            [
                "## Summary",
                "",
                "| Aspect | Static (AST) | Empirical (measured) |",
                "| --- | --- | --- |",
                f"| Time | {self.static.time_class.label} | {empirical_time} |",
                f"| Space | {self.static.space_class.label} | {empirical_space} |",
                f"| Fit (R^2) | n/a | {self._format_fit()} |",
            ]
        )

    def _format_fit(self) -> str:
        if self.dynamic is None or self.dynamic.r_squared is None:
            return "n/a"
        return f"{self.dynamic.r_squared:.3f}"

    def _render_time_section(self) -> str:
        lines = ["## Time Complexity", "", self._narrate_loops()]
        if self.dynamic is not None and self.dynamic.time_class.is_known:
            lines.extend(["", self._narrate_fit(self.dynamic)])
        return "\n".join(lines)

    def _narrate_loops(self) -> str:
        loops = sorted(self.static.loops, key=lambda loop: (loop.depth, loop.line))
        if not loops:
            return (
                "No iteration constructs were detected; the routine runs a fixed number of "
                f"steps, implying {self.static.time_class.label} complexity."
            )

        has_siblings = self._has_siblings(loops)
        phrases = [
            self._describe_loop(loop, index, nested_chain=not has_siblings)
            for index, loop in enumerate(loops)
        ]
        detected = f"We detected {self._join_phrases(phrases)}."
        implication = (
            f"This structural layout implies {self.static.time_class.label} "
            f"({self.static.time_class.plain_name}) complexity."
        )
        parts = [detected, implication]
        if has_siblings:
            parts.append(
                "Note that loops at the same nesting depth run in sequence, so their costs add "
                "together rather than multiply."
            )
        return " ".join(parts)

    def _describe_loop(self, loop: LoopEvidence, index: int, *, nested_chain: bool) -> str:
        # "outer"/"inner" only make sense when each loop sits at its own depth; with siblings the
        # depth is the only honest description.
        if nested_chain and index < len(_ORDINALS):
            role = f"an {_ORDINALS[index]} loop"
            verb = "iterating" if index == 0 else "running"
        elif loop.depth <= 1:
            role = "a top-level loop"
            verb = "running"
        else:
            role = f"a loop nested at depth {loop.depth}"
            verb = "running"
        return f"{role} at line {loop.line} {verb} {loop.iteration_desc}"

    def _join_phrases(self, phrases: list[str]) -> str:
        if len(phrases) == 1:
            return phrases[0]
        return f"{', '.join(phrases[:-1])}, and {phrases[-1]}"

    def _has_siblings(self, loops: list[LoopEvidence]) -> bool:
        parent_counts = Counter(loop.parent_id for loop in loops if loop.parent_id is not None)
        return any(count > 1 for count in parent_counts.values())

    def _narrate_fit(self, dynamic: ComplexityEstimate) -> str:
        measured = dynamic.time_class
        if dynamic.r_squared is None:
            return (
                f"Our runtime measurements matched the {measured.label} "
                f"({measured.plain_name}) model."
            )
        if dynamic.r_squared < MIN_TRUSTWORTHY_FIT:
            return (
                f"Our runtime measurements did not fit the "
                f"{measured.label} ({measured.plain_name}) model closely "
                f"(R² = {dynamic.r_squared:.3f})."
            )
        return (
            f"Our runtime curve-fitting tests matched the {measured.label} "
            f"({measured.plain_name}) model with an R^2 of {dynamic.r_squared:.3f}."
        )

    def _render_space_section(self) -> str:
        return "\n".join(["## Space Complexity", "", self._narrate_space()])

    def _narrate_space(self) -> str:
        # No Dynamic Analysis
        if self.dynamic is None:
            declared = self.static.space_class
            if declared.is_known:
                return (
                    f"Static analysis expects {declared.label} ({declared.plain_name}) "
                    "auxiliary space. Memory was not profiled, so this bound is theoretical only."
                )
            return "Space complexity could not be determined from static analysis."

        measured = self.dynamic.space_class

        if measured is ComplexityClass.CONSTANT:
            return (
                "Peak memory allocations remained constant (O(1)) across all profiled "
                "sizes, indicating no auxiliary storage scaling."
            )

        if measured.is_known:
            return (
                f"Peak memory allocations grew as {measured.label} "
                f"({measured.plain_name}) across the profiled sizes, indicating "
                "auxiliary storage that scales with the input."
            )

        # Dynamic profiling was performed, but no growth class was determined.
        declared = self.static.space_class

        if declared.is_known:
            return (
                f"Memory was profiled, but no empirical space complexity could be "
                f"determined. Static analysis expects {declared.label} "
                f"({declared.plain_name}) auxiliary space."
            )

        return "Memory was profiled, but no empirical space complexity could be determined."

    def _render_verdict(self) -> str:
        return "\n".join(["## Verdict", "", self._narrate_verdict()])

    def _narrate_verdict(self) -> str:
        static_class = self.static.time_class
        if self.dynamic is None:
            return (
                f"This report is based on static analysis alone. {static_class.label} is a "
                "theoretical worst-case bound; run an empirical profile to confirm it."
            )

        fit = self.dynamic.r_squared
        if fit is not None and fit < MIN_TRUSTWORTHY_FIT:
            return (
                f"Our measurements did not fit any growth model closely (R^2 of {fit:.3f}), so "
                "the empirical figure should be treated as unreliable rather than as a competing "
                "bound. This is a measurement problem, not evidence about your code: profile "
                "over a wider range of input sizes, or reduce timing noise, then re-run."
            )

        measured = self.dynamic.time_class
        if not static_class.is_known or not measured.is_known:
            return self._narrate_unknown(static_class, measured)

        if static_class is measured:
            return (
                f"Static structure and empirical measurement agree on {static_class.label}, "
                "confirming the theoretical bounds."
            )
        if static_class.rank > measured.rank:
            return (
                f"Static analysis predicted {static_class.label} but measurement showed the "
                f"faster {measured.label}. Static analysis reports a worst case derived from "
                "loop structure, whereas measurement samples the inputs actually profiled. An "
                "early `break` or `return`, a short-circuited condition, or inputs that never "
                f"reach the worst case can all keep real runtime at {measured.label} even though "
                f"the loops could in principle cost {static_class.label}. Treat "
                f"{static_class.label} as the guarantee and {measured.label} as the typical case."
            )
        return (
            f"Measurement showed {measured.label}, which grows faster than the "
            f"{static_class.label} predicted from loop structure. The extra cost is coming from "
            "somewhere the loop analysis cannot see: work inside a called function, an amortized "
            "container resize, or a library operation that is not constant-time. Trust the "
            f"measured {measured.label} and audit the operations inside the loop bodies."
        )

    def _narrate_unknown(self, static_class: ComplexityClass, measured: ComplexityClass) -> str:
        if not static_class.is_known and not measured.is_known:
            return (
                "Neither static analysis nor measurement could determine a growth class, so no "
                "comparison is possible."
            )
        if not static_class.is_known:
            return (
                "Static analysis could not determine a growth class, so the measured "
                f"{measured.label} stands unverified against the code structure."
            )
        return (
            f"Measurement could not determine a growth class, so the static {static_class.label} "
            "bound stands unconfirmed."
        )
