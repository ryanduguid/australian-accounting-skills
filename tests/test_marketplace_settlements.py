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
        self.assert_sentence(step, r"\bplus or minus the platform-collected tax lines as the report shows them\b",
                             r"\bplus or minus a balance carried from another settlement\b")
        self.assert_sentence(step, r"\bWhere the result is negative\b", r"\bcarries to a later settlement\b",
                             r"\bdebits from the seller's bank or card\b")

    def test_a_carried_balance_stays_in_clearing_and_a_debit_can_match(self) -> None:
        self.assertIn("a balance carried from or to another settlement", workflow_step(SKILL, 2))
        self.assert_sentence(workflow_step(SKILL, 5), r"\bbalance carried between settlements stays in the clearing account\b",
                             DO_NOT + r"post it in either settlement\b")
        step = workflow_step(SKILL, 4)
        self.assert_sentence(step, r"\bnegative settlement\b", r"\bdebits from the seller's bank or card\b",
                             r"\bmatches a debit of that amount on that account\b")
        self.assert_sentence(step, r"\bcarries to a later settlement needs no bank line\b")
        self.assertIn("any bank or card statement the platform debits", section(SKILL, "Inputs"))

    def test_bank_tie_keeps_its_matching_limits(self) -> None:
        step = workflow_step(SKILL, 4)
        self.assert_sentence(step, r"\bEqual amounts alone do not establish a match where 2 payouts share an amount\b",
                             r"\buse the payout reference\b")
        self.assert_sentence(step, r"\bAccept one bank line for several payouts only where the report shows them combined\b")
        # A converted payout ties on the report's own amount, with the bank's conversion recorded as shown.
        self.assert_sentence(step, r"\bWhere the bank converts a payout from another currency\b",
                             r"\bpayout currency amount and reference the report shows\b",
                             r"\brecord the converted amount and the rate the bank shows under step 8\b")

    def test_no_difference_is_plugged(self) -> None:
        self.assert_sentence(workflow_step(SKILL, 3), DO_NOT + r"plug, round or net a figure to make a settlement tie\b",
                             affirmed=(r"\blist the difference as an open item\b",))
        self.assert_sentence(workflow_step(SKILL, 4), r"\bexact amount\b", r"\bdate on or after the report's payout date\b")
        self.assert_sentence(workflow_step(SKILL, 4), DO_NOT + r"adjust the payout or the bank figure to agree\b")
        clearing = workflow_step(SKILL, 5)
        self.assert_sentence(clearing, DO_NOT + r"post it to suspense, fees or sales to clear it\b")
        self.assert_sentence(clearing, r"\bA person approves and posts every entry\b")
        self.assert_sentence(section(SKILL, "Hand-off and checks"), r"\bNo difference is plugged, netted or posted to suspense\b")

    def test_period_end_balance_nets_every_unsettled_component(self) -> None:
        clearing = workflow_step(SKILL, 5)
        self.assert_sentence(clearing, r"\bthe net of every component the reports show as not yet in a paid settlement\b",
                             r"\bplus reserves still held\b",
                             r"\bplus payouts the reports show as paid that the bank had not received\b",
                             r"\bless any balance the reports show the seller owes the platform\b")
        self.assert_sentence(clearing, r"\bA payout leaves the clearing account on the report's payout date\b",
                             r"\bunless the firm records it when the bank receives it\b")
        self.assert_sentence(clearing, r"\bassumes the ledger records sales, refunds and fees when they occur\b",
                             r"\bsettlement-date policy\b", r"\bperson\b")
        self.assertNotRegex(clearing, r"\bsales not yet in a paid settlement and reserves still held\b")

    def test_sales_recorded_net_of_fees_are_raised_and_rebuilt_gross(self) -> None:
        step = workflow_step(SKILL, 6)
        self.assert_sentence(step, r"\bnet of fees as sales\b", affirmed=(r"\braise it as an exception\b",
                                                                        r"\brebuild the gross sales and the fees from the report\b"))

    def test_fee_gst_is_taken_only_from_a_document(self) -> None:
        step = workflow_step(SKILL, 7)
        self.assert_sentence(step, r"\bGST on the platform's fees\b",
                             r"\btake it only from the platform's tax invoice for the fees or from the report's own tax column\b")
        self.assert_sentence(step, DO_NOT + r"compute it from a rate or by dividing a fee\b")
        self.assert_sentence(step, r"\bWhere no such document is held\b", r"\bleave it blank and list the missing invoice\b")
        # A document that shows no GST, such as an offshore platform's invoice, is recorded as shown, not as missing.
        self.assert_sentence(step, r"\bdocument that shows no GST\b", r"\brecord it as the document shows\b",
                             r"\breverse-charge question\b", r"\bregistered agent\b")
        self.assert_sentence(step, r"\bseller's own GST on its sales\b", DO_NOT + r"compute or decide it\b")
        self.assert_routes_to(step, "tax-invoice-review", "bas-preparation")

    def test_platform_collected_tax_is_kept_apart_and_routed_not_classified(self) -> None:
        step = workflow_step(SKILL, 7)
        self.assert_sentence(step, r"\b3 GST classes apart\b", r"\bdecide none\b")
        self.assert_sentence(step, r"\bA report's marking is a lead, not a classification\b",
                             DO_NOT + r"decide who made the supply or whether it is taxable\b",
                             r"\bdo not move the tax into sales, GST payable or fees\b")
        self.assert_sentence(step, r"\bRoute each lead to the registered agent through `bas-preparation`")
        # s 84-55 is stated with its multiple-platform rule and its exception, s 84-60 with all its conditions.
        self.assert_sentence(step, r"\bs 84-55\(1\) of the GST Act\b")
        self.assert_sentence(step, r"\bs 84-55\(2\) of the GST Act\b", r"\bmore than one electronic distribution platform\b")
        self.assert_sentence(step, r"\bs 84-55\(4\) of the GST Act\b", r"\bdocument issued to the recipient\b",
                             r"\bagreed in writing that the supplier is responsible for paying the GST\b",
                             r"\bdoes not authorise the charge\b", r"\bthe delivery\b",
                             r"\bset any of the terms and conditions\b")
        self.assert_sentence(step, r"\bSection 84-60\(1\) of the GST Act\b",
                             r"\bthe agreement treats the supply as an inbound intangible consumer supply\b")
        self.assert_sentence(step, r"\bs 84-60\(2\) of the GST Act\b",
                             r"\bwould not be treated as the supplier under s 84-55 of the GST Act\b")
        self.assert_sentence(step, r"\bWhen an EDP operator isn't responsible for GST\b")
        # Each Division 84 section is named with its Act, and no threshold figure is stated.
        for section_number in ("84-55(1)", "84-55(2)", "84-55(4)", "84-60(1)", "84-60(2)", "84-81(3)", "84-79(3)",
                               "84-70(2)"):
            with self.subTest(section=section_number):
                self.assertRegex(step, rf"\b[Ss](?:ection)? {re.escape(section_number)} of the GST Act\b")
        self.assert_sentence(step, r"\bdoes not apply the low value goods limit in s 84-79\(3\) of the GST Act\b",
                             r"\breads it at the source for the period\b")
        self.assertEqual(figures(skill_text(SKILL)), [], "the skill states no figure")
        self.assert_sentence(step, r"\bAgent read on 12 November 2026, human review pending\b", r"\bcompilation 96\b")

    def test_foreign_currency_keeps_the_shown_rate_and_routes_conversion(self) -> None:
        step = workflow_step(SKILL, 8)
        self.assert_sentence(step, r"\bthe conversion rate the report or the bank shows\b")
        self.assert_sentence(step, DO_NOT + r"supply a rate\b")
        self.assert_routes_to(step, "au-forex-review")

    def test_neighbouring_work_is_routed_not_repeated(self) -> None:
        self.assert_routes_to(workflow_step(SKILL, 1), "au-short-stay-accommodation", "statement-to-csv")
        self.assert_routes_to(workflow_step(SKILL, 4), "reconciliation-break-trace", "month-end-close")
        self.assert_routes_to(workflow_step(SKILL, 9), "au-sole-trader")

    def test_stock_questions_go_to_the_practitioner(self) -> None:
        step = workflow_step(SKILL, 9)
        self.assert_sentence(step, r"\bOutside `au-sole-trader`, no skill in this pack classifies cost of sales or counts stock\b",
                             r"\bpractitioner\b")
        self.assertNotIn("`year-end-workpapers`", step)

    def test_an_unregistered_seller_goes_to_the_registration_review(self) -> None:
        step = workflow_step(SKILL, 7)
        self.assert_sentence(step, r"\bWhere the seller is not registered for GST\b", r"\brebuilt gross sales\b",
                             r"\bplatform-collected tax leads\b", r"`au-gst-registration-review`",
                             DO_NOT + r"decide anything about registration\b")

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

    def test_each_planted_fault_is_found_by_a_skill_step(self) -> None:
        """Each fault the card plants is a required check, and the skill step that finds it says so."""
        for card_name, fault, number, rule in (
            ("planted-faults", r"\b50\.00 difference\b.*\bopen item\b", 4, r"\bany amount or date difference are open items\b"),
            ("planted-faults", r"\bsales recorded net of fees as an exception\b", 6, r"\braise it as an exception\b"),
            ("planted-faults", r"\b300\.00 reserve still held\b", 5, r"\bplus reserves still held\b"),
            ("planted-faults", r"\brefund to its settlement T1 order\b", 3, r"\bLink each refund to its original order\b"),
            ("planted-faults", r"\bleave settlement T1's fee GST blank\b", 7, r"\bleave it blank and list the missing invoice\b"),
            ("transit-and-carried-balance", r"\b1545\.00 payout\b.*\bin transit\b", 5,
             r"\bpayouts the reports show as paid that the bank had not received\b"),
            ("transit-and-carried-balance", r"-255\.00\b.*\bstays in the clearing account\b", 5,
             r"\bbalance carried between settlements stays in the clearing account\b"),
            ("transit-and-carried-balance", r"\brefund and fees on the unsettled orders\b", 5,
             r"\bthe net of every component the reports show as not yet in a paid settlement\b"),
        ):
            card = (CARDS / f"marketplace-settlements-{card_name}.md").read_text(encoding="utf-8")
            checks = " ".join(card.split("## Required checks", 1)[1].split("## Must not do", 1)[0].split())
            with self.subTest(card=card_name, fault=fault):
                self.assertRegex(checks, fault)
                self.assertRegex(workflow_step(SKILL, number), rule)

    def test_figure_guard_catches_bare_amounts_but_not_section_numbers(self) -> None:
        self.assertEqual(figures("a limit of 1,000 or 82.50"), ["1,000", "82.50"])
        self.assertEqual(figures("$75 and A$1"), ["$75", "A$1"])
        self.assertEqual(figures("s 84-79(3), compilation 96, 12 November 2026 and 3 GST classes"), [])


def figures(text: str) -> list[str]:
    """Money-like figures: a dollar sign, a thousands separator or 2 decimal places."""
    return re.findall(r"A?\$\s?\d[\d,]*(?:\.\d+)?|\b\d{1,3}(?:,\d{3})+(?:\.\d+)?\b|\b\d+\.\d{2}\b", text)


if __name__ == "__main__":
    unittest.main()
