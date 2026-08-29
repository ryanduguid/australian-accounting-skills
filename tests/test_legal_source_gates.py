"""Regression gates for the reviewed legal and tax source boundaries."""

from __future__ import annotations

import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS = REPOSITORY / ".claude" / "skills"


def skill_text(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


class LegalSourceGateTests(unittest.TestCase):
    def test_nsw_mining_coverage_uses_primary_act_and_judgment(self) -> None:
        text = skill_text("progress-claim-preparation")

        self.assertIn(
            "https://legislation.nsw.gov.au/view/whole/html/inforce/current/act-1999-046",
            text,
        )
        self.assertIn(
            "https://www.caselaw.nsw.gov.au/decision/175b4bf54ee486b38a0338e5",
            text,
        )
        self.assertIn("s 5(2)(b)", text)
        self.assertIn("[101]-[112]", text)
        self.assertIn("[147]-[150]", text)
        self.assertIn("construction lawyer", text)
        self.assertIn("do not authorise an autonomous coverage conclusion", text)
        self.assertNotIn("Every NSW section number below comes from", text)
        self.assertNotIn("Commentary on Cadia", text)

    def test_nsw_retention_rule_preserves_guidance_conflict(self) -> None:
        text = skill_text("retention-schedule")

        self.assertIn(
            "https://legislation.nsw.gov.au/view/whole/html/inforce/current/act-1999-046",
            text,
        )
        self.assertIn(
            "https://legislation.nsw.gov.au/view/whole/html/inforce/current/sl-2020-0504",
            text,
        )
        self.assertIn(
            "https://www.nsw.gov.au/housing-and-construction/compliance-and-regulation/"
            "security-of-payment/retention-money",
            text,
        )
        self.assertIn("10 business days", text)
        self.assertIn("14 days", text)
        self.assertIn("cl 9(3)", text)
        self.assertIn("cl 20A", text)
        self.assertIn("1 July 2019", text)
        self.assertIn("in-force instrument as the controlling source", text)
        self.assertIn(
            "Never direct or authorise a withdrawal from a statutory trust account",
            text,
        )
        self.assertNotIn("its text was not read", text)
        self.assertNotIn("annual account review report survives is unresolved", text)

    def test_contractor_skill_uses_current_statutory_pathways(self) -> None:
        text = skill_text("contractor-super-tpar")

        required_sources = (
            "https://www.legislation.gov.au/C2004A04402/latest/text",
            "https://www.legislation.gov.au/C2025A00057/latest/text",
            "https://www.legislation.gov.au/C1953A00001/latest/text",
            "https://www.legislation.gov.au/F2019L00864/latest/text",
            "https://www.legislation.gov.au/F2017L01227/latest/text",
            "https://www.ato.gov.au/law/view/document?docid=TXR/TR20234/NAT/ATO/00001",
            "https://www.ato.gov.au/law/view/document?docid=SGR/SGR20052/NAT/ATO/00001",
            "https://www.ato.gov.au/law/view/document?docid=PSR/PS201115/NAT/ATO/00001",
            "https://softwaredevelopers.ato.gov.au/TPRS",
        )
        for source in required_sources:
            with self.subTest(source=source):
                self.assertIn(source, text)

        self.assertIn("s 10A(1)(d)", text)
        self.assertIn("1 July 2026", text)
        self.assertIn("Schedule 1 Division 405", text)
        self.assertIn("reg 70", text)
        self.assertIn("at least half", text)
        self.assertIn("materials-only supply", text)
        self.assertIn("no mechanical percentage", text)
        self.assertIn("genuine contract only with an interposed entity", text)
        self.assertIn("Do not conclude that a worker is or is not an employee", text)
        self.assertIn("Do not lodge the TPAR", text)
        self.assertNotIn("Building and construction is not in the Act at all", text)
        self.assertNotIn("whether payday super has commenced", text)
        self.assertNotIn("The worker carries the onus", text)

    def test_tr_2023_4_title_and_withdrawal_history_are_current(self) -> None:
        text = skill_text("contractor-super-tpar")

        self.assertIn(
            "TR 2023/4, *Income tax and superannuation guarantee: "
            "who is an employee?*",
            text,
        )
        self.assertIn("withdrawn with effect from 26 June 2024", text)
        self.assertIn("incorporated in Appendix 2 of TR 2023/4", text)
        self.assertNotIn(
            "Income tax: pay as you go withholding - who is an employee?",
            text,
        )

    def test_post_payday_super_calculation_is_bounded_and_reviewable(self) -> None:
        text = skill_text("contractor-super-tpar")

        self.assertIn("s 10A(5)", text)
        self.assertIn("s 10A(6)", text)
        self.assertIn("maximum contributions base", text)
        self.assertIn("in relation to this employer", text)
        self.assertIn("Under s 17A(2)", text)
        self.assertIn("12% charge percentage", text)
        self.assertIn("seventh business day", text)
        self.assertIn("20th business day", text)
        self.assertIn("ss 18A and 18B", text)
        self.assertIn("s 18C(2)", text)
        self.assertIn("s 18C(3)", text)
        self.assertIn("s 18C(4)", text)
        self.assertIn(
            "It does not calculate the final individual shortfall",
            text,
        )
        self.assertIn(
            "The SG amount and contribution-period screen is not a final "
            "obligation or charge calculation",
            text,
        )

    def test_post_payday_super_same_day_payments_are_aggregated_after_cap(self) -> None:
        text = skill_text("contractor-super-tpar")

        self.assertIn("each payment in its actual payment order", text)
        self.assertIn("two or more payments on the same QE day", text)
        self.assertIn("sum their s 10A(6)-adjusted amounts", text)
        self.assertIn("QE-day total once by the 12% charge percentage", text)

    def test_post_payday_super_certificate_sets_nil_only_with_evidence(self) -> None:
        text = skill_text("contractor-super-tpar")

        self.assertIn("Apply s 17B before returning the amount", text)
        self.assertIn("treat the QE-day payments as nil", text)
        self.assertIn("nil individual superannuation guarantee amount", text)
        self.assertIn("Commissioner-issued certificate", text)
        self.assertIn("s 17D notice and enclosed copy", text)
        self.assertIn("specified employer and period", text)
        self.assertIn("do not infer a certificate", text)

    def test_s18c_longer_period_items_keep_their_distinct_deadlines(self) -> None:
        text = skill_text("contractor-super-tpar")

        self.assertIn("The standard receipt periods are the **usual period**", text)
        self.assertIn("12-month period ending on the day before the QE day", text)
        self.assertIn("do not call them all the extended usual period", text)
        self.assertIn("Item 1 uses the **extended usual period**", text)
        self.assertIn("after the employer ceased making", text)
        self.assertIn("Item 2 applies", text)
        self.assertIn("first standard QE day after the current QE day", text)
        self.assertIn("Item 3 applies", text)
        self.assertIn("starting on the day after the determination is made", text)
        self.assertIn("Item 4 applies", text)
        self.assertIn("earlier contribution's latest due day", text)
        self.assertNotIn("ordinary or applicable extended contribution period", text)

    def test_tpar_turnover_exemption_stays_scoped_to_items_11_to_14(self) -> None:
        text = skill_text("contractor-super-tpar")

        self.assertIn("F2019L00864", text)
        self.assertIn("less than 10%", text)
        self.assertIn("current GST turnover", text)
        self.assertIn("projected GST turnover", text)
        self.assertIn(
            "transaction must not be described in another s 396-55 table item",
            text,
        )
        self.assertIn("entity must not have chosen to report", text)
        self.assertIn("Giving a report for the transaction", text)
        self.assertIn(
            "does not exempt Division 405 building-and-construction reporting",
            text,
        )

    def test_tpar_reporting_clocks_preserve_their_authority(self) -> None:
        text = skill_text("contractor-super-tpar")

        self.assertIn("default time is the 31st day after the period", text)
        self.assertIn("by legislative instrument", text)
        self.assertIn("s 388-55", text)
        self.assertIn("s 405-10(1)", text)
        self.assertIn("within 21 days after each quarter", text)
        self.assertIn("s 405-10(4)", text)
        self.assertIn("by written notice", text)
        self.assertIn("PS LA 2011/15", text)
        self.assertIn("annual TPAR with a 28 August due date", text)
        self.assertIn(
            "practice statement is not the operative written notice",
            text,
        )

    def test_s388_55_deferral_is_general_and_does_not_replace_405_notice(self) -> None:
        text = skill_text("contractor-super-tpar")

        self.assertIn("Section 388-55 is a separate general power", text)
        self.assertIn("can apply to either reporting pathway", text)
        self.assertIn("paragraph 396-55(a)", text)
        self.assertIn("s 405-10(2)", text)
        self.assertIn("s 405-10(4) written notice", text)
        self.assertIn("plus any s 388-55 deferral", text)
        self.assertIn("practice statement as a notice or deferral", text)

    def test_source_review_records_scope_and_no_client_data(self) -> None:
        review = (
            REPOSITORY / "docs" / "source-review-2026-08-15.md"
        ).read_text(encoding="utf-8")

        self.assertIn("## Scope and decision boundary", review)
        self.assertIn("## Controlling source order", review)
        self.assertIn("## NSW security of payment coverage", review)
        self.assertIn("## NSW retention-money trusts", review)
        self.assertIn("## Contractor superannuation and reporting", review)
        self.assertIn("F2019L00864", review)
        self.assertIn("maximum contributions base", review)
        self.assertIn("s 405-10(4)", review)
        self.assertIn("written notice", review)
        self.assertIn("26 June 2024", review)
        self.assertIn("No client records, identifiers or credentials were used", review)

    def test_wip_skill_names_the_wip_tally_engine(self) -> None:
        text = skill_text("wip-over-under-billing")

        self.assertIn("https://github.com/ryanduguid/TheWIPTally", text)
        self.assertIn("wip-tally schedule", text)
        self.assertIn("Do not invent WIP arithmetic", text)
        self.assertIn("Do not invent the cost-to-cost ratio", text)


if __name__ == "__main__":
    unittest.main()
