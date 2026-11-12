# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""A skill's worked example must be fabricated, rate-free and add up.

A validation card's working must add up too.
"""

from __future__ import annotations

import re
import unittest
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS = REPOSITORY / ".claude" / "skills"
CARDS = REPOSITORY / "validation" / "cases"

WORKED = (
    "au-ato-account-reconciliation", "au-bookkeeping", "au-financial-statements",
    "au-franking-account", "au-managed-fund-amit", "au-payroll-review", "au-rental-property",
    "au-sapto", "au-trust-distributions", "bas-preparation", "cashflow-forecast-13week",
    "contract-cost-tracking", "month-end-close", "progress-claim-preparation",
    "reconciliation-break-trace", "retention-schedule", "stp-finalisation",
    "wip-over-under-billing", "workpaper-tie-out", "year-end-workpapers",
)

NUMBER = r"-?\d[\d,]*(?:\.\d+)?"
EQUATION = re.compile(rf"({NUMBER}(?: [-+x/] {NUMBER})+) = ({NUMBER})")
# A card may state a ratio as a percentage: 18000.00 / 24000.00 = 75 per cent.
CARD_EQUATION = re.compile(rf"{EQUATION.pattern}( per cent)?")


def worked_example(skill: str) -> str:
    text = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"^## Worked example\n(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL)
    assert match, f"{skill} has no worked example"
    return match.group(1)


def number(text: str) -> Decimal:
    return Decimal(text.replace(",", ""))


def evaluate(expression: str) -> Decimal:
    """Left to right, so an expression may use + and - or x and /, never both kinds."""
    tokens = expression.split(" ")
    operators = set(tokens[1::2])
    if operators & {"+", "-"} and operators & {"x", "/"}:
        raise ValueError(f"{expression} mixes + or - with x or /; left to right ignores precedence")
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


def card_equations(card: Path) -> list[tuple[str, str, str]]:
    """A card wraps its prose, so an equation can span lines."""
    return CARD_EQUATION.findall(" ".join(card.read_text(encoding="utf-8").split()))


def foots(expression: str, result: str, per_cent: str) -> bool:
    """Compare at the precision the card states: 1000000.00 x 181 / 365 = 495890.41."""
    value = evaluate(expression) * (100 if per_cent else 1)
    stated = number(result)
    return value.quantize(stated, rounding=ROUND_HALF_UP) == stated


class ValidationCardArithmeticTests(unittest.TestCase):
    def test_every_card_equation_adds_up(self) -> None:
        checked = 0
        for card in sorted(CARDS.glob("*.md")):
            equations = card_equations(card)
            checked += bool(equations)
            for expression, result, per_cent in equations:
                with self.subTest(card=card.stem, expression=expression):
                    stated = f"{expression} = {result}{per_cent}"
                    self.assertTrue(foots(expression, result, per_cent), stated)
        self.assertTrue(checked, "no card equation was found, so nothing was recomputed")

    def test_mixed_precedence_is_refused_not_misread(self) -> None:
        with self.assertRaises(ValueError):
            evaluate("2.00 + 3.00 x 4.00")


if __name__ == "__main__":
    unittest.main()
