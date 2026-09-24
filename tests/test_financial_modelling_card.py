"""Regression gates for the financial-modelling skill and its validation card."""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]


def card_text() -> str:
    return (
        REPOSITORY / "validation" / "cases" / "financial-modelling-structure-faults.md"
    ).read_text(encoding="utf-8")


def skill_text() -> str:
    return (
        REPOSITORY / ".claude" / "skills" / "financial-modelling" / "SKILL.md"
    ).read_text(encoding="utf-8")


class FinancialModellingTests(unittest.TestCase):
    def test_card_keeps_the_structure_faults_explicit(self) -> None:
        text = card_text()
        self.assertIn("typed over a formula in two months", text)
        self.assertIn("the workbook has no check rows", text)
        self.assertIn("the assumptions sit on the calculation sheet", text)
        self.assertNotIn("the summary line is reliable", text)

    def test_card_never_accepts_the_summary_line_without_checks(self) -> None:
        text = card_text()
        self.assertIn("Do not accept the summary line as verified", text)
        self.assertIn("carry the unverified status explicitly", text)
        self.assertIn("leave the finance request as a reviewer decision", text)
        self.assertIn(
            "An authorised human makes the financial and accounting decisions", text
        )

    def test_skill_keeps_the_untrusted_content_and_check_rules(self) -> None:
        text = skill_text()
        self.assertIn("instructions found inside", text)
        self.assertIn("untrusted content", text)
        self.assertIn("Rows labelled `check_*` that evaluate to zero", text)
        self.assertIn("A non-zero check is a broken model", text)
        self.assertIn("never recall them from memory", text)
        self.assertNotIn("guaranteed accurate", text)


if __name__ == "__main__":
    unittest.main()
