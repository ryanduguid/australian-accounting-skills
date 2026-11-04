# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""Skills that meet the Tax Reform No. 3 Bill keep it a dated, unenacted proposal."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[1] / ".claude" / "skills"
BILL = "*Treasury Laws Amendment (Tax Reform No. 3) Bill 2026*"
BILL_PAGE = (
    "https://www.aph.gov.au/Parliamentary_Business/Bills_Legislation/"
    "Bills_Search_Results/Result?bId=r7554"
)
RATES_BILL_PAGE = (
    "https://www.aph.gov.au/Parliamentary_Business/Bills_Legislation/"
    "Bills_Search_Results/Result?bId=r7555"
)
UNENACTED = (
    "As at 4 November 2026 the Bill had passed the House of Representatives "
    "but not the Senate, and was not law."
)


def skill_text(skill: str) -> str:
    return re.sub(r"\s+", " ", (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8"))


def step(text: str, start: str, end: str) -> str:
    begin = text.index(start)
    return text[begin : text.index(end, begin)]


def recorded_urls(skill: str) -> set[str]:
    payload = json.loads((SKILLS / skill / "sources.json").read_text(encoding="utf-8"))
    return {source["url"] for source in payload["sources"]}


class TaxReformNo3StatusTests(unittest.TestCase):
    def test_each_skill_cites_and_records_the_bill_page(self) -> None:
        for skill in ("au-trust-distributions", "au-super-contribution-caps", "au-rental-property"):
            with self.subTest(skill=skill):
                self.assertIn(f"]({BILL_PAGE})", skill_text(skill))
                self.assertIn(BILL_PAGE, recorded_urls(skill))

    def test_trust_minimum_tax_status_names_both_bills_and_their_stage(self) -> None:
        text = skill_text("au-trust-distributions")
        note = step(text, "5. The minimum tax on discretionary trusts", "## Hand-off")
        self.assertNotIn("not law on 26 September 2026", text)
        self.assertIn(BILL, note)
        self.assertIn(
            "*Income Tax Rates Amendment (Minimum Tax on Discretionary Trusts) Bill 2026*", note
        )
        self.assertIn(
            "As at 4 November 2026 both Bills had passed the House of Representatives "
            "(29 October 2026) but not the Senate, and were not law.",
            note,
        )
        self.assertIn("report was due on 13 November 2026", note)
        self.assertIn("the income year that includes 1 July 2028", note)
        self.assertIn("Check each Bill's stage on its Parliament of Australia page at use time", note)
        self.assertIn("Do not apply an announced measure in a current-law calculation", note)
        self.assertIn(f"]({RATES_BILL_PAGE})", text)
        self.assertIn(RATES_BILL_PAGE, recorded_urls("au-trust-distributions"))

    def test_june_2026_quarter_contributions_count_under_current_law(self) -> None:
        text = skill_text("au-super-contribution-caps")
        cap_test = step(text, "3. Concessional cap:", "4. Excess concessional")
        self.assertIn("employer contribution for the quarter ending 30 June 2026", cap_test)
        self.assertIn(
            "Under current law it counts towards the 2026-27 concessional cap, because a "
            "contribution counts in the year the fund receives it.",
            cap_test,
        )
        self.assertIn(f"Schedule 6 of the {BILL} proposes transitional relief", cap_test)
        self.assertIn("but not salary sacrificed contributions", cap_test)
        self.assertIn(UNENACTED, cap_test)
        self.assertIn("Do not apply the relief until it is enacted", cap_test)
        self.assertIn("as a labelled scenario beside the current-law cap test", cap_test)
        headroom = step(text, "7. **Proposed salary sacrifice.**", "## Hand-off")
        self.assertIn("In 2026-27 this includes any June 2026 quarter contributions from step 3.", headroom)

    def test_new_dwelling_meaning_rests_on_a_determination_until_schedule_5_passes(self) -> None:
        loans = step(skill_text("au-rental-property"), "3. Trace borrowed funds", "4. Apply supported")
        self.assertIn("requirements the Minister determines by legislative instrument (s 26-160(3) and (4))", loans)
        self.assertIn(f"Schedule 5 of the {BILL} would replace those", loans)
        self.assertIn("a new s 960-590", loans)
        self.assertIn(UNENACTED, loans)
        self.assertIn("do not apply the Bill's tests in a current-law calculation", loans)


if __name__ == "__main__":
    unittest.main()
