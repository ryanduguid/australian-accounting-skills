# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: Apache-2.0
"""The MIT and AMIT trustee skill: status stays a fact for the reviewer, no rate without its facts."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILL = REPOSITORY / ".claude" / "skills" / "au-mit-amit-trustee"


def text() -> str:
    return " ".join((SKILL / "SKILL.md").read_text(encoding="utf-8").split())


def step(number: int) -> str:
    body = text()
    start = body.index(f"{number}. **")
    end = body.find(f"{number + 1}. **", start)
    return body[start : end if end != -1 else body.index("## Tax calculator")]


class MitAmitTrusteeTests(unittest.TestCase):
    def test_every_link_has_a_pending_source_record(self) -> None:
        links = set(re.findall(r"\]\((https://[^)]+)\)", text()))
        records = json.loads((SKILL / "sources.json").read_text(encoding="utf-8"))["sources"]
        self.assertEqual(links, {record["url"] for record in records})
        for record in records:
            with self.subTest(url=record["url"]):
                self.assertEqual(record["verification_status"], "source-discovery-only-human-review-pending")
                self.assertEqual(record["checked_at"], "")

    def test_status_is_recorded_as_facts_never_concluded(self) -> None:
        self.assertIn(
            "It never concludes that a trust is a managed investment trust, a withholding MIT or an AMIT, "
            "and never applies a withholding rate, without the facts each step lists",
            text(),
        )
        self.assertIn("MIT status is a conclusion for the reviewer, never this skill's", step(1))
        # A foreign resident individual at 10% or more fails the closely held restriction at any time in the year.
        self.assertIn("a foreign resident individual with a MIT participation interest of 10% or more fails", step(1))
        # s 12-383(1)(a): a trust that is a MIT only under s 275-45 is not a withholding MIT.
        self.assertIn("not only because of s 275-45 of the ITAA 1997", step(2))
        self.assertIn("Whether the proportion is substantial is the reviewer's decision", step(2))

    def test_the_amit_choice_is_irrevocable_and_never_made_by_the_return(self) -> None:
        choice = step(3)
        self.assertIn("The choice cannot be revoked", choice)
        self.assertIn(
            "never prepare an AMIT return for a trust whose trustee has not decided to make the choice", choice
        )
        self.assertIn("route the trust's net income to `au-trust-distributions`", choice)

    def test_amma_statements_keep_their_timing_and_content(self) -> None:
        amma = step(5)
        self.assertIn("no later than 3 months after the end of the income year", amma)
        self.assertIn("a statement given more than 4 years after the end of the year is not an AMMA statement", amma)
        self.assertIn("without streaming any character to a member because of the member's tax characteristics", amma)
        self.assertIn("Whether the attribution is fair and reasonable is the reviewer's decision", amma)
        self.assertIn("s 286-75(2AB) in Schedule 1 to the TAA 1953", amma)

    def test_trustee_shortfall_is_net_of_rounding_and_member_shortfalls(self) -> None:
        liabilities = step(7)
        self.assertIn(
            "less the part that is a rounding adjustment deficit and the part already taxed under s 276-405, "
            "with a discount capital gain shortfall doubled",
            liabilities,
        )
        self.assertIn("(compilation 66, read 24 November 2026) each set a rate of 45%", liabilities)
        self.assertIn("record both and leave the rate applied to the reviewer", liabilities)
        # s 276-340(2): a non-FITO tax offset trust component deficit is the trustee's own liability.
        self.assertIn("which the trustee is taxed on under s 276-340 of the ITAA 1997", liabilities)
        self.assertIn("No under or over arises once the amendment period under s 170 of the ITAA 1936", step(6))

    def test_no_withholding_rate_without_character_address_and_listed_country(self) -> None:
        withholding = step(8)
        self.assertIn(
            "15% for a fund payment, 10% to the extent it is from a clean building managed investment trust "
            "(ss 12-425 and 12-430), and 30% to the extent it is attributable to non-concessional MIT income",
            withholding,
        )
        self.assertIn("any other address, 30%", withholding)
        self.assertIn("listed in the table in s 34 of the *Taxation Administration Regulations 2017*, each with its own date of effect", withholding)
        self.assertIn("where any is missing, leave the rate blank and the item open", withholding)
        self.assertIn("turns on the recipient's residence (s 12-390(7)), not the address", withholding)
        # ss 12A-110(9) and (10) and 12-405(4) and (5) cap the Commissioner's extension; s 12A-110(8)
        # stops a post-AMMA actual payment being counted again.
        self.assertIn("up to 3 years more under s 12A-110(9) and (10)", withholding)
        self.assertIn("up to 3 months more under s 12-405(4) and (5)", withholding)
        self.assertIn("is not another fund payment (s 12A-110(8)", withholding)
        hand_off = text().split("## Hand-off and checks", 1)[1]
        self.assertIn("no withholding rate appears without the payment's character split", hand_off)

    def test_notices_and_payment_summaries_keep_their_deadlines(self) -> None:
        notices = step(9)
        self.assertIn("for at least 5 continuous years, before or at the time of the payment", notices)
        self.assertIn(
            "not later than 14 days after the end of 6 months after the end of the trust's income year", notices
        )
        self.assertIn("s 16-157 in Schedule 1 to the TAA 1953", notices)
        # s 12A-15(1)(c): the AMIT notice covers deemed and pre-AMMA actual payments only.
        self.assertIn(
            "only for a deemed payment under s 12A-205 or a pre-AMMA actual payment in respect of one", notices
        )

    def test_return_map_shows_taxable_amounts_and_capital_gains_reform(self) -> None:
        labels = step(10)
        self.assertIn("each showing the taxable amount, not the tax", labels)
        self.assertIn("(published 31 May 2026, read 24 November 2026)", labels)
        self.assertIn("For a CGT event on or after 1 July 2027", labels)

    def test_calculator_takes_the_net_amount_and_never_estimates_it(self) -> None:
        calculator = text().split("## Tax calculator", 1)[1].split("## Hand-off and checks", 1)[0]
        self.assertIn('{"kind": "cgt_cost_base_adjustments"}', calculator)
        self.assertIn("It does not work out the trustee's estimate in step 5", calculator)
        self.assertIn("for income years from 2018-19 to 2026-27", calculator)


if __name__ == "__main__":
    unittest.main()
