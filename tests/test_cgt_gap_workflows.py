# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The main residence and share buy-back workflows added on 11 November 2026 keep their key rules.

Each test reads one numbered workflow step and checks the provisions, conditions and
prohibitions it must carry, not its wording, in the style of test_practice_workflows.py.
The helpers are in skill_prose.py.
"""

from __future__ import annotations

import re
import unittest

from skill_prose import (
    DO_NOT,
    IN_PROHIBITED_LIST,
    ISO_DATE,
    PENDING,
    PENDING_FACT,
    SKILLS,
    affirms,
    records,
    sentences,
    skill_text,
    workflow_step,
)

MR = (
    "https://www.ato.gov.au/individuals-and-families/investments-and-assets/"
    "capital-gains-tax/property-and-capital-gains-tax/your-main-residence-home"
)
MAIN_RESIDENCE = "au-main-residence"
BUY_BACK = "au-share-buy-back"


class CgtGapWorkflowTests(unittest.TestCase):
    def assert_carries(self, text: str, *terms: str) -> None:
        folded = text.casefold()
        for term in terms:
            with self.subTest(term=term):
                self.assertIn(term.casefold(), folded)

    def assert_sentence(self, text: str, *patterns: str, affirmed: tuple[str, ...] = ()) -> None:
        """One sentence of `text` matches every pattern, case-insensitively, and each
        `affirmed` pattern with no negator directly before it."""
        with self.subTest(patterns=patterns, affirmed=affirmed):
            self.assertTrue(
                any(all(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)
                    and all(affirms(sentence, pattern) for pattern in affirmed)
                    for sentence in sentences(text)),
                f"no sentence matches all of {patterns} with {affirmed} affirmed",
            )

    def assert_prohibited(self, text: str, *actions: str) -> None:
        """Each action is named in `text`, and every mention is an item of a prohibited list."""
        for action in actions:
            with self.subTest(prohibited=action):
                mentions = [sentence[: match.start()] for sentence in sentences(text)
                            for match in re.finditer(action, sentence, re.IGNORECASE)]
                self.assertTrue(mentions, f"{action!r} is not named")
                for before in mentions:
                    self.assertTrue(re.search(IN_PROHIBITED_LIST, before, re.IGNORECASE),
                                    f"{action!r} is not inside a prohibited list after {before!r}")

    def assert_routes_to(self, text: str, *names: str) -> None:
        for name in names:
            with self.subTest(route=name):
                self.assertIn(f"`{name}`", text)
                self.assertTrue((SKILLS / name / "SKILL.md").is_file())

    def assert_cited_and_recorded(self, skill: str, *urls: str) -> None:
        text = skill_text(skill)
        indexed = records(skill)
        self.assertEqual(set(indexed), set(urls), "every indexed source is cited and checked here")
        for url in urls:
            with self.subTest(skill=skill, url=url):
                self.assertIn(f"]({url})", text)
                record = indexed[url]
                self.assertEqual(record["verification_status"], PENDING)
                self.assertEqual(record["checked_at"], "")
                self.assertEqual(record["fact"], PENDING_FACT)
                self.assertRegex(str(record["review_required_since"]), ISO_DATE)

    # main residence

    def test_main_residence_screens_who_can_use_it(self) -> None:
        step = workflow_step(MAIN_RESIDENCE, 1)
        self.assert_carries(step, "Section 118-110(1)", "s 118-110(2)", "s 118-110(3)", "s 118-110(4)",
                            "s 118-110(5)", "s 118-185(3)", "ss 118-195 and 118-200")
        self.assert_sentence(step, r"\bindividual\b", r"\bdeceased estate\b")
        # Residency is tested at the CGT event, and the foreign resident bar reaches the partial exemption.
        self.assert_sentence(step, r"\bresidency at the time of the CGT event\b")
        self.assert_sentence(step, r"\bcontinuous period of more than 6 years\b")
        self.assert_sentence(step, r"\blife events test\b", r"\bdoes not satisfy\b")
        self.assert_sentence(step, r"\bcannot use the home first used to produce income rule\b")
        self.assert_routes_to(step, "au-deceased-estates", "au-tax-residency", "au-nonresident-cgt")

    def test_main_residence_keeps_both_date_bases_and_the_land_limits(self) -> None:
        step = workflow_step(MAIN_RESIDENCE, 2)
        self.assert_carries(step, "20 September 1985", "s 118-130(2) and (3)", "s 118-115", "s 118-120",
                            "s 118-165", "s 118-245")
        self.assert_sentence(step, r"\bboth date pairs\b", r"\bboth day counts\b",
                             affirmed=(r"\bleave the basis to the reviewer\b",))
        self.assert_sentence(step, r"\bprimarily for private or domestic purposes\b",
                             r"\b2 hectares less the land under the dwelling\b")
        self.assert_sentence(step, r"\bland used to produce income is\W+not exempt\b")
        self.assert_sentence(step, r"\bmust include the land under the dwelling\b")

    def test_main_residence_tests_each_extension_with_its_conditions(self) -> None:
        step = workflow_step(MAIN_RESIDENCE, 3)
        self.assert_carries(step, "s 118-135", "s 118-140", "s 118-145", "s 118-150", "s 118-155",
                            "ss 118-147 and 118-160", "s 118-170", "s 118-175", "ss 118-178 and 118-180")
        self.assert_sentence(step, r"\bno gaps or overlaps\b")
        # Changing residences: the shorter period and both conditions.
        self.assert_sentence(step, r"\bshorter of 6 months\b", r"\bat least 3 months in the 12 months\b",
                             r"\bnot used to produce assessable income\b")
        # Absence: 6 years each absence while income producing, otherwise unlimited, and exclusivity.
        self.assert_sentence(step, r"\bmaximum is 6 years for each absence\b", r"\botherwise there is no limit\b")
        self.assert_sentence(step, r"\bNo other dwelling can be the main residence\b", r"\bs 118-140\b")
        self.assert_sentence(step, r"\bcannot cover a period before the dwelling first became the main residence\b")
        # Building: life interest excluded, 3 months, 4-year limit.
        self.assert_sentence(step, r"\bother than a life interest\b", r"\bat least 3 months\b")
        self.assert_sentence(step, r"\bshorter of 4 years\b")
        # Spouse split by interest, and the child rule.
        self.assert_sentence(step, r"\bnot more than half\b", r"\bwhole period\b", r"\bhalf the period\b")
        self.assert_sentence(step, r"\bliving permanently separately and apart\b")
        self.assert_sentence(step, r"\bdependent child under 18\b", r"\bone dwelling must be chosen\b")
        choices = step[step.index("Do not make"):]
        self.assert_sentence(choices, DO_NOT + r"make\b")
        self.assert_prohibited(choices, r"\bmake\b", r"\bvary\b", r"\brecommend\b")
        self.assert_sentence(choices, affirmed=(r"\bthe owner chooses\b",))

    def test_main_residence_records_income_use_and_the_first_use_rule(self) -> None:
        step = workflow_step(MAIN_RESIDENCE, 4)
        self.assert_carries(step, "s 118-190", "s 118-190(1)(c)", "s 118-190(3)", "s 118-192",
                            "7.30 pm", "20 August 1996")
        self.assert_sentence(step, r"\bapplies even where there is no loan\b")
        self.assert_sentence(step, r"\bset aside exclusively\b", r"\bnot readily adaptable for private use\b")
        self.assert_sentence(step, r"\btaken to have acquired the dwelling at that time for its market value\b")
        self.assert_sentence(step, r"\bincome use from acquisition\b", r"\bforeign resident\b")
        self.assert_sentence(step, r"\bUNVERIFIED\b", r"\baccepts a valuation\b")
        self.assert_sentence(step, r"\bappraisal is a screen\b", r"\bnot evidence of market value\b")

    def test_main_residence_apportions_only_on_supported_inputs(self) -> None:
        step = workflow_step(MAIN_RESIDENCE, 5)
        self.assert_carries(step, "s 118-185(2)", "s 118-190(2)", "s 102-6", "1 July 2027", "Subdivision 118-B")
        self.assert_sentence(step, r"\bnon-main residence days over the days in the ownership period\b")
        self.assert_sentence(step, r"\bevery input is supported\b", affirmed=(r"\bas preliminary\b",))
        self.assert_sentence(step, r"\bblank\b", r"\bUNVERIFIED\b", r"\binput is missing\b")
        self.assert_routes_to(step, "au-capital-gains")

    def test_main_residence_sources_are_pending(self) -> None:
        self.assert_cited_and_recorded(
            MAIN_RESIDENCE,
            "https://www.legislation.gov.au/C2004A05138/latest/text",
            MR,
            f"{MR}/eligibility-for-main-residence-exemption",
            f"{MR}/moving-to-a-new-main-residence",
            f"{MR}/treating-former-home-as-main-residence",
            f"{MR}/living-separately-to-your-spouse-or-children",
            f"{MR}/using-your-home-for-rental-or-business",
            f"{MR}/building-or-renovating-your-home",
            f"{MR}/destruction-of-your-home",
            f"{MR}/compulsory-acquisition-of-your-home",
            f"{MR}/home-on-more-than-2-hectares",
            "https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/"
            "foreign-residents-and-capital-gains-tax/main-residence-exemption-for-foreign-residents",
            "https://www.legislation.gov.au/C2026A00049/asmade/text",
        )

    def test_capital_gains_routes_a_main_residence_claim(self) -> None:
        text = " ".join(skill_text("au-capital-gains").split())
        self.assert_sentence(text, r"\bmain-residence exemption\b", rf"`{MAIN_RESIDENCE}`")
        self.assert_sentence(text, r"\bnot an established exemption\b")

    # share buy-back

    def test_buy_back_classifies_for_tax_and_procedure(self) -> None:
        step = workflow_step(BUY_BACK, 1)
        self.assert_carries(step, "s 159GZZZK", "s 159GZZZL", "s 257B(1)", "s 257B(2) and (3)",
                            "s 257B(4) and (5)", "s 257B(6) and (7)", "10/12 limit", "paragraph 40")
        self.assert_sentence(step, r"\bordinary course of trading\b", r"\bon-market\b")
        self.assert_sentence(step, r"\bminimum holding\b", r"\bemployee share scheme\b", r"\bequal access\b",
                             r"\bselective\b")
        self.assert_sentence(step, r"\bthe two can differ\b")

    def test_buy_back_lists_the_corporations_act_steps_without_concluding(self) -> None:
        step = workflow_step(BUY_BACK, 2)
        self.assert_carries(step, "Section 257A", "s 257C", "s 257D", "s 257E", "s 257F", "s 257G", "s 257H(3)",
                            "s 254Y(1)", "Forms 280 and 281")
        self.assert_sentence(step, r"\bmaterially prejudice\b", r"\bpay its creditors\b")
        self.assert_sentence(step, r"\bspecial resolution\b", r"\bno votes in favour\b", r"\bassociates\b",
                             r"\ball ordinary shareholders\b")
        self.assert_sentence(step, r"\bwithin 1 month\b")
        self.assert_sentence(step, r"\b28 days\b")
        self.assert_sentence(step, r"\bdiary the earlier\b")
        self.assert_sentence(step, DO_NOT + r"conclude\b", r"\bvalidly taken\b", r"\bsolvent\b")

    def test_buy_back_splits_the_price_by_company_type(self) -> None:
        step = workflow_step(BUY_BACK, 3)
        self.assert_carries(step, "s 159GZZZM", "s 159GZZZR", "s 159GZZZP(1)", "s 159GZZZP(2)",
                            "ss 159GZZZP(3) and 159GZZZPA", "25 October 2022", "paragraphs 12, 62 and 69")
        self.assert_sentence(step, r"\blisted public company\b", r"\bno part is a dividend\b")
        self.assert_sentence(step, r"\bnot a listed public company\b", r"\bdebited to the share capital account\b",
                             r"\bdividend\b")
        self.assert_sentence(step, r"\baverage capital per share\b", r"\bshares on issue\b")
        self.assert_sentence(step, r"\bbefore s 159GZZZPA\b")
        self.assert_sentence(step, DO_NOT + r"apply its dividend split guidance\b")

    def test_buy_back_evidences_market_value(self) -> None:
        step = workflow_step(BUY_BACK, 4)
        self.assert_carries(step, "s 159GZZZQ(2)", "s 202-45(c)", "TD 2004/22", "5 trading days",
                            "S&P/ASX 200", "paragraph 14")
        self.assert_sentence(step, r"\bas if it had not happened and were never proposed\b")
        self.assert_sentence(step, r"\bUNVERIFIED\b", r"\baccepts it\b")
        self.assert_sentence(step, r"\bappraisal as a screen only\b")

    def test_buy_back_schedules_franking_debits_and_unfrankable_parts(self) -> None:
        step = workflow_step(BUY_BACK, 5)
        self.assert_carries(step, "s 202-45(c)", "s 202-45(e)", "s 202-45(g)(i)", "s 202-45(h)(ii)",
                            "item 9 of the s 205-30 table", "Item 9A", "paragraph 163", "s 159GZZZN")
        self.assert_sentence(step, r"\bunfrankable to the extent the price exceeds that market value\b")
        self.assert_sentence(step, r"\bon-market\b", r"\bas if the purchase had been off-market\b",
                             r"\bnot listed\b")
        self.assert_routes_to(step, "au-franking-account")

    def test_buy_back_records_integrity_and_ruling_facts_without_concluding(self) -> None:
        step = workflow_step(BUY_BACK, 6)
        self.assert_carries(step, "ss 45A, 45B and 177EA", "s 204-30", "Divisions 725 and 727",
                            "paragraphs 18 to 24", "class ruling")
        self.assert_sentence(step, r"\bwithout concluding\b")
        self.assert_sentence(step, r"\bcovers only the scheme it describes\b")

    def test_buy_back_screens_division_7a_links(self) -> None:
        step = workflow_step(BUY_BACK, 7)
        self.assert_carries(step, "set off against", "shortfall released", "lent to fund the purchase",
                            "left owing", "above market value")
        self.assert_sentence(step, r"\bDivision 7A does not apply to amounts assessable under other parts\b")
        self.assert_routes_to(step, "div7a-compliance")

    def test_buy_back_prepares_each_sellers_position(self) -> None:
        step = workflow_step(BUY_BACK, 8)
        self.assert_carries(step, "s 159GZZZS", "s 159GZZZQ(1)", "s 159GZZZQ(3) to (5)", "s 159GZZZQ(3A)",
                            "s 159GZZZQ(8) and (9)", "s 159GZZZP(1A)", "paragraph 158", "paragraphs 71 to 88",
                            "last in first out")
        self.assert_sentence(step, r"\bCGT event\b", r"\boffer's terms\b")
        # Market value substitution reaches a listed company; the reduction does not.
        self.assert_sentence(step, r"\bmarket value\b", r"\bwhere the price is lower\b",
                             r"\bincluding for a listed public company\b")
        self.assert_sentence(step, r"\bs 159GZZZQ\(3A\) excludes a listed public company\b")
        self.assert_sentence(step, r"\bevery input is supported\b", r"\bpreliminary gain or loss\b")
        self.assert_sentence(step, r"\bblank\b", r"\bUNVERIFIED\b")
        self.assert_routes_to(step, "au-capital-gains", "au-dssp", "au-nonresident-cgt")

    def test_buy_back_sources_are_pending(self) -> None:
        self.assert_cited_and_recorded(
            BUY_BACK,
            "https://www.legislation.gov.au/C1936A00027/latest/text",
            "https://www.legislation.gov.au/C2004A05138/latest/text",
            "https://www.legislation.gov.au/C2004A00818/latest/text",
            "https://www.ato.gov.au/law/view/document?DocID=PSR/PS20079/NAT/ATO/00001",
            "https://www.ato.gov.au/law/view/document?DocID=TXD/TD200422/NAT/ATO/00001",
            "https://www.ato.gov.au/individuals-and-families/investments-and-assets/capital-gains-tax/"
            "shares-and-similar-investments/share-buy-backs",
            "https://www.ato.gov.au/law/view/view.htm?docid=AFS%2FCommunityBankcompanies%2F00001"
            "&PiT=99991231235958",
            "https://www.ato.gov.au/businesses-and-organisations/corporate-tax-measures-and-assurance/"
            "private-company-benefits-division-7a-dividends",
            "https://www.asic.gov.au/for-business-and-companies/companies/"
            "company-share-and-shareholder-rules-and-changes/company-share-buy-backs",
        )

    def test_franking_account_routes_a_buy_back(self) -> None:
        step = workflow_step("au-franking-account", 8)
        self.assert_sentence(step, r"\bshare buy-back\b", rf"`{BUY_BACK}`")
        self.assert_sentence(step, r"\bcapital return or capital reduction only as a screen\b")


if __name__ == "__main__":
    unittest.main()
