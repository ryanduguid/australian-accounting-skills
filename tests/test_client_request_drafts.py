# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The client request drafts added on 12 November 2026 ask for facts and are never sent.

Each draft asks the client for facts or records, is prepared for the practitioner
to review and send, is marked drafted and not sent, and states no tax treatment,
rate, threshold or due date. Each test reads the step that builds a draft and
checks those limits, then the rule specific to that draft. It checks wording, not
model behaviour. The helpers are in skill_prose.py.
"""

from __future__ import annotations

import re
import unittest

from skill_prose import DO_NOT, affirms, section, sentences, workflow_step

# The step that builds each draft.
DRAFT_STEPS = (
    ("au-crypto-tax", 0),
    ("bas-preparation", 6),
    ("au-bookkeeping", "3a"),
    ("year-end-workpapers", 0),
    ("au-individual-return", 1),
)
NO_TREATMENT = r"\bstates? no (?:GST or other )?tax treatment, position, conclusion or advice, and no rate, threshold or due date\b"


class ClientRequestDraftTests(unittest.TestCase):
    def assert_sentence(self, text: str, *patterns: str, affirmed: tuple[str, ...] = ()) -> None:
        """One sentence of `text` matches every pattern, and each `affirmed` pattern unnegated."""
        with self.subTest(patterns=patterns, affirmed=affirmed):
            self.assertTrue(
                any(all(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)
                    and all(affirms(sentence, pattern) for pattern in affirmed)
                    for sentence in sentences(text)),
                f"no sentence matches all of {patterns} with {affirmed} affirmed",
            )

    def test_each_draft_asks_for_facts_states_no_treatment_and_is_not_sent(self) -> None:
        for skill, number in DRAFT_STEPS:
            with self.subTest(skill=skill):
                step = workflow_step(skill, number)
                self.assert_sentence(step, r"\basks? for facts and records only\b", NO_TREATMENT)
                self.assert_sentence(step, r"\bdrafted and not sent\b", r"\bthis skill never sends\b")

    # au-crypto-tax: row 25

    def test_crypto_records_checklist_never_asks_for_keys_and_assumes_no_activity(self) -> None:
        step = workflow_step("au-crypto-tax", 0)
        self.assert_sentence(step, r"\bexchange or wallet\b", r"\bearliest acquisition\b", r"\bopening holdings\b",
                             r"\bfiat deposits and withdrawals\b")
        self.assert_sentence(step, r"\bstaking\b", r"\bairdrop\b", r"\bwrapping\b", r"\bbridge\b", r"\bNFT\b",
                             r"\bDeFi\b", DO_NOT + r"assume\b")
        self.assert_sentence(step, r"\bcover note\b")
        self.assert_sentence(step, DO_NOT + r"request private keys or seed phrases\b")
        self.assertIn("exchanges and wallets already known", section("au-crypto-tax", "Inputs"))
        self.assertIn("records checklist and cover note", section("au-crypto-tax", "Hand-off and checks"))

    # bas-preparation: row 45

    def test_bas_unexplained_movements_become_client_questions(self) -> None:
        step = workflow_step("bas-preparation", 6)
        self.assert_sentence(step, r"\bno supported explanation\b", r"\bone plain-words question\b",
                             r"\bdraft client question list\b")
        self.assert_sentence(step, r"\barea in words\b", r"\bthe period\b", r"\bthe movement\b",
                             r"\bthe record that would explain it\b")
        checks = section("bas-preparation", "Checks before handing over")
        self.assertIn("draft client question list, drafted and not sent", checks)

    # au-bookkeeping: row 46

    def test_bookkeeping_unknown_lines_get_queries_and_codes_stay_suggestions(self) -> None:
        step = workflow_step("au-bookkeeping", "3a")
        self.assert_sentence(step, r"\bpurpose, payee or evidence is unknown\b", r"\bdate, amount and statement text as printed\b")
        self.assert_sentence(step, r"\binvoice or receipt\b", r"\bbusiness and private split\b")
        self.assert_sentence(step, r"\bstays? a suggestion\b", r"\buntil the client's answer\b")
        self.assert_sentence(step, DO_NOT + r"post it\b")
        self.assertIn("draft client query list", section("au-bookkeeping", "Hand-off and checks"))

    # year-end-workpapers: rows 51 and 73

    def test_year_end_three_year_view_runs_only_with_two_prior_years(self) -> None:
        inputs = section("year-end-workpapers", "Inputs needed")
        self.assertIn("signed statements for the 2 prior years", inputs)
        step = workflow_step("year-end-workpapers", 5)
        self.assert_sentence(step, r"\b3-column P&L and balance sheet\b", r"\breverses\b", r"\bmateriality\b")
        self.assert_sentence(step, r"`div7a-compliance`")
        self.assert_sentence(step, r"\bstep 7\b", affirmed=(r"\bFeed each\b",))
        self.assert_sentence(step, r"\bonly one prior year\b", r"\b3-year view as `not run`")

    def test_year_end_records_request_starts_from_the_prior_year(self) -> None:
        step = workflow_step("year-end-workpapers", 0)
        self.assert_sentence(step, r"\bprior year workpaper pack and trial balance\b", r"\bbank and loan statements\b",
                             r"\baged listings\b", r"\bstock count\b", r"\badditions and disposals\b", r"\bpayroll\b")
        self.assert_sentence(step, r"\bnew\b", DO_NOT + r"assume\b")
        self.assert_sentence(step, r"\bcovering email\b")
        checks = section("year-end-workpapers", "Checks before handing over")
        self.assertIn("records request and covering email", checks)

    # au-individual-return: row 73

    def test_individual_return_adds_a_covering_email_and_keeps_the_firm_sending(self) -> None:
        step = workflow_step("au-individual-return", 1)
        self.assert_sentence(step, r"\bcovering email\b")
        self.assert_sentence(step, r"\bThe firm sends the request\b")


if __name__ == "__main__":
    unittest.main()
