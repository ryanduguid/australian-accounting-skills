# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: Apache-2.0
"""The pre-sign-off QA matrix for completed company and trust tax returns.

`au-company-tax` step 5 and `au-trust-distributions` step 6 compare each figure
across its sources and give every row one of 4 fixed states, under a stated
tolerance, without changing a figure to clear a row. Each matrix row names the
return label and the rule it tests. The tests check wording, not model
behaviour. The helpers are in skill_prose.py.
"""

from __future__ import annotations

import re
import unittest

from skill_prose import DO_NOT, PENDING, affirms, records, sentences, table_row, workflow_step

QA_STEPS = (("au-company-tax", 5), ("au-trust-distributions", 6))
STATES = r"`agrees`.*`differs`.*`one source only`.*`not found`"


class ReturnQaMatrixTests(unittest.TestCase):
    def assert_sentence(self, text: str, *patterns: str, affirmed: tuple[str, ...] = ()) -> None:
        """One sentence of `text` matches every pattern, and each `affirmed` pattern unnegated."""
        with self.subTest(patterns=patterns, affirmed=affirmed):
            self.assertTrue(
                any(all(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)
                    and all(affirms(sentence, pattern) for pattern in affirmed)
                    for sentence in sentences(text)),
                f"no sentence matches all of {patterns} with {affirmed} affirmed",
            )

    def row(self, skill: str, check: str) -> str:
        return " ".join(table_row(skill, "Return QA matrix", check))

    def test_each_review_gives_every_row_one_fixed_state(self) -> None:
        for skill, number in QA_STEPS:
            with self.subTest(skill=skill):
                step = workflow_step(skill, number)
                self.assert_sentence(step, r"\bexactly one state\b", STATES)
                self.assert_sentence(step, r"\btolerance is under AUD 1\b", r"\bwhole figures or no cents\b",
                                     r"\bonly to the cents dropped\b")
                self.assert_sentence(step, r"\bevery other difference, however small, is `differs`")
                self.assert_sentence(step, r"`differs` \(any 2 sources disagree beyond the tolerance, even where others agree\)")
                self.assert_sentence(step, r"\bcompare the unrounded amounts first\b", r"\brounding bridge\b",
                                     r"\bnever widening the tolerance\b")
                self.assert_sentence(step, r"\bsame basis\b", r"\btrust-law income are different figures\b")
                self.assert_sentence(step, DO_NOT + r"change a figure to clear a row\b", r"\bopen item\b")
                self.assert_sentence(step, r"\bnot performed\b", r"\brather than mapping it from this table\b")
                self.assert_sentence(step, r"\bnot a finding that the return is correct\b", r"\bno assurance\b")
                self.assert_sentence(step, r"\b24 November 2026\b", r"\bHuman review pending\b")

    def test_company_matrix_tests_the_base_rate_entity_label_against_the_act(self) -> None:
        row = self.row("au-company-tax", "Base rate entity")
        self.assert_sentence(row, r"\bs 23AA of the \*Income Tax Rates Act 1986\*", r"\bno more than 80%",
                             r"\bless than AUD 50 million\b", affirmed=(r"\bis a base rate entity\b",))
        self.assert_sentence(row, r"\bdenominator is assessable income, not accounting revenue\b")
        self.assert_sentence(row, r"\bs 23AB\(2\)", r"\bleave the exclusion to the reviewer\b", r"\bnever applying it yourself\b")
        self.assert_sentence(row, r"\bpercentage\b")
        self.assert_sentence(row, r"\binput is missing\b", r"`not found`", r"\bF2 stays `UNVERIFIED`")

    def test_company_matrix_ties_label_n_and_leaves_deemed_dividends_to_div7a(self) -> None:
        row = self.row("au-company-tax", "Division 7A loans")
        self.assert_sentence(row, r"\bwhole figures\b", r"\bdebit balance at the end of the year\b",
                             r"\bnatural person, partnership or trust\b",
                             r"\bcode A \(all loans made on or after 4 December 1997\)", r"\bprivate company or closely held\b")
        self.assert_sentence(row, r"\bs 109D\(1\) of the ITAA 1936\b", r"`div7a-compliance`",
                             DO_NOT + r"conclude\b")

    def test_company_matrix_rolls_the_franking_account_between_labels_p_and_m(self) -> None:
        row = self.row("au-company-tax", "Franking account")
        self.assert_sentence(row, r"\bblank\b", r"\bdeficit\b", r"\bfranking account tax return\b")
        self.assert_sentence(row, r"\bOpening plus credits less debits must equal the closing balance\b")
        self.assertIn("labels P Opening franking account balance and M Closing franking account balance", row)
        for check in ("Profit", "Taxable income", "Dividends paid", "PAYG instalments", "Losses", "Balance sheet"):
            with self.subTest(check=check):
                self.assertTrue(self.row("au-company-tax", check))

    def test_trust_matrix_flags_benefit_to_another_for_section_100a_review(self) -> None:
        row = self.row("au-trust-distributions", "Benefit of entitlements")
        self.assert_sentence(row, r"\bsomeone other than the beneficiary\b", r"`differs`", r"\bstep 4b\b",
                             r"\bs 100A\(1\) of the ITAA 1936\b", r"\bs 100A\(13\) of the ITAA 1936\b",
                             r"\bordinary family or commercial dealing\b")
        self.assert_sentence(row, r"\bspecialist decision\b")
        self.assert_sentence(row, r"\bas a fact to investigate, never as evidence that a reimbursement agreement exists\b")

    def test_trust_matrix_ties_shares_to_trust_income_and_keeps_tfns_out(self) -> None:
        self.assertIn("item 57 label A", self.row("au-trust-distributions", "Beneficiary shares"))
        self.assert_sentence(self.row("au-trust-distributions", "Trust income"), r"\bloss is shown as 0\b")
        self.assert_sentence(self.row("au-trust-distributions", "Beneficiary details"), r"\bnever the TFN itself\b")
        self.assert_sentence(self.row("au-trust-distributions", "No beneficiary presently entitled"),
                             r"\bnever assume the Commissioner's discretion\b")
        self.assert_sentence(self.row("au-trust-distributions", "No beneficiary presently entitled"),
                             r"\bs 99A\(2\) of the ITAA 1936\b", r"\bwill, codicil, intestacy\b", r"\bbankrupt\b",
                             r"\bs 99A\(3\) of the ITAA 1936\b")
        self.assert_sentence(self.row("au-trust-distributions", "Beneficiary shares"), r"\bnever use it to reconcile net income\b")
        self.assert_sentence(self.row("au-trust-distributions", "Net income"), r"\bseparately from label W\b", r"\bnot forced to agree\b")
        self.assert_sentence(self.row("au-trust-distributions", "Assessment calculation code"), r"\bnever infer one from a name\b")
        self.assert_sentence(self.row("au-trust-distributions", "Losses"),
                             r"\bexceed the total the instructions state\b", r"\bmust equal item 27 label U\b")
        for check in ("Net income", "Unpaid entitlements", "Elections", "Balance sheet"):
            with self.subTest(check=check):
                self.assertTrue(self.row("au-trust-distributions", check))

    def test_sources_read_today_are_indexed_as_pending_human_review(self) -> None:
        expected = {
            "au-company-tax": (
                "https://www.ato.gov.au/forms-and-instructions/company-tax-return-2026-instructions",
                "https://www.legislation.gov.au/C2004A03348/latest/text",
                "https://www.legislation.gov.au/C1936A00027/latest/text",
            ),
            "au-trust-distributions": ("https://www.ato.gov.au/forms-and-instructions/trust-tax-return-2026-instructions",),
        }
        for skill, urls in expected.items():
            sources = records(skill)
            for url in urls:
                with self.subTest(skill=skill, url=url):
                    self.assertIn(url, sources)
                    if "2026-instructions" in url or "C2004A03348" in url:
                        self.assertEqual(sources[url]["verification_status"], PENDING)
                        self.assertEqual(sources[url]["review_required_since"], "2026-11-24")


if __name__ == "__main__":
    unittest.main()
