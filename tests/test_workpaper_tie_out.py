# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""Regression gates for the workpaper-tie-out skill and its validation card."""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILL = "workpaper-tie-out"


def skill_text() -> str:
    text = (REPOSITORY / ".claude" / "skills" / SKILL / "SKILL.md").read_text(encoding="utf-8")
    return " ".join(text.split())


def step(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin : text.index(end, begin)]


class WorkpaperTieOutTests(unittest.TestCase):
    def test_the_trace_runs_both_ways(self) -> None:
        trace = step(skill_text(), "2. **Trace and agree both ways.**", "3. **Recalculate.**")
        self.assertIn("Agree each statement amount to its workpaper, and the workpaper to its source export.", trace)
        self.assertIn("trace each figure in each workpaper back to its source figure", trace)
        self.assertIn("each source export total forward to the workpaper and statement line that uses it", trace)
        self.assertIn("a source total that reaches no workpaper or statement line, is an exception", trace)
        self.assertIn("agreement in one direction does not clear it", trace)

    def test_narrative_figures_are_recomputed(self) -> None:
        recalculation = step(skill_text(), "3. **Recalculate.**", "4. **Check comparatives.**")
        self.assertIn("Recompute every figure quoted in narrative", recalculation)
        self.assertIn("including movements, percentages and totals given in words", recalculation)
        self.assertIn("A narrative figure that does not recompute is an exception even when the schedules agree.", recalculation)

    def test_a_no_exceptions_statement_is_tested_against_open_flags(self) -> None:
        exceptions = step(skill_text(), "6. **Write the exceptions list.**", "## Output")
        self.assertIn("test any statement in the pack that there are no exceptions", exceptions)
        self.assertIn("Compare it with the open flags: this list, unresolved review notes, gate results and open preparer queries.", exceptions)
        self.assertIn("record the statement as unsupported and add it to the list", exceptions)
        self.assertIn("do not edit the statement or close the flag", exceptions)

    def test_completion_requires_both_directions_and_narrative_recalculation(self) -> None:
        output = step(skill_text(), "## Output", "## Boundaries")
        self.assertIn("both trace directions are done, recalculations (including narrative figures)", output)

    def test_a_fabricated_card_exercises_both_directions(self) -> None:
        card = (REPOSITORY / "validation" / "cases" / "workpaper-tie-out-both-ways.md").read_text(encoding="utf-8")
        self.assertIn("  - workpaper-tie-out\n", card)
        self.assertIn("list accrued expenses of 35.00 as a source total", card)
        self.assertIn("list the stated 50.00 as an exception of 10.00", card)
        self.assertIn("record it as unsupported", card)


if __name__ == "__main__":
    unittest.main()
