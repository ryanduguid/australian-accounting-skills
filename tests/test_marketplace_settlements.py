# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The marketplace settlements workflow added on 12 November 2026 keeps its tie-out and GST limits.

Each test reads one workflow step or section and checks the rule a reader could get
wrong: components sum to the payout in exact cents, nothing is plugged, fee GST comes
only from a document, platform-collected tax stays apart and is routed rather than
classified, and no platform's column names are assumed. It checks wording, not model
behaviour. The helpers are in skill_prose.py.
"""

from __future__ import annotations

import re
import unittest

from skill_prose import (
    DO_NOT,
    PENDING,
    PENDING_FACT,
    SKILLS,
    affirms,
    records,
    section,
    sentences,
    skill_text,
    workflow_step,
)

SKILL = "marketplace-settlements"
GST_ACT = "https://www.legislation.gov.au/C2004A00446/latest/text"
NON_RESIDENT = "https://www.ato.gov.au/businesses-and-organisations/international-tax-for-business/gst-for-non-resident-businesses"
EDP = f"{NON_RESIDENT}/how-to-charge-gst/if-you-are-an-edp-operator"
LOW_VALUE = f"{NON_RESIDENT}/gst-on-low-value-imported-goods"
CARDS = SKILLS.parents[1] / "validation" / "cases"


class MarketplaceSettlementTests(unittest.TestCase):
    def assert_sentence(self, text: str, *patterns: str, affirmed: tuple[str, ...] = ()) -> None:
        """One sentence of `text` matches every pattern, and each `affirmed` pattern unnegated."""
        with self.subTest(patterns=patterns, affirmed=affirmed):
            self.assertTrue(
                any(all(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)
                    and all(affirms(sentence, pattern) for pattern in affirmed)
                    for sentence in sentences(text)),
                f"no sentence matches all of {patterns} with {affirmed} affirmed",
            )

    def assert_routes_to(self, text: str, *routes: str) -> None:
        for route in routes:
            with self.subTest(route=route):
                self.assertIn(f"`{route}`", text)
                self.assertTrue((SKILLS / route / "SKILL.md").is_file())

    def test_report_columns_are_mapped_from_the_platforms_own_definitions(self) -> None:
        step = workflow_step(SKILL, 2)
        self.assert_sentence(step, r"\bplatform's own documentation\b", r"\bask the person who supplied the report\b")
        self.assert_sentence(step, DO_NOT + r"assume a column's meaning from its heading or from memory of a platform\b")
        self.assert_sentence(step, r"\bnot confirmed\b", r"\bopen item\b", r"\bstays unreconciled\b")
        # The skill is generic: it names no platform and no report heading of its own.
        self.assertNotRegex(skill_text(SKILL), r"\b(?:Amazon|eBay|Etsy|Shopify|Stripe|PayPal|Square|Afterpay)\b")

    def test_each_settlement_sums_to_its_payout_in_exact_cents(self) -> None:
        step = workflow_step(SKILL, 3)
        self.assert_sentence(step, r"\bgross sales less refunds\b", r"\breserves held\b", r"\breserves released\b",
                             r"\bmust equal the payout the report states, to the cent\b")
        self.assert_sentence(step, DO_NOT + r"net a fee into a sale, a refund into the original sale or a reserve "
                             r"release into a reserve held\b")
        self.assert_sentence(step, r"\brefund in a later settlement than its sale\b",
                             r"\bstays in the settlement that carries it\b", r"`bas-preparation`")

    def test_no_difference_is_plugged(self) -> None:
        self.assert_sentence(workflow_step(SKILL, 3), DO_NOT + r"plug, round or net a figure to make a settlement tie\b",
                             affirmed=(r"\blist the difference as an open item\b",))
        self.assert_sentence(workflow_step(SKILL, 4), r"\bexact amount\b", r"\bdate on or after the report's payout date\b")
        self.assert_sentence(workflow_step(SKILL, 4), DO_NOT + r"adjust the payout or the bank figure to agree\b")
        clearing = workflow_step(SKILL, 5)
        self.assert_sentence(clearing, r"\bsales not yet in a paid settlement and reserves still held\b",
                             r"\bthe unsettled items the reports themselves show\b")
        self.assert_sentence(clearing, DO_NOT + r"post it to suspense, fees or sales to clear it\b")
        self.assert_sentence(section(SKILL, "Hand-off and checks"), r"\bNo difference is plugged, netted or posted to suspense\b")

    def test_sales_recorded_net_of_fees_are_raised_and_rebuilt_gross(self) -> None:
        step = workflow_step(SKILL, 6)
        self.assert_sentence(step, r"\bnet of fees as sales\b", affirmed=(r"\braise it as an exception\b",
                                                                        r"\brebuild the gross sales and the fees from the report\b"))

    def test_fee_gst_is_taken_only_from_a_document(self) -> None:
        step = workflow_step(SKILL, 7)
        self.assert_sentence(step, r"\bGST on the platform's fees\b",
                             r"\btake it only from the platform's tax invoice for the fees or from the report's own tax column\b")
        self.assert_sentence(step, DO_NOT + r"compute it from a rate or by dividing a fee\b")
        self.assert_sentence(step, r"\bWhere neither shows it\b", r"\bleave it blank\b")
        self.assert_routes_to(step, "tax-invoice-review", "bas-preparation")

    def test_platform_collected_tax_is_kept_apart_and_routed_not_classified(self) -> None:
        step = workflow_step(SKILL, 7)
        self.assert_sentence(step, r"\b3 GST classes apart\b", r"\bdecide none\b")
        self.assert_sentence(step, r"\bA report's marking is a lead, not a classification\b",
                             DO_NOT + r"decide who made the supply or whether it is taxable\b",
                             r"\bdo not move the tax into sales, GST payable or fees\b")
        self.assert_sentence(step, r"\bRoute each lead to the registered agent through `bas-preparation`")
        # Each Division 84 section is named with its Act, and no threshold figure is stated.
        for section_number in ("84-55", "84-60", "84-81(3)", "84-79(3)", "84-70(2)"):
            with self.subTest(section=section_number):
                self.assertRegex(step, rf"\b[Ss](?:ection)? {re.escape(section_number)} of the GST Act\b")
        self.assert_sentence(step, r"\bdoes not apply the low value goods limit in s 84-79\(3\) of the GST Act\b",
                             r"\breads it at the source for the period\b")
        self.assertNotRegex(skill_text(SKILL), r"\$\s?\d|\bA\$")
        self.assert_sentence(step, r"\bAgent read on 12 November 2026, human review pending\b", r"\bcompilation 96\b")

    def test_foreign_currency_keeps_the_shown_rate_and_routes_conversion(self) -> None:
        step = workflow_step(SKILL, 8)
        self.assert_sentence(step, r"\bthe conversion rate the report or the bank shows\b")
        self.assert_sentence(step, DO_NOT + r"supply a rate\b")
        self.assert_routes_to(step, "au-forex-review")

    def test_neighbouring_work_is_routed_not_repeated(self) -> None:
        self.assert_routes_to(workflow_step(SKILL, 1), "au-short-stay-accommodation", "statement-to-csv")
        self.assert_routes_to(workflow_step(SKILL, 4), "reconciliation-break-trace", "month-end-close")
        self.assert_routes_to(workflow_step(SKILL, 9), "year-end-workpapers", "au-sole-trader")

    def test_sources_are_cited_and_pending(self) -> None:
        text = skill_text(SKILL)
        indexed = records(SKILL)
        self.assertEqual(set(indexed), {GST_ACT, EDP, LOW_VALUE})
        for url, record in indexed.items():
            with self.subTest(url=url):
                self.assertIn(f"]({url})", text)
                self.assertEqual(record["verification_status"], PENDING)
                self.assertEqual(record["checked_at"], "")
                self.assertEqual(record["fact"], PENDING_FACT)
                self.assertEqual(record["review_required_since"], "2026-11-12")

    def test_fault_card_lists_each_planted_fault_as_an_open_item(self) -> None:
        card = (CARDS / "marketplace-settlements-planted-faults.md").read_text(encoding="utf-8")
        checks = " ".join(card.split("## Required checks", 1)[1].split("## Must not do", 1)[0].split())
        for fault in (r"\b50\.00 difference\b.*\bopen item\b", r"\bsales recorded net of fees as an exception\b",
                      r"\b300\.00 reserve still held\b", r"\brefund to its settlement T1 order\b",
                      r"\bleave settlement T1's fee GST blank\b"):
            with self.subTest(fault=fault):
                self.assertRegex(checks, fault)


if __name__ == "__main__":
    unittest.main()
