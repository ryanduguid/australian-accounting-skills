# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The SMSF death benefit, family trust election and dividend preparation workflows
added on 11 November 2026 keep their key rules.

As in test_practice_workflows.py, each test reads one numbered workflow step and
checks the authorities, conditions, cut-offs and prohibitions it must carry, not
its wording. The assertion helpers are that file's, reused rather than copied.
"""

from __future__ import annotations

import unittest

import test_practice_workflows as practice
from skill_prose import DO_NOT, NOT, SKILLS, section, workflow_step

CASES = SKILLS.parents[1] / "validation" / "cases"
ATO_SMSF = "https://www.ato.gov.au/individuals-and-families/super-for-individuals-and-families/self-managed-super-funds-smsf"


class EntitySuperWorkflowTests(unittest.TestCase):
    assert_carries = practice.PracticeWorkflowTests.assert_carries
    assert_sentence = practice.PracticeWorkflowTests.assert_sentence
    assert_prohibited = practice.PracticeWorkflowTests.assert_prohibited
    assert_routes = practice.PracticeWorkflowTests.assert_routes
    assert_cited_and_recorded = practice.PracticeWorkflowTests.assert_cited_and_recorded

    # au-smsf-death-benefits

    def test_death_benefits_cite_the_restructure_rules(self) -> None:
        step = workflow_step("au-smsf-death-benefits", 1)
        self.assert_sentence(step, r"\bs 17A\(3\)\(a\)", r"\blegal personal representative may be a trustee\b",
                             r"\buntil death benefits commence to be payable\b")
        self.assert_sentence(step, r"\bs 17A\(4\)", r"\bearlier of an RSE licensee's appointment and 6 months\b")

    def test_death_benefits_test_nominations_against_the_deed(self) -> None:
        step = workflow_step("au-smsf-death-benefits", 2)
        # SMSFD 2008/3: the statutory nomination rules do not bind an SMSF; the deed does.
        self.assert_sentence(step, r"\bSMSFD 2008/3\b", r"\bs 59\b", r"\breg 6\.17A\b",
                             NOT + r"apply to SMSFs\b")
        self.assert_sentence(step, NOT + r"binding to the extent it names a person who cannot receive a benefit\b")
        # Only where the deed adopts reg 6.17A are its witness and lapse rules tested.
        self.assert_sentence(step, r"\bWhere the deed adopts reg 6\.17A\b", r"\breg 6\.17A\(6\)",
                             r"\b2 adult witnesses who are not named in it\b", r"\breg 6\.17A\(7\)",
                             r"\blapse 3 years after it was signed, last confirmed or amended\b")
        self.assert_sentence(step, r"\blegal question for the trustee's lawyer\b",
                             DO_NOT + r"conclude on it\b")
        # The High Court settled the point; SMSFD 2008/3 is not left to carry it alone.
        self.assert_sentence(step, r"\bHill v Zuda Pty Ltd\b", r"\breg 6\.17A has no application to an SMSF\b",
                             r"\[4\], \[12\] and \[30\]", r"\bs 55A still applies\b", r"\[33\]")

    def test_death_benefits_keep_sis_and_tax_dependants_apart(self) -> None:
        step = workflow_step("au-smsf-death-benefits", 3)
        self.assert_carries(step, "reg 6.22(2)", "reg 6.22(3)", "Section 10(1)", "s 302-195", "s 302-200",
                            "s 302-195(2)", "line of duty")
        self.assert_sentence(step, r"\bseparate columns\b", r"\bSIS dependant status\b",
                             r"\bdeath benefits dependant status\b")
        self.assert_sentence(step, r"\bAn adult child can be a SIS dependant without being a death benefits dependant\b")
        self.assert_sentence(step, r"\ba former spouse is a death benefits dependant under s 302-195\(1\)\(a\)", NOT + r"a SIS dependant as a spouse\b",
                             r"\bSMSFD 2008/3 \(paragraph 31\)")
        self.assert_sentence(step, DO_NOT + r"decide who is paid or how much\b",
                             affirmed=(r"\bthe trustee decides under the deed\b",))

    def test_death_benefits_limit_income_streams_and_reversion(self) -> None:
        step = workflow_step("au-smsf-death-benefits", 4)
        self.assert_carries(step, "reg 6.21(2)", "reg 6.21(2A)", "reg 6.21(2B)", "reg 6.21(2C)", "TR 2013/5",
                            "paragraph 29", "paragraph 126", "paragraph 127")
        # The child conditions are alternatives, each with its own age limit.
        self.assert_sentence(step, r"\bunder 18, or was financially dependent on the member and under 25, or has a disability\b")
        self.assert_sentence(step, r"\bceases on the member's death unless\b", r"\bautomatically transfer\b")
        self.assert_sentence(step, r"\bcannot be retained in accumulation phase\b")
        self.assert_sentence(step, r"\breg 6\.21\(2B\)", r"\bunless it is rolled over to commence a new annuity or pension\b", r"\bwhichever is earlier\b")

    def test_death_benefits_defer_a_reversionary_credit(self) -> None:
        step = workflow_step("au-smsf-death-benefits", 5)
        self.assert_carries(step, "s 294-25(1) item 2")
        # Child recipients are Subdivision 294-E; 294-D is capped defined benefit income streams.
        self.assert_sentence(step, r"\bSubdivision 294-E modifies the cap for a child recipient\b")
        self.assertNotIn("294-D", step)
        self.assert_sentence(step, r"\breversionary beneficiary\b",
                             r"\bat the end of the 12 months beginning on the starting day\b")
        self.assert_sentence(step, r"\bdeath itself is not reported\b", r"\bdate of death as the effective date\b")
        self.assert_routes(step, 1)

    def test_death_benefits_record_components_without_computing_tax(self) -> None:
        step = workflow_step("au-smsf-death-benefits", 6)
        self.assert_carries(step, "s 307-125", "s 307-290", "s 295-465", "s 295-470", "s 302-60", "s 302-145",
                            "ss 302-65 to 302-90", "s 302-10")
        self.assert_sentence(step, r"\bleave the element blank until each input is evidenced\b")
        self.assert_sentence(step, r"\bcommuting an income stream\b", r"\bwhen that income stream commenced\b",
                             r"\(s 307-125\(3\)\(c\)\)")
        self.assert_sentence(step, r"\bwithout computing their tax\b")
        # A benefit from a pension that did not revert keeps that pension's proportions:
        # s 307-125(4)(a) displaces the payment-date rule for the method in s 307-125.02.
        self.assert_sentence(step, r"\bs 307-125\(4\)\(a\)", r"\bs 307-125\.02\b", r"\bdid not automatically revert\b",
                             r"\bother than investment earnings\b", r"\bself-insurance amounts arising on or after the death\b",
                             r"\bwhen the original income stream commenced\b")
        self.assert_routes(step, 1)

    def test_death_benefits_adult_child_interdependency_stays_open(self) -> None:
        # Financial independence rules out s 302-195(1)(b) and (d), not an interdependency
        # relationship under (1)(c), so neither the example nor the card may settle it.
        example = section("au-smsf-death-benefits", "Fabricated acceptance example")
        card = " ".join((CASES / "au-smsf-death-benefits-reversionary-and-nomination.md").read_text(encoding="utf-8").split())
        for text in (example, card):
            self.assert_sentence(text, r"\bSIS dependant\b", r"`UNVERIFIED` under s 302-195\(1\)\(c\)",
                                 r"\binterdependency\b")
            self.assertNotRegex(text, r"\bbut not\b[^.]*\ba death benefits dependant\b")

    def test_death_benefits_timeline_does_not_judge_lateness(self) -> None:
        step = workflow_step("au-smsf-death-benefits", 7)
        self.assert_sentence(step, r"\breg 6\.21\(1\)", r"\bas soon as practicable after the death\b")
        self.assert_sentence(step, r"\bsets no number of days\b", DO_NOT + r"conclude the payment was late\b")
        self.assert_sentence(step, r"\bwithin 14 days of a lump sum\b", r"\bby 14 July after the year for an income stream\b")

    def test_death_benefit_sources_are_pending(self) -> None:
        self.assert_cited_and_recorded(
            "au-smsf-death-benefits",
            "https://www.legislation.gov.au/C2004A04633/latest/text",
            "https://www.legislation.gov.au/F1996B00580/latest/text",
            "https://www.legislation.gov.au/C2004A05138/latest/text",
            "https://www.ato.gov.au/law/view/document?DocID=SFD/SMSFD20083/NAT/ATO/00001",
            "https://www.ato.gov.au/law/view/document?DocID=TXR/TR20135/NAT/ATO/00001",
            "https://www.legislation.gov.au/F2021L00206/latest/text",
            f"{ATO_SMSF}/paying-smsf-benefits/death-of-an-smsf-member",
            f"{ATO_SMSF}/smsf-administration-and-reporting/when-to-lodge-a-transfer-balance-account-report-for-smsfs",
            f"{ATO_SMSF}/paying-smsf-benefits/payg-withholding-obligations-when-paying-super-benefits",
            "https://www.ato.gov.au/individuals-and-families/super-for-individuals-and-families/super/"
            "withdrawing-and-using-your-super/superannuation-death-benefits",
            "https://www.hcourt.gov.au/sites/default/files/eresources/2022/HCA/21.pdf",
        )

    # au-family-trust-election

    def test_election_family_excludes_cousins(self) -> None:
        step = workflow_step("au-family-trust-election", 2)
        self.assert_carries(step, "s 272-95", "s 272-90", "s 272-90(2A)", "s 272-90(5)", "s 272-90(9)",
                            "parent, grandparent, brother or sister", "nephew, niece or child", "lineal descendant")
        self.assert_sentence(step, r"\bAunts, uncles and cousins\b", NOT + r"in the family under s 272-95\b")
        self.assert_sentence(step, affirmed=(r"\bThe trustee chooses the individual\b",))

    def test_election_family_control_test_counts_family_trusts(self) -> None:
        step = workflow_step("au-family-trust-election", 3)
        self.assert_carries(step, "s 272-87(1)(b)", "s 272-87(1)(c)", "paragraph (f)")

    def test_election_earlier_year_needs_both_conditions(self) -> None:
        step = workflow_step("au-family-trust-election", 4)
        # Both limbs of s 272-80(4A) run to 30 June of the year before the election.
        self.assert_sentence(
            step, r"\bs 272-80\(4A\)", r"\buntil 30 June of the income year before the one in which the election is made\b",
            r"\bpassed the family control test at all times and every conferral\b",
        )
        self.assert_carries(step, "s 272-80(10)")

    def test_election_screens_retrospective_ftdt(self) -> None:
        step = workflow_step("au-family-trust-election", 5)
        self.assert_sentence(step, r"\bs 271-15\b", r"\bincluding a time before it was made\b")
        self.assert_sentence(step, r"\bSection 271-75\(1\)\(a\)", r"\b21 days after the day the election is made\b")
        # The gap between the s 272-80(4A) period and the election date is screened on its own.
        self.assert_sentence(step, r"\bonly the period up to 30 June\b", r"\bseparately\b")
        self.assert_sentence(step, DO_NOT + r"compute or conclude the liability\b")
        self.assert_sentence(step, r"\bs 272-60\b", r"\bexceed any consideration given in return\b")
        self.assert_sentence(step, r"\bas trustee of a trust that is not in the family group \(s 271-15\(1\)\(b\)\(ii\)\)")
        self.assert_routes(step, 1)

    def test_election_iee_exposes_every_distribution(self) -> None:
        step = workflow_step("au-family-trust-election", 6)
        self.assert_carries(step, "s 272-85(1)", "s 272-87(3)", "s 272-85(4)", "(4A)", "s 272-85(6B)",
                            "s 272-90(5)", "s 272-85(7)", "ss 271-20 to 271-30")
        # The one-trust restriction ignores an IEE revoked under s 272-85(5A) or (5B).
        self.assert_sentence(step, r"\bs 272-85\(8\)", r"\brevoked under s 272-85\(5A\) or \(5B\)")
        self.assert_sentence(step, r"\bmore than half of its income or capital\b")
        self.assert_sentence(step, r"\ball of its conferrals and distributions outside the family group\b",
                             r"\bnot only amounts that came from the family trust\b")

    def test_election_records_the_limits_on_undoing_it(self) -> None:
        step = workflow_step("au-family-trust-election", 7)
        self.assert_carries(step, "s 272-80(5)", "s 272-80(5A)", "(5B)", "s 272-80(5C)", "s 272-80(6)",
                            "s 272-80(6A)", "s 272-80(8)", "s 272-85(5A) to (6)")
        self.assert_sentence(step, r"\bOne variation\b|\bone variation\b", r"\bfamily at the election commencement time\b",
                             r"\bby the trust and by each entity with an interposed entity election in relation to it\b")
        # A fixed trust's revocation has its own conditions and is made under s 272-80(7).
        self.assert_sentence(step, r"\bs 272-80\(6\)", r"\ban outsider later holds a fixed entitlement\b",
                             r"\(s 272-80\(7\)\)")
        self.assert_sentence(step, r"\bUnder s 272-80\(8\) any other variation or revocation\b")
        # The s 272-80(6A) lookback stops before the year the revocation takes effect.
        self.assert_sentence(step, r"\bs 272-80\(6A\)",
                             r"\bend of the income year before the one from which the revocation is to take effect\b")
        self.assert_sentence(step, r"\bs 272-80\(6B\)\(a\)", r"\bend of the fourth income year after the specified income year\b")
        self.assert_sentence(step, r"\blodged return cannot be amended to add a revocation or variation schedule\b")

    def test_election_card_fixes_the_iee_commencement(self) -> None:
        # Without a specified day, 'every dividend' leaves the IEE's exposure period open.
        card = " ".join((CASES / "au-family-trust-election-earlier-year.md").read_text(encoding="utf-8").split())
        self.assert_sentence(card, r"\binterposed entity election specifying the first day of income year 6\b")
        self.assert_sentence(card, r"\bs 271-30\b", r"\bs 272-85\(6B\)", r"\bincome year 3 to 5 dividends precede it\b")

    def test_election_form_pack_is_not_lodged(self) -> None:
        step = workflow_step("au-family-trust-election", 8)
        self.assert_carries(step, "s 272-80(2)", "s 272-85(2)", "s 272-80(11)", "approved form")
        self.assert_prohibited(step, r"\bmake, sign or lodge an election\b", r"\brecommend making one\b")

    def test_election_sources_are_pending(self) -> None:
        self.assert_cited_and_recorded(
            "au-family-trust-election",
            "https://www.legislation.gov.au/C1936A00027/latest/text",
            "https://www.legislation.gov.au/C2004A05138/latest/text",
            "https://www.ato.gov.au/businesses-and-organisations/trusts/family-trusts",
            "https://www.ato.gov.au/forms-and-instructions/family-trust-election-revocation-or-variation-2026-instructions",
            "https://www.ato.gov.au/forms-and-instructions/interposed-entity-election-or-revocation-2026-instructions",
        )

    # au-franking-account step 5a

    def test_dividend_preparation_keeps_the_corporate_law_conditions(self) -> None:
        step = workflow_step("au-franking-account", "5a")
        self.assert_carries(step, "s 254U", "s 254W(2)", "s 254T(2)", "s 251A(2)", "s 251A(3)",
                            "s 251A(1)(d)", "Section 202-5")
        # A sole director's dividend is a s 248B(1) resolution, not a s 248B(2) declaration.
        self.assert_sentence(step, r"\b1 director, the director passes the resolution\b", r"\(s 248B\(1\)\)")
        self.assertNotIn("251A(1)(e)", step)
        # A determined dividend is revocable until the payment time; a declared one is a debt at once.
        self.assert_sentence(step, r"\bs 254V\(1\)", r"\bonly when the time fixed for payment arrives\b",
                             r"\bcan be revoked before then\b", r"\bs 254V\(2\)", r"\ba debt when declared\b")
        # All 3 conditions of s 254T(1) are listed.
        self.assert_sentence(step, r"\bs 254T\(1\)", r"\bassets exceed its liabilities immediately before\b",
                             r"\bfair and reasonable to the shareholders as a whole\b",
                             r"\bmaterially prejudice the company's ability to pay its creditors\b")
        self.assert_sentence(step, affirmed=(r"\bThe directors decide whether the conditions are met\b",))
        self.assert_sentence(step, DO_NOT + r"draft the resolution as passed or sign anything\b")

    def test_dividend_preparation_statements_and_entries(self) -> None:
        step = workflow_step("au-franking-account", "5a")
        self.assert_carries(step, "s 202-60", "s 202-65", "s 203-30", "s 203-50", "s 203-25", "s 202-80(3)")
        self.assert_sentence(step, r"\bproposed issue date against the s 202-75 issue time\b", r"\bstep 6 checks both\b")
        self.assert_sentence(step, r"\blater issue time is not available\b",
                             r"\bcreate or increase a franking deficit tax liability \(s 202-75\(4\)\)")
        self.assert_sentence(step, r"\bon the date the distribution is made, not the resolution date\b",
                             r"\bwithout posting them\b")

    def test_dividend_preparation_routes_division_7a_set_offs(self) -> None:
        step = workflow_step("au-franking-account", "5a")
        self.assert_sentence(step, NOT + r"excluded from counting as a repayment by s 109R\(2\)", r"\(s 109R\(3\)\(a\)\)")
        # s 109ZC(2) excludes the set-off only up to the part neither franked nor franked with an
        # exempting credit; the excess stays a dividend.
        self.assert_sentence(step, r"\bs 109ZC\(2\)", r"\bexcept for franking purposes\b",
                             r"\bonly up to the part of the later dividend that is neither franked nor franked with an exempting credit\b")
        self.assert_sentence(step, r"\bany amount set off above that part is still a dividend\b")
        self.assert_routes(step, 1)

    def test_dividend_preparation_sources_are_pending(self) -> None:
        self.assert_cited_and_recorded(
            "au-franking-account",
            "https://www.legislation.gov.au/C2004A00818/latest/text",
            "https://www.legislation.gov.au/C2004A05138/latest/text",
            "https://www.legislation.gov.au/C1936A00027/latest/text",
        )


if __name__ == "__main__":
    unittest.main()
