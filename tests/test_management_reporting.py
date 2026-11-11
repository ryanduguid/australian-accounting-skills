# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The accounting depreciation schedule and the monthly management report keep their limits.

`au-depreciation-schedule` step 8a works only from the entity's documented accounting
policy, leaves a class blank and `UNVERIFIED` where the policy is silent, never borrows
tax lives and ties to the trial balance. `month-end-close` step 9 reports from figures
tied to the close, states each ratio's formula, supplies no benchmark, keeps unexplained
variances open and frames actions as options. It checks wording, not model behaviour.
The helpers are in skill_prose.py.
"""

from __future__ import annotations

import re
import unittest

from skill_prose import (
    DO_NOT,
    ISO_DATE,
    PENDING,
    PENDING_FACT,
    affirms,
    records,
    section,
    sentences,
    skill_text,
    workflow_step,
)

AASB_116 = "https://standards.aasb.gov.au/aasb-116-dec-2022"


class ManagementReportingTests(unittest.TestCase):
    def assert_sentence(self, text: str, *patterns: str, affirmed: tuple[str, ...] = ()) -> None:
        """One sentence of `text` matches every pattern, and each `affirmed` pattern unnegated."""
        with self.subTest(patterns=patterns, affirmed=affirmed):
            self.assertTrue(
                any(all(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)
                    and all(affirms(sentence, pattern) for pattern in affirmed)
                    for sentence in sentences(text)),
                f"no sentence matches all of {patterns} with {affirmed} affirmed",
            )

    # au-depreciation-schedule: step 8a

    def test_accounting_schedule_works_from_the_documented_policy(self) -> None:
        step = workflow_step("au-depreciation-schedule", "8a")
        self.assert_sentence(step, r"\bonly from the entity's documented accounting policy\b")
        # The policy is an input, so the step is reachable from what the skill asks for.
        self.assertIn("documented accounting policy for property, plant and equipment",
                      section("au-depreciation-schedule", "Inputs"))

    def test_a_missing_policy_item_leaves_the_class_blank(self) -> None:
        step = workflow_step("au-depreciation-schedule", "8a")
        self.assert_sentence(step, r"\bwhere the policy gives no useful life or rate, method or residual value\b",
                             r"\bblank and `UNVERIFIED`", r"\bmissing policy item\b",
                             affirmed=(r"leave that class's depreciation",))

    def test_tax_lives_are_never_adopted_without_a_recorded_policy(self) -> None:
        step = workflow_step("au-depreciation-schedule", "8a")
        self.assert_sentence(step, DO_NOT + r"adopt a tax effective life\b", r"\bunless the recorded policy adopts it\b")
        self.assertIn("never from the tax schedule", section("au-depreciation-schedule", "Hand-off and checks"))

    def test_accounting_schedule_ties_to_the_trial_balance_and_keeps_differences_open(self) -> None:
        step = workflow_step("au-depreciation-schedule", "8a")
        self.assert_sentence(step, r"\btie closing cost, closing accumulated depreciation and the period's depreciation expense to the trial balance\b")
        self.assert_sentence(step, r"\bwhere a class does not tie\b", DO_NOT + r"adjust the schedule to force the tie\b",
                             r"\bopen item with evidence needed, owner and next action\b")
        self.assert_sentence(step, r"\binto step 8\b")

    def test_aasb_116_paragraphs_name_the_standard_and_the_source_is_indexed(self) -> None:
        step = workflow_step("au-depreciation-schedule", "8a")
        cited = [sentence for sentence in sentences(step) if re.search(r"\bparagraphs?\s+\d", sentence)]
        self.assertTrue(cited, "step 8a cites no AASB 116 paragraph")
        for sentence in cited:
            with self.subTest(sentence=sentence[:60]):
                self.assertIn("AASB 116", sentence)
        self.assertIn("**Human review pending:** an agent read on 12 November 2026", step)
        self.assertIn(f"]({AASB_116})", skill_text("au-depreciation-schedule"))
        record = records("au-depreciation-schedule")[AASB_116]
        self.assertEqual(record["verification_status"], PENDING)
        self.assertEqual(record["checked_at"], "")
        self.assertEqual(record["fact"], PENDING_FACT)
        self.assertRegex(str(record["review_required_since"]), ISO_DATE)

    # month-end-close: step 9

    def test_management_report_ties_to_the_closed_trial_balance(self) -> None:
        step = workflow_step("month-end-close", 9)
        self.assert_sentence(step, r"\bafter step 8\b", r"`xero-exports`", r"\binput 13\b")
        self.assert_sentence(step, r"\btie each report's net profit and net assets to the closed trial balance\b",
                             r"\bwhere either does not tie, stop\b", r"\bopen exception\b")

    def test_each_ratio_states_its_formula(self) -> None:
        step = workflow_step("month-end-close", 9)
        for ratio in ("gross margin (gross profit / revenue)", "net margin (net profit / revenue)",
                      "current ratio (current assets / current liabilities)",
                      "debtor days (trade debtors / revenue for the period x days in the period)",
                      "creditor days (trade creditors / purchases or cost of sales for the period x days in the period, naming which)",
                      "wages to revenue (wages and salaries / revenue)"):
            with self.subTest(ratio=ratio):
                self.assertIn(ratio, step)
        self.assert_sentence(step, r"\beach ratio beside its formula\b", r"\bonly to the entity's own figures\b")

    def test_no_benchmark_is_supplied(self) -> None:
        step = workflow_step("month-end-close", 9)
        self.assert_sentence(step, DO_NOT + r"compare a ratio with an industry figure or benchmark supplied from memory or by this skill\b",
                             r"\bonly with the entity's own budget and prior periods\b",
                             r"\ba benchmark the owner supplies with its source\b")

    def test_unexplained_variances_stay_open_in_the_report(self) -> None:
        step = workflow_step("month-end-close", 9)
        self.assert_sentence(step, r"\bcomment only on movements step 5 explained\b",
                             r"\bstill unexplained appears in the report as open\b",
                             r"\bnever with a reason supplied to fill the gap\b")
        self.assertIn("every unexplained variance appears in it as open",
                      section("month-end-close", "Checks before handing over"))

    def test_actions_are_options_and_questions_never_recommendations(self) -> None:
        step = workflow_step("month-end-close", 9)
        self.assert_sentence(step, r"\boptions and questions for the owner\b", r"`cashflow-forecast-13week`",
                             r"\bnever as recommendations\b")
        self.assert_sentence(step, r"\bnot a set of financial statements or an assurance conclusion\b",
                             r"\ban authorised human decides whether it is sent\b")

    def test_descriptions_name_the_new_outputs(self) -> None:
        for skill, phrase in (("au-depreciation-schedule", "tax or accounting depreciation schedule"),
                              ("month-end-close", "monthly management report")):
            with self.subTest(skill=skill):
                front_matter = skill_text(skill).split("---", 2)[1]
                self.assertIn(phrase, front_matter)


if __name__ == "__main__":
    unittest.main()
