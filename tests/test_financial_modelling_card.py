# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""Regression gates for the financial-modelling skill and its validation cards."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

from skill_prose import DO_NOT, section, sentences

REPOSITORY = Path(__file__).resolve().parents[1]


def card_text(name: str = "financial-modelling-structure-faults") -> str:
    return (REPOSITORY / "validation" / "cases" / f"{name}.md").read_text(encoding="utf-8")


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

    def assert_sentence(self, text: str, *patterns: str) -> None:
        """One sentence of `text` matches every pattern."""
        with self.subTest(patterns=patterns):
            self.assertTrue(
                any(all(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)
                    for sentence in sentences(text)),
                f"no sentence matches all of {patterns}",
            )

    def test_three_way_forecast_opens_from_the_trial_balance(self) -> None:
        text = section("financial-modelling", "Three-way forecast")
        self.assert_sentence(text, r"opening balance sheet from the trial balance", r"source log")
        self.assert_sentence(text, r"if the trial balance is missing, a line does not tie or the opening balance sheet does not balance, stop",
                             DO_NOT + r"plug it to equity, cash or a suspense line")

    def test_three_way_forecast_defines_check_balance_and_check_cash(self) -> None:
        text = section("financial-modelling", "Three-way forecast")
        self.assertIn("`check_balance` (total assets less total liabilities less equity)", text)
        self.assertIn("`check_cash` (balance sheet cash less the cash flow statement's closing cash)", text)
        self.assert_sentence(text, r"Each is zero in every month")
        self.assert_sentence(text, r"non-zero result is a broken model",
                             DO_NOT + r"hand the forecast over until it is zero")
        self.assertIn("`check_balance` and `check_cash` are zero in every month",
                      section("financial-modelling", "Checks before handing over"))

    def test_three_way_forecast_links_working_capital_tax_and_loans(self) -> None:
        text = section("financial-modelling", "Three-way forecast")
        self.assert_sentence(text, r"debtor days and creditor days drivers on the Assumptions sheet")
        self.assert_sentence(text, r"GST, PAYG withholding, super and income tax",
                             r"due date verified at a primary source")
        self.assert_sentence(text, r"cannot be verified stays `UNVERIFIED`", r"payment month stays blank")
        self.assert_sentence(text, r"opening balance tied to the lender's statement")
        self.assert_sentence(text, r"weekly cash view to `cashflow-forecast-13week`")
        self.assert_sentence(text, r"predicts nothing and recommends nothing")

    def test_three_way_card_fails_check_balance_on_the_opening_position(self) -> None:
        text = " ".join(card_text("financial-modelling-three-way").split())
        # The build stops at the opening position, so the check is on the opening balance sheet, not a first month.
        self.assertIn("so the opening balance sheet's `check_balance` is 35000.00 - 10000.00 - 24000.00 = 1000.00, not zero", text)
        self.assertNotIn("first month", text)
        self.assertIn("do not plug the difference to equity, cash or a suspense line", text)
        self.assertIn("Do not hand over a forecast with a non-zero `check_balance` or `check_cash`", text)
        self.assertIn("Do not predict whether the business can afford the hire", text)


if __name__ == "__main__":
    unittest.main()
