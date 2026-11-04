# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""A skill's worked example must be fabricated, rate-free and add up."""

from __future__ import annotations

import re
import unittest
from decimal import Decimal
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[1] / ".claude" / "skills"

WORKED = (
    "au-bookkeeping", "au-financial-statements", "au-managed-fund-amit", "au-payroll-review",
    "au-rental-property", "au-sapto", "cashflow-forecast-13week", "contract-cost-tracking",
    "month-end-close", "progress-claim-preparation", "reconciliation-break-trace",
    "retention-schedule", "wip-over-under-billing", "workpaper-tie-out", "year-end-workpapers",
)

NUMBER = r"-?\d[\d,]*(?:\.\d+)?"
EQUATION = re.compile(rf"({NUMBER}(?: [-+x/] {NUMBER})+) = ({NUMBER})")


def worked_example(skill: str) -> str:
    text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"^## Worked example\n(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL)
    assert match, f"{skill} has no worked example"
    return match.group(1)


def number(text: str) -> Decimal:
    return Decimal(text.replace(",", ""))


def evaluate(expression: str) -> Decimal:
    """Left to right: each example uses only + and -, or a single x or /."""
    tokens = expression.split(" ")
    total = number(tokens[0])
    for operator, operand in zip(tokens[1::2], tokens[2::2], strict=True):
        value = number(operand)
        if operator == "+":
            total += value
        elif operator == "-":
            total -= value
        elif operator == "x":
            total *= value
        else:
            total /= value
    return total


class WorkedExampleTests(unittest.TestCase):
    def test_every_equation_adds_up(self) -> None:
        for skill in WORKED:
            equations = EQUATION.findall(worked_example(skill))
            with self.subTest(skill=skill):
                self.assertTrue(equations, "a worked example shows its working")
            for expression, result in equations:
                with self.subTest(skill=skill, expression=expression):
                    self.assertEqual(evaluate(expression), number(result))

    def test_examples_are_fabricated_and_state_no_rate(self) -> None:
        for skill in WORKED:
            example = worked_example(skill)
            with self.subTest(skill=skill):
                self.assertIn("Fabricated from scratch", example)
                self.assertIn("no figure here is a rate, threshold or benchmark", example)
                self.assertNotRegex(example, r"%|per\s?cent|\$\s?\d")

    def test_examples_leave_the_decision_with_a_person(self) -> None:
        reserved = re.compile(
            r"review|authorised|owner|project manager|unverified|verified", re.IGNORECASE
        )
        for skill in WORKED:
            with self.subTest(skill=skill):
                self.assertRegex(worked_example(skill).split("benchmark.", 1)[1], reserved)


if __name__ == "__main__":
    unittest.main()
