# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The farm land GST step and the farm succession step keep each statutory condition and route."""

from __future__ import annotations

import re
import unittest
from decimal import Decimal
from pathlib import Path

from skill_prose import ISO_DATE, PENDING, PENDING_FACT, records, skill_text, workflow_step

CASES = Path(__file__).resolve().parents[1] / "validation" / "cases"
LAW = "https://www.ato.gov.au/law/view/document?docid="


def card(name: str) -> str:
    return " ".join((CASES / f"{name}.md").read_text(encoding="utf-8").split())


class FarmLandAndSuccessionTests(unittest.TestCase):
    def assert_carries(self, text: str, *terms: str) -> None:
        for term in terms:
            with self.subTest(term=term):
                self.assertIn(term, text)

    def assert_pending_and_cited(self, skill: str, *urls: str) -> None:
        text = skill_text(skill)
        indexed = records(skill)
        for url in urls:
            with self.subTest(skill=skill, url=url):
                self.assertIn(f"]({url})", text)
                record = indexed[url]
                self.assertEqual(record["verification_status"], PENDING)
                self.assertEqual(record["checked_at"], "")
                self.assertEqual(record["fact"], PENDING_FACT)
                self.assertRegex(str(record["review_required_since"]), ISO_DATE)

    def test_farm_land_paths_keep_their_conditions_and_interactions(self) -> None:
        step = workflow_step("au-gst-property", 5)
        self.assert_carries(
            step,
            "**Human review pending:**", "on 11 November 2026 (not a human review)",
            "A vendor's being a farmer does not make a sale GST-free",
            # s 38-480: both limbs, read as a continuous period, land only.
            "for at least the period of 5 years preceding the supply",
            "the recipient intends that a farming business be carried on, on the land",
            "continuous 5 years immediately before the supply",
            "Section 38-480 covers the interest in land only",
            "Evidence the recipient's intention in writing",
            # s 38-475: potential residential land to an associate below market value.
            "is to an associate of the supplier without consideration or for less than the GST inclusive market value",
            "(land that it is permissible to use for residential purposes but that does not contain any buildings "
            "that are residential premises, s 195-1)",
            # Going concern conditions differ from s 38-480's.
            "s 38-480 has none of those conditions but covers only the land",
            "carries on the enterprise until the day of the supply (s 38-325(2)(a) and (b))",
            "ATO ID 2001/291, an edited record of an ATO decision rather than a public ruling",
            # A later change of use is a Division 129 adjustment, not only the s 135-5 one.
            "s 135-10 applies Division 129", "whether or not a s 135-5 adjustment arose (s 135-10(3))",
            # No margin scheme on a GST-free supply; the history decides a later sale.
            "The margin scheme applies only to a taxable supply (s 75-5(1))",
            "s 75-5(2) and (3)(f)", "Test s 75-11(5) first",
            # Withholding needs a taxable supply, but the notice duty is separate.
            "is not a taxable supply (s 9-5)", "s 14-250(9)", "s 14-255",
            # A withheld amount is either the supplier's credit or a refund in error, never chosen here.
            "record the evidence for both outcomes without choosing between them", "(s 18-60)",
            "lodged at least 14 days before the supplier must pay GST on the supply",
            "leave the amount blank for the reviewer",
            "mark the classification `UNVERIFIED`",
        )
        self.assert_pending_and_cited(
            "au-gst-property",
            *(LAW + f"PAC/19990055/{section}" for section in
              ("9-5", "38-325", "38-475", "38-480", "75-5", "75-11", "135-5", "135-10", "195-1")),
            LAW + "PAC/19530001/Sch1-14-250",
            LAW + "PAC/19530001/Sch1-14-255",
            LAW + "PAC/19530001/Sch1-18-60",
            LAW + "AID/AID2001291/00001",
            LAW + "GII/GSTIIPP3/NAT/ATO/00001",
            LAW + "GSD/GSTD20112/NAT/ATO/00001",
        )

    def test_farm_succession_prepares_evidence_and_leaves_decisions_open(self) -> None:
        step = workflow_step("au-primary-production", 8)
        self.assert_carries(
            step,
            "**Human review pending:**", "on 11 November 2026 (not a human review)",
            "Do not choose the structure, the timing or who receives what",
            "A missing cost or value is unknown, not zero",
            "CGT event A1 (s 104-10)", "s 116-30 substitutes market value", "s 128-15",
            # Farm facts for the concessions; the general conditions live in au-small-business-cgt.
            "Route the concession evidence to `au-small-business-cgt`", "s 152-10(1)(c)(iii) and (1B)",
            "s 152-40(4)(e)", "s 152-40(4A)", "unless that main use was only temporary",
            "s 152-40(2) disregards s 392-20(1)", "(s 152-105(d))", "(s 104-10(3))",
            "s 70-105", "(s 70-105(7))",
            "Verify every threshold, limit and age test at the source for the year",
            "s 40-295", "s 40-340(3)", "s 70-90", "s 70-100(4)",
            "A depositor's rights cannot be transferred to another entity (item 6 of the table in s 393-35)",
            "dies or becomes bankrupt",
            "ceases to carry on a primary production business in Australia and does not start carrying on such a "
            "business again within 120 days (item 11)",
            "The successor cannot take over a deposit",
            "s 392-10(1)", "s 392-10(2)",
            "`au-small-business-cgt`", "`au-restructure-rollovers`", "`au-deceased-estates`", "`au-capital-gains`",
            "`au-depreciation-schedule`", "`au-transfer-duty`", "`au-land-tax`", "`au-gst-property`",
            "`au-trust-deed-review`",
            "List each as an open decision with its owner; do not recommend one.",
        )
        self.assertIsNone(re.search(r"\$\s?\d|\d\s?%", step), "no threshold or rate is stated")
        self.assert_pending_and_cited(
            "au-primary-production",
            *(LAW + f"PAC/19970038/{section}" for section in
              ("40-295", "40-340", "70-90", "70-100", "70-105", "104-10", "116-30", "128-15", "152-10",
               "152-40", "152-105", "393-35")),
        )
        concessions = " ".join(skill_text("au-small-business-cgt").split())
        self.assert_carries(
            concessions,
            "s 152-10(1)(c)", "s 152-10(1A) and (1B)", "s 152-10(2)", "active asset test in s 152-35",
            "unless that main use was only temporary (s 152-40(4)(e))", "s 152-40(4A)",
            "For an individual's 15-year exemption (s 152-105)", "For the retirement exemption (s 152-305)",
            "s 152-325 requires", "For the small business rollover (s 152-410)", "J2, J5 and J6",
            "(s 152-80(1)(d) and (3))",
            # The reduction's own entity test from the 2027-28 income year.
            "Section 152-205(2), inserted by No 49 of 2026", "disregards s 152-10(1AA)(b)",
        )
        self.assert_pending_and_cited(
            "au-small-business-cgt",
            *(LAW + f"PAC/19970038/{section}" for section in
              ("152-10", "152-35", "152-40", "152-80", "152-105", "152-205", "152-305", "152-325", "152-410")),
        )

    def test_cards_target_their_skills_and_their_arithmetic_holds(self) -> None:
        gst = card("au-gst-property-farm-land-and-associate-lot")
        self.assertIn("target_skills: - au-gst-property", gst)
        # The bridge in the required checks must follow from the settlement statement in the inputs.
        settlement = re.search(r"Settlement statement for the main sale: price ([\d.]+) plus a rates adjustment "
                               r"of ([\d.]+), total ([\d.]+)\.", gst)
        assert settlement, "the card no longer states the settlement statement"
        price, rates, total = (Decimal(figure) for figure in settlement.groups())
        self.assertEqual(price + rates, total)
        self.assertIn(f"{price} plus {rates} equals {total}", gst)
        self.assert_carries(
            gst, "It is not an input tax credit", "s 38-325(2)(b)", "s 18-60",
            "treat the withheld amount as reducing the GST calculated on the supply",
            "s 14-255", "the appraisal letter is not a valuation",
            "Do not apply the margin scheme to a supply claimed as GST-free",
        )
        succession = card("au-primary-production-farm-succession-evidence")
        self.assertIn("target_skills: - au-primary-production", succession)
        # The head-count reconciliation must follow from the flock movements in the inputs.
        flock = re.search(r"Flock: (\d+) opening head, (\d+) lambs marked, (\d+) sold, (\d+) deaths, "
                          r"(\d+) closing head\.", succession)
        assert flock, "the card no longer states the flock movements"
        opening, marked, sold, deaths, closing = (int(figure) for figure in flock.groups())
        self.assertEqual(opening + marked - sold - deaths, closing)
        self.assertIn(f"{opening} plus {marked} less {sold} sold and {deaths} deaths equals {closing}", succession)
        self.assert_carries(
            succession,
            "cannot be transferred to the daughter", "Do not conclude that any concession applies",
            "Do not recommend who receives which assets",
        )


if __name__ == "__main__":
    unittest.main()
