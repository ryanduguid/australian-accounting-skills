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
            "s 135-5",
            # No margin scheme on a GST-free supply; the history decides a later sale.
            "The margin scheme applies only to a taxable supply (s 75-5(1))",
            "s 75-5(3)(f)", "s 75-11(5)",
            # Withholding needs a taxable supply, but the notice duty is separate.
            "is not a taxable supply (s 9-5)", "s 14-250(9)", "s 14-255",
            "leave the amount blank for the reviewer",
            "mark the classification `UNVERIFIED`",
        )
        self.assert_pending_and_cited(
            "au-gst-property",
            *(LAW + f"PAC/19990055/{section}" for section in
              ("9-5", "38-325", "38-475", "38-480", "75-5", "75-11", "135-5", "195-1")),
            LAW + "PAC/19530001/Sch1-14-250",
            LAW + "PAC/19530001/Sch1-14-255",
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
            "s 152-10", "s 152-35", "s 152-40(4)(e)", "s 152-40(4A)", "s 152-105", "s 152-305",
            "s 152-410", "s 152-80",
            "Verify every threshold, limit and age test at the source for the year",
            "s 40-295", "s 40-340(3)", "s 70-90", "s 70-100(4)",
            "A depositor's rights cannot be transferred to another entity (item 6 of the table in s 393-35)",
            "does not start again within 120 days (item 11)",
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
              ("40-295", "40-340", "70-90", "70-100", "104-10", "116-30", "128-15", "152-10", "152-35",
               "152-40", "152-80", "152-105", "152-205", "152-305", "152-410", "393-35")),
        )

    def test_cards_target_their_skills_and_their_arithmetic_holds(self) -> None:
        gst = card("au-gst-property-farm-land-and-associate-lot")
        self.assertIn("target_skills: - au-gst-property", gst)
        self.assertEqual(Decimal("1840000.00") + Decimal("2150.00"), Decimal("1842150.00"))
        self.assert_carries(
            gst, "1840000.00 plus 2150.00 equals 1842150.00", "It is not an input tax credit",
            "s 14-255", "the appraisal letter is not a valuation",
            "Do not apply the margin scheme to a supply claimed as GST-free",
        )
        succession = card("au-primary-production-farm-succession-evidence")
        self.assertIn("target_skills: - au-primary-production", succession)
        self.assertEqual(1450 + 520 - 610 - 35, 1325)
        self.assert_carries(
            succession, "1450 plus 520 less 610 sold and 35 deaths equals 1325",
            "cannot be transferred to the daughter", "Do not conclude that any concession applies",
            "Do not recommend who receives which assets",
        )


if __name__ == "__main__":
    unittest.main()
