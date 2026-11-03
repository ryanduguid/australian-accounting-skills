# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""The financial statements skill records whether a sustainability report is also due."""

import json
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parents[1] / ".claude" / "skills" / "au-financial-statements"
SKILL = SKILL_DIR / "SKILL.md"


class SustainabilityReportScopeStep(unittest.TestCase):
    """The Chapter 2M scope check is sourced, dated and kept apart from the statements."""

    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")
        start = self.text.index(
            "2. Record whether Chapter 2M of the Corporations Act also requires"
        )
        self.step = self.text[start : self.text.index("3. Map every trial-balance account", start)]

    def test_thresholds_are_those_in_section_292a(self) -> None:
        self.assertIn("a threshold in section 292A", self.step)
        self.assertIn("2 of the 3 corporate size thresholds", self.step)
        self.assertIn("National Greenhouse and Energy Reporting Act 2007", self.step)
        self.assertIn("retail CCIV, the value of assets threshold", self.step)

    def test_an_entity_without_a_chapter_2m_report_needs_none(self) -> None:
        self.assertIn("An entity with no Chapter 2M financial report needs none", self.step)
        self.assertIn("an entity relying on ASIC relief from one", self.step)

    def test_phase_in_is_dated_and_rechecked(self) -> None:
        self.assertIn("As at 4 November 2026", self.step)
        for start in ("1 January 2025 (Group 1)", "1 July 2026 (Group 2)", "1 July 2027 (Group 3)"):
            self.assertIn(start, self.step)
        self.assertIn("large proprietary company thresholds in section 45A", self.step)
        self.assertIn("from RG 280 Section B and the Act at use time", self.step)

    def test_the_outcome_is_recorded_not_prepared(self) -> None:
        self.assertIn("the group and the check date, or `UNVERIFIED`", self.step)
        self.assertIn("a separate deliverable that this skill does not prepare", self.step)
        self.assertIn("and the sustainability report scope record", self.text)

    def test_the_asic_sources_are_cited_and_recorded(self) -> None:
        recorded = {
            s["url"]
            for s in json.loads((SKILL_DIR / "sources.json").read_text(encoding="utf-8"))["sources"]
        }
        for slug in (
            "/sustainability-reporting",
            "who-must-prepare-a-sustainability-report",
            "rg-280-sustainability-reporting",
        ):
            self.assertIn(slug, self.text)
            self.assertTrue(any(url.endswith(slug) for url in recorded), slug)


if __name__ == "__main__":
    unittest.main()
