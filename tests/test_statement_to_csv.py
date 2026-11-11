# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""Regression gates for the statement-to-csv skill, its checker route and its card statement card."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILL = REPOSITORY / ".claude" / "skills" / "statement-to-csv" / "SKILL.md"
CHECKER = REPOSITORY / "tools" / "accounting-skills" / "src" / "statement_check.rs"
CARD = REPOSITORY / "validation" / "cases" / "statement-to-csv-card-in-credit-year-end.md"


def skill_text() -> str:
    return " ".join(SKILL.read_text(encoding="utf-8").split())


def step(start: str, end: str) -> str:
    text = skill_text()
    begin = text.index(start)
    return text[begin : text.index(end, begin)]


class StatementToCsvTests(unittest.TestCase):
    def test_signs_from_the_running_balance_need_an_exact_change(self) -> None:
        signs = step("3. **Normalise dates and signs.**", "4. **Tie out before building the file.**")
        self.assertIn("Where a line's sign comes only from the running balance", signs)
        self.assertIn(
            "differs from the printed balance on the line before by exactly the amount, "
            "and take the sign from the direction of that change",
            signs,
        )
        self.assertIn("never because a sign makes the totals tie", signs)

    def test_card_balances_keep_the_owed_direction_and_the_balance_field(self) -> None:
        signs = step("3. **Normalise dates and signs.**", "4. **Tie out before building the file.**")
        self.assertIn("a balance in credit is a negative amount owed", signs)
        self.assertIn("a balance can cross zero within a period", signs)
        self.assertIn("never from available credit, the credit limit or the minimum payment", signs)
        self.assertIn("is not out of period on that ground alone", signs)
        self.assertIn("infer the year across a year end from the statement period", signs)

    def test_manual_tie_outs_follow_the_account_direction(self) -> None:
        tie_out = step("4. **Tie out before building the file.**", "5. **Resolve overlaps")
        self.assertIn("plus credits less debits must equal the carried-forward balance for a deposit account", tie_out)
        self.assertIn("the brought-forward balance plus debits less credits must equal it", tie_out)
        inventory = step("1. **Inventory and sequence the statements.**", "2. **Extract one row")
        self.assertIn("after its last line posted before the later statement's period starts", inventory)
        self.assertIn("Use posting (processing) dates, not transaction dates", inventory)
        self.assertIn("the overlap cannot be placed; flag it", inventory)

    def test_gross_totals_catch_omissions_that_cancel(self) -> None:
        tie_out = step("4. **Tie out before building the file.**", "5. **Resolve overlaps")
        self.assertIn(
            "the extracted gross credits and gross debits must each equal them", tie_out
        )
        self.assertIn("an omitted credit and an omitted debit cancel", tie_out)
        self.assertIn("A statement that prints movement but yields no extracted lines fails.", tie_out)

    def test_the_checker_does_the_arithmetic_when_installed(self) -> None:
        tie_out = step("4. **Tie out before building the file.**", "5. **Resolve overlaps")
        for contract in (
            "Do this arithmetic with `accounting-skills statement-check`",
            "by printing `usage: accounting-skills statement-check FILE`",
            "Otherwise record the checker as not run, tie out by hand",
            "`cargo install --locked --path tools/accounting-skills`",
            "Do not install it yourself, and do not describe what it would have found.",
            "Leave every description out",
            "quote its output unchanged in the workpaper",
            "- `0`: every check passed.",
            "a pass that compared no printed totals cannot detect omissions that cancel",
            "- `2`: each `BREAK` line names a statement, page and line",
            "except that with `owed` a line may be dated up to 31 days early",
            "without surrounding spaces",
            "Reread only the pages the lines name.",
            "except those whose own printed total for that side was compared and tied",
            "For a closing-balance break, reread every page whose carried-forward balance was not "
            "compared, and the closing figure.",
            "a posting date outside the statement's period breaks",
            "each `OVERLAP` line names 2 statements whose periods overlap",
            "its one total, or its parts",
            "references must be present and unique",
            "- `1` or any other code: the run failed",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, tie_out)

    def test_a_period_break_is_explained_but_left_open(self) -> None:
        tie_out = step("4. **Tie out before building the file.**", "5. **Resolve overlaps")
        for contract in (
            "a period break can flag a line the statement legitimately prints; no such statement has "
            "been confirmed.",
            "For a period break, compare the date the `BREAK` line names, the line's `date` or its "
            "`posted` date, with the period the statement itself prints "
            "and with any posting cutoff the issuer states, record the explanation and the evidence for "
            "it in the workpaper, and leave the break open for a person.",
            "Never widen `period_start` or `period_end` beyond the printed period to make a line pass.",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, tie_out)
        tool = " ".join((REPOSITORY / "tools" / "accounting-skills" / "README.md").read_text(encoding="utf-8").split())
        self.assertIn("The period check can flag a line the issuer legitimately placed on the statement", tool)
        self.assertIn("never passes a line whose `posted` date falls outside the period.", tool)

    def test_the_documented_input_fields_are_the_checkers(self) -> None:
        """Every field the skill names must be one the checker accepts, and the reverse."""
        tie_out = step("Its input is one JSON file per account", "Amounts are plain decimals")
        values = {"deposit", "owed", "column"}
        documented = set(re.findall(r"`([a-z_]+)`", tie_out)) - values
        source = CHECKER.read_text(encoding="utf-8")
        accepted = {
            name
            for body in re.findall(r"#\[serde\(deny_unknown_fields\)\]\s*struct \w+ \{(.*?)\}", source, re.S)
            for name in re.findall(r"^\s*([a-z_]+):", body, re.M)
        }
        self.assertEqual(documented, accepted)
        self.assertIn("usage: accounting-skills statement-check FILE", source)

    def test_release_notes_describe_the_checker(self) -> None:
        notes = (REPOSITORY / "RELEASE_NOTES.md").read_text(encoding="utf-8")
        notes = " ".join(notes[: notes.index("# v0.5.0\n")].split())
        for contract in (
            "`accounting-skills statement-check` exits 0 when everything ties, 2 on any break",
            "and 1 on malformed input",
            "an empty input, a repeated statement id or a missing or repeated reference",
            "an `OVERLAP` line",
            "a statement period wholly within another",
            "a line posted outside its period",
            "a line dated outside it, with 31 days' allowance before the period for",
            "The `PASS` line counts the printed balances, printed totals and statement links",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, notes)

    def test_xero_row_limit_and_date_prompt_are_dated(self) -> None:
        target = step("8. **Verify the target format at use time.**", "9. **Hand the import")
        self.assertIn("Xero Central's CSV article, read on 11 November 2026", target)
        self.assertIn("a leading minus sign or brackets", target)
        self.assertIn("a CSV file with more than 100,000 rows cannot be imported", target)
        self.assertIn("applies the choice to the entire statement and all future CSV bank statements", target)
        self.assertIn("'could be either DD/MM/YY, MM/DD/YY or YY/MM/DD'", target)
        self.assertIn("tell the person to choose that format if Xero asks", target)
        self.assertNotIn("within a stated row limit", target)

    def test_the_card_statement_card_exercises_each_rule(self) -> None:
        card = CARD.read_text(encoding="utf-8")
        self.assertIn("  - statement-to-csv\n", card)
        for contract in (
            "'Opening balance 35.00 CR'",
            "'Available credit 3845.50'",
            "15 December of year Y1 to 14 January of year Y2",
            "printed new debits of 251.50 and new credits of 62.00 by 12.00 each",
            "a change equal to its 50.00 amount",
            "not the 3845.50 available credit",
            "without flagging it as out of period on that ground alone",
            "Do not accept the draft as complete because its net movement and running balances tie.",
        ):
            with self.subTest(contract=contract):
                self.assertIn(contract, card)


if __name__ == "__main__":
    unittest.main()
