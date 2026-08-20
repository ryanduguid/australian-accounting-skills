"""Contract checks for Payday Super guidance used by maintained skills."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
SKILL_FILES = {
    "stp-finalisation": REPOSITORY / ".claude" / "skills" / "stp-finalisation" / "SKILL.md",
    "month-end-close": REPOSITORY / ".claude" / "skills" / "month-end-close" / "SKILL.md",
    "cashflow-forecast-13week": (
        REPOSITORY / ".claude" / "skills" / "cashflow-forecast-13week" / "SKILL.md"
    ),
}

ATO_PAYDAY_SUPER = "https://softwaredevelopers.ato.gov.au/PaydaySuper"
PAYDAY_SUPER_ACT = "https://www.legislation.gov.au/C2025A00057/asmade/text"
SGA_REGULATIONS = "https://www.legislation.gov.au/F2018L01289/latest/text"


def compact(text: str) -> str:
    """Normalise Markdown whitespace while retaining its substantive wording."""
    return re.sub(r"\s+", " ", text).strip().lower()


class PaydaySuperGuidanceTests(unittest.TestCase):
    def test_each_skill_checks_allowable_period_before_a_late_classification(self) -> None:
        """A universal seven-day shortcut must not drive a late or SGC outcome."""
        for skill, path in SKILL_FILES.items():
            content = compact(path.read_text(encoding="utf-8"))
            with self.subTest(skill=skill):
                self.assertRegex(content, r"ordinary.{0,80}(?:seven|7)[ -]business-day")
                self.assertIn(
                    "by the end of the seventh business day after the payday",
                    content,
                )
                self.assertIn("allowable longer period", content)
                self.assertRegex(
                    content,
                    r"check.{0,160}allowable longer period.{0,220}before.{0,120}(?:late|sgc)",
                )
                self.assertRegex(
                    content,
                    r"(?:missing|insufficient|unproven) facts.{0,160}(?:unknown|human review|review state)",
                )

    def test_each_skill_names_the_fact_dependent_longer_periods(self) -> None:
        """Removing any statutory branch must fail the maintained-skill contract."""
        for skill, path in SKILL_FILES.items():
            content = compact(path.read_text(encoding="utf-8"))
            with self.subTest(skill=skill):
                self.assertIn("20 business days", content)
                self.assertIn("first eligible contribution to a particular fund", content)
                self.assertIn("new starter", content)
                self.assertIn("recommencement", content)
                self.assertIn("fund change", content)
                self.assertIn("out-of-cycle", content)
                self.assertIn("subsequent standard qualifying-earnings payment", content)
                self.assertIn("exceptional-circumstances determination", content)
                self.assertIn("earlier contribution", content)
                self.assertIn("s 18c", content)
                self.assertIn("actual allocation", content)
                self.assertRegex(
                    content,
                    r"(?:planned|remitted).{0,120}(?:is not|does not establish).{0,80}fund receipt",
                )
                self.assertIn("enterprise agreements", content)
                self.assertIn("awards", content)
                self.assertIn("fund terms", content)
                self.assertIn("earlier payment", content)

    def test_each_skill_records_primary_sources_and_check_date(self) -> None:
        """Mutable deadline guidance must retain its source trail."""
        for skill, path in SKILL_FILES.items():
            content = path.read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertIn(ATO_PAYDAY_SUPER, content)
                self.assertIn(PAYDAY_SUPER_ACT, content)
                self.assertIn(SGA_REGULATIONS, content)
                self.assertIn("20 August 2026", content)


if __name__ == "__main__":
    unittest.main()
