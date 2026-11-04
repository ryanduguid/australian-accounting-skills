# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""Skills that meet a 2026 rule change keep its start date, its scope and its source."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[1] / ".claude" / "skills"
PENDING = "source-discovery-only-human-review-pending"


def skill_text(skill: str) -> str:
    return re.sub(r"\s+", " ", (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8"))


def step(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin : text.index(end, begin)]


def records(skill: str) -> dict[str, dict[str, object]]:
    payload = json.loads((SKILLS / skill / "sources.json").read_text(encoding="utf-8"))
    return {str(source["url"]): source for source in payload["sources"]}


class DatedRuleChangeTests(unittest.TestCase):
    def assert_cited_and_pending(self, skill: str, *urls: str) -> None:
        text = skill_text(skill)
        indexed = records(skill)
        for url in urls:
            with self.subTest(skill=skill, url=url):
                self.assertIn(f"]({url})", text)
                self.assertEqual(indexed[url]["verification_status"], PENDING)
                self.assertEqual(indexed[url]["checked_at"], "")

    def test_smsf_lrba_real_property_must_be_business_real_property(self) -> None:
        text = skill_text("au-smsf-year-end")
        borrowing = step(text, "For each limited recourse borrowing arrangement", "5. Build the annual-return")
        self.assertIn("s 67A(2)(c) of the *Superannuation Industry (Supervision) Act 1993*", borrowing)
        self.assertIn("business real property within the meaning of s 66", borrowing)
        self.assertIn("from 10 August 2026", borrowing)
        self.assertIn("the date the LRBA was entered into and the date of the contract", borrowing)
        self.assertIn("maintains or refinances a borrowing under an arrangement entered into before", borrowing)
        self.assertIn("even if settlement happens later", borrowing)
        self.assertIn("for the life of the LRBA", borrowing)
        self.assertIn("possible contravention of the borrowing prohibition in s 67(1)", borrowing)
        self.assertIn("do not conclude on it", borrowing)
        self.assertIn("LRBA loan and acquisition contracts", step(text, "## Inputs", "## Workflow"))
        self.assert_cited_and_pending(
            "au-smsf-year-end",
            "https://www.legislation.gov.au/C2026A00049/asmade/text",
            "https://www.legislation.gov.au/C2004A04633/latest/text",
            "https://www.ato.gov.au/individuals-and-families/super-for-individuals-and-families/"
            "self-managed-super-funds-smsf/smsf-investing/restrictions-on-smsf-investments/"
            "smsf-borrowing-restrictions/limited-recourse-borrowing-arrangements/"
            "changes-to-limited-recourse-borrowing-arrangements",
        )

    def test_rental_holiday_home_costs_are_denied_before_apportionment(self) -> None:
        text = skill_text("au-rental-property")
        screen = step(text, "Before apportioning, screen for a holiday home.", "5. If cashflow")
        self.assertIn("s 26-50 of the *Income Tax Assessment Act 1997*", screen)
        self.assertIn("denied rather than apportioned", screen)
        self.assertIn("at all times in the income year it was used or held for use mainly", screen)
        self.assertIn("(s 26-50(3)(b)(ii))", screen)
        self.assertIn("advertising for tenants or cleaning after a guest stay, stay under s 8-1", screen)
        self.assertIn("definite and sustained change", screen)
        self.assertIn("s 26-50(4)", screen)
        self.assertIn("expenses incurred before 1 July 2026", screen)
        self.assertIn("evidence of avoidance, fraud or evasion", screen)
        self.assertIn("an amended assessment or private ruling follows the ruling", screen)
        self.assertIn("PCG 2026/3", screen)
        self.assertIn("cost base", screen)
        self.assert_cited_and_pending(
            "au-rental-property",
            "https://www.ato.gov.au/law/view/document?DocID=TXR/TR20261/NAT/ATO/00001",
            "https://www.ato.gov.au/law/view/document?DocID=COG/PCG20263/NAT/ATO/00001",
            "https://www.legislation.gov.au/C2004A05138/latest/text",
        )


if __name__ == "__main__":
    unittest.main()
