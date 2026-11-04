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
        self.assertIn("Both the size and asset tests include any entities it controls", self.step)

    def test_an_entity_without_a_chapter_2m_report_needs_none(self) -> None:
        self.assertIn("An entity with no Chapter 2M financial report needs none", self.step)
        self.assertIn("an entity relying on ASIC relief from one", self.step)

    def test_phase_in_is_dated_and_rechecked(self) -> None:
        self.assertIn("As at 4 November 2026", self.step)
        for start in ("1 January 2025 (Group 1)", "1 July 2026 (Group 2)", "1 July 2027 (Group 3)"):
            self.assertIn(start, self.step)
        self.assertIn("large proprietary company thresholds in section 45A", self.step)
        self.assertIn(
            "the proposals are not yet in effect, and the existing thresholds apply", self.step
        )
        self.assertIn("from RG 280 Section B and the Act at use time", self.step)

    def test_the_outcome_is_recorded_not_prepared(self) -> None:
        self.assertIn("the group and the check date, or `UNVERIFIED`", self.step)
        self.assertIn("a separate deliverable that this skill does not prepare", self.step)
        self.assertIn(
            "approves accounting judgements and the sustainability report scope record", self.text
        )

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


class Aasb18TransitionCheck(unittest.TestCase):
    """Step 1 records AASB 18's first period and the AASB 108 disclosure before it."""

    def setUp(self) -> None:
        self.text = " ".join(SKILL.read_text(encoding="utf-8").split())
        start = self.text.index("1. Confirm the applicable reporting framework")
        self.step = self.text[start : self.text.index("2. Record whether Chapter 2M", start)]

    def test_application_dates_are_dated_and_paragraph_cited(self) -> None:
        self.assertIn("As at 4 November 2026, AASB 18", self.step)
        self.assertIn(
            "annual reporting periods beginning on or after 1 January 2027 (paragraph C1)",
            self.step,
        )
        self.assertIn(
            "not-for-profit private and public sector entities and superannuation entities "
            "applying AASB 1056 from periods beginning on or after 1 January 2028 "
            "(paragraph AusC1.1)",
            self.step,
        )

    def test_the_comparative_period_is_recorded(self) -> None:
        self.assertIn(
            "whether this period is the comparative period immediately before it", self.step
        )
        self.assertIn("(paragraph C2)", self.step)
        self.assertIn("(paragraph C3)", self.step)

    def test_a_standard_issued_but_not_yet_effective_is_disclosed(self) -> None:
        self.assertIn("the statements must comply with AASB 108", self.step)
        self.assertIn("what paragraph 30 of AASB 108 requires", self.step)
        self.assertIn("known or reasonably estimable information", self.step)

    def test_the_aasb_sources_are_cited_and_recorded(self) -> None:
        recorded = {
            s["url"]
            for s in json.loads((SKILL_DIR / "sources.json").read_text(encoding="utf-8"))["sources"]
        }
        for url in (
            "https://standards.aasb.gov.au/node/3710",
            "https://standards.aasb.gov.au/aasb-108-mar-2021",
        ):
            self.assertIn(f"]({url})", self.text)
            self.assertIn(url, recorded)

    def test_a_fabricated_card_exercises_the_check(self) -> None:
        card = Path(__file__).resolve().parents[1] / "validation" / "cases" / (
            "au-financial-statements-aasb-18-comparative-year.md"
        )
        text = card.read_text(encoding="utf-8")
        self.assertIn("  - au-financial-statements\n", text)
        self.assertIn("year ending 31 December 2026", text)
        self.assertIn("AASB 108 paragraph 30", text)


if __name__ == "__main__":
    unittest.main()
