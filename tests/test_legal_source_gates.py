# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""Regression gates for the reviewed legal and tax source boundaries."""

from __future__ import annotations

import json
import unittest
from fractions import Fraction
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS = REPOSITORY / ".claude" / "skills"


def skill_text(name: str) -> str:
    return (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")


class LegalSourceGateTests(unittest.TestCase):
    def test_coal_wages_preserve_the_overtime_floor_and_employee_categories(self) -> None:
        text = skill_text("coal-lsl-levy")
        self.assertIn("75% of the combined total of Formula A, overtime or penalty rates", text)
        self.assertIn("Use the greater result each month", text)
        self.assertIn("For an annual salary", text)
        self.assertIn("casual periods from 1 January 2024", text)
        self.assertIn("an insurer or other source", text)
        self.assertIn("that source reimburses the employer", text)
        self.assertIn("the employer pays the employee normally", text)
        self.assertIn("every payroll week ending in the reporting month", text)
        self.assertIn("each week's start date and hours", text)
        self.assertNotIn("so they can be excluded", text)

    def test_coal_exit_status_does_not_erase_worked_hours(self) -> None:
        text = skill_text("coal-lsl-levy")
        self.assertIn("Preserve weekly hours worked before cessation or leave", text)
        self.assertIn("annual leave retains normal hours", text)
        self.assertIn("leaving weeks outside the reporting period blank", text)
        self.assertNotIn("relevant status code and zero hours", text)

    def test_contractual_deadlines_retain_their_units(self) -> None:
        text = skill_text("progress-claim-preparation")
        self.assertIn("actual unit or fixed date", text)
        self.assertIn("14(4)(b)(i)", text)
        self.assertIn("73(1)(a) and 76(1)(a)", text)
        self.assertNotIn("Every period in this step runs in business days", text)

    def test_qld_retention_notices_opening_and_transfer_keep_their_conditions(self) -> None:
        text = skill_text("retention-schedule")
        for rule in (
            "s 34(2)(b) allows 20 business days",
            "Section 35(2)",
            "Section 34B requires commissioner notice",
            "s 40(4) allows 5 business days after opening",
            "deposit-notice exception in s 40A(3)",
            "Section 51 requires the trustee to deposit the shortfall immediately",
            "ss 34A(4)(b) and 34C",
            "s 37A(3) preserves that exception",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, text)

    def test_retention_financing_exception_requires_both_conditions(self) -> None:
        text = skill_text("retention-schedule")
        self.assertIn("both a reason other than financing", text)
        self.assertIn("proportionate to that reason", text)
        self.assertIn("assess paras 60 and 61", text)
        self.assertIn("one-year practical expedient", text)
        self.assertIn("before 1 July 2026", text)
        self.assertNotIn("para 62(c) takes it out", text)

    def test_rollback_requires_an_available_replacement_before_uninstall(self) -> None:
        text = (REPOSITORY / "docs/HARDHAT-CONSOLIDATION.md").read_text(encoding="utf-8")
        self.assertIn("publicly unavailable", text)
        self.assertIn("Do not\nuninstall a working destination pack until", text)
        self.assertIn("obtained and verified", text)
        self.assertNotIn("that release and its tags stay\navailable", text)

    def test_xero_export_rules_preserve_observed_schema_and_au_bas_scope(self) -> None:
        text = skill_text("xero-exports")
        self.assertIn("direct references and arithmetic", text)
        self.assertIn("Accept either an empty cell or numeric `0`", text)
        self.assertIn("grouped by BAS field, with no `Net` column", text)
        self.assertIn("retrieves a specific published BAS", text)
        self.assertIn("Check whether voluntary-agreement payments are included", text)
        self.assertNotIn("It will not carry the voluntary-agreement component", text)

    def test_nsw_payroll_nexus_starts_with_monthly_service_locations(self) -> None:
        text = skill_text("payroll-tax-contractors")
        self.assertIn("services performed wholly in NSW", text)
        self.assertIn("s 11(1)(a)", text)
        self.assertIn("s 11(1)(b)", text)
        self.assertIn("s 11(1)(c)", text)
        self.assertIn("s 11(4) and (5)", text)
        self.assertNotIn("fixed order starting with the worker's principal place of residence", text)

    def test_nsw_payroll_exemptions_use_the_current_section_32(self) -> None:
        # These exclusions constrain the NSW workflow, not other jurisdictions'
        # own statutory lists in the separate routing table.
        text = skill_text("payroll-tax-contractors").split("## Other states and territories", 1)[0]
        self.assertIn("owner-driver conveyance (s 32(2)(d), PTA 006", text)
        self.assertNotIn("insurance procurement", text)
        self.assertNotIn("door-to-door sale", text)
        self.assertNotIn("s 32(2)(d)(ii)", text)
        self.assertNotIn("s 32(2)(d)(iii)", text)

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
        self.assertIn("charge percentage verified for that payment", text)
        self.assertIn("rounding rule from the SGAA compilation", text)
        self.assertIn("return `UNKNOWN` without calculating", text)
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
        self.assertIn("2 or more payments on the same QE day", text)
        self.assertIn("sum their s 10A(6)-adjusted amounts", text)
        self.assertIn("QE-day total once by the charge percentage verified for that payment", text)

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
        revision = "a5a56e5e126c6d8eabb6341cbba2f2a18e0c3d7b"

        self.assertIn(f"https://github.com/ryanduguid/australian-accounting/tree/{revision}/packages/the-wip-tally", text)
        self.assertIn("wip-tally schedule", text)
        # The engine is a Rust binary now; pip installs only the retired Python package.
        self.assertIn(
            f"cargo install --locked --root <tool-dir> --git https://github.com/ryanduguid/australian-accounting --rev {revision} the-wip-tally",
            text,
        )
        self.assertNotIn("pip install", text)
        # Other builds also report 1.0.0, so the pinned binary runs by path, never from PATH.
        self.assertIn("`cargo install --list --root <tool-dir>`", text)
        self.assertIn("never a `wip-tally` found on `PATH`", text)
        # The engine refuses a blank outcome_reasonably_measurable instead of assuming yes.
        self.assertIn("State `outcome_reasonably_measurable` as `yes` or `no` on every row", text)
        self.assertIn("Do not invent WIP arithmetic", text)
        self.assertIn("Do not invent the cost-to-cost ratio", text)

    def test_aml_coverage_routes_firm_address_matches_to_the_compliance_officer(self) -> None:
        text = skill_text("au-aml-ctf-client-coverage")

        self.assertIn("each client's recorded registered office and principal place of business addresses", text)
        self.assertIn("the firm's own street addresses", text)
        self.assertIn("fill a firm address field for every client", text)
        self.assertIn("as an item 9 designated service", text)
        self.assertIn("Route every `yes` and `UNVERIFIED` to the AML/CTF compliance officer", text)
        self.assertIn("even where the firm's assessment lists no address service", text)
        self.assertIn("using a firm address", text)

    def test_aml_coverage_needs_evidence_for_each_beneficial_owner(self) -> None:
        text = " ".join(skill_text("au-aml-ctf-client-coverage").split())
        start = text.index("3. Split the clients receiving a designated service")
        step = text[start : text.index("4. For every client receiving a designated service", start)]

        self.assertIn("Test beneficial owner evidence owner by owner.", step)
        self.assertIn("In the Act and Rules as read on 4 November 2026", step)
        self.assertIn("(s 28(2)(d) and (e) of the *Anti-Money Laundering and Counter-Terrorism Financing Act 2006*)", step)
        # A recorded Rules basis is applied, within its scope, before any owner is tested.
        basis = step.index("First record any basis the register gives, and who recorded it,")
        per_owner = step.index("For each beneficial owner the register or its recorded ownership and control structure lists")
        self.assertLess(basis, per_owner)
        self.assertIn("apply it to the owners within its scope whether or not owners are listed", step)
        self.assertIn("is covered for every beneficial owner (s 6-7(1), (1A) and (1B))", step)
        self.assertIn("covers only an individual who is a beneficial owner solely through that part (s 6-7(1C))", step)
        self.assertIn(
            "s 6-17 covers the matter only if the customer's ML/TF risk has been identified from KYC information "
            "reasonably available before it began providing the designated service, KYC information about the matter "
            "appropriate to that risk has been collected and there are no reasonable grounds to doubt that information's "
            "adequacy or veracity (s 6-17(a), (c), (d) and (e))",
            step,
        )
        self.assertIn(
            "Route to the AML/CTF compliance officer any recorded basis that names no decision-maker, does not record "
            "each condition of the provision it cites or rests on KYC information that the register's own records "
            "contradict, and carry the owners it would cover as unresolved, not as covered.",
            step,
        )
        self.assertIn("s 6-18 covers it where the customer is, or is controlled by,", step)
        self.assertIn("as established; s 6-17 does not.", step)
        self.assertIn(
            "record a verification evidence reference unless a recorded basis covers that owner's identity, "
            "and a screening date unless the register records that s 6-7(2) or s 6-18(2) covers that owner's screening",
            step,
        )
        self.assertIn("identified by its position in the register (such as owner 2 of 3), not by name", step)
        self.assertIn("record each owner a basis covers as covered by it, not as missing", step)
        self.assertIn("at least one piece of KYC information verified for each matter", step)
        self.assertIn("Where the register lists no beneficial owner and records no basis under s 6-7, s 6-17 or s 6-18", step)
        self.assertIn("with neither, the beneficial owner evidence is missing", step)
        self.assertIn("Do not decide whether a basis applies or extend it beyond its recorded scope", step)
        self.assertNotIn("Where the register lists no beneficial owner, record the basis it gives", step)
        self.assertIn("A screening or verification vendor's entity-level `complete` status is not this evidence", step)
        self.assertIn("Section 111(3) of the Act requires records", step)
        self.assertIn("remains responsible for complying with the Act and Rules", step)
        self.assertIn("Record the vendor status beside the per-owner result, never in place of it.", step)

        sources = SKILLS / "au-aml-ctf-client-coverage" / "sources.json"
        recorded = {s["url"] for s in json.loads(sources.read_text(encoding="utf-8"))["sources"]}
        for url in (
            "https://www.austrac.gov.au/industry-and-business/obligations-and-guidance/your-amlctf-program/"
            "customer-due-diligence/initial-customer-due-diligence/overview-initial-customer-due-diligence",
            "https://www.austrac.gov.au/industry-and-business/obligations-and-guidance/your-amlctf-program/"
            "customer-due-diligence/initial-customer-due-diligence/initial-customer-due-diligence-guides-"
            "customer-type/initial-cdd-trust",
            "https://www.austrac.gov.au/industry-and-business/obligations-and-guidance/additional-guidance/"
            "using-outsourcing-help-meet-your-obligations",
            "https://www.legislation.gov.au/F2025L01026/latest",
        ):
            self.assertIn(f"]({url})", text)
            self.assertIn(url, recorded)

        card = (REPOSITORY / "validation" / "cases" / "au-aml-ctf-client-coverage-beneficial-owner-evidence.md")
        card_text = card.read_text(encoding="utf-8")
        self.assertIn("  - au-aml-ctf-client-coverage\n", card_text)
        self.assertIn("Do not mark H1 complete on the vendor's status.", card_text)

        card = (REPOSITORY / "validation" / "cases" / "au-aml-ctf-client-coverage-recorded-exception-scope.md")
        card_text = " ".join(card.read_text(encoding="utf-8").split())
        self.assertIn("- au-aml-ctf-client-coverage", card_text)
        self.assertIn("not as missing elements, although both are listed", card_text)
        self.assertIn("Do not extend J2's recorded basis to owner 2 of 2.", card_text)

        card = (REPOSITORY / "validation" / "cases" / "au-aml-ctf-client-coverage-contradictory-kyc-basis.md")
        card_text = " ".join(card.read_text(encoding="utf-8").split())
        self.assertIn("- au-aml-ctf-client-coverage", card_text)
        self.assertIn("Route K1's recorded basis to the compliance officer because the ownership summary it relies on contradicts", card_text)
        # K3 is covered only because its basis records every s 6-17 condition, including (a).
        self.assertIn("also recorded that s 31 of the Act permits simplified customer due diligence for all 3 clients", card_text)
        self.assertIn("Do not record K1's or K2's owners as covered, or mark either client complete, on its recorded basis.", card_text)

    def test_bas_purchases_test_import_gst_coded_to_cost(self) -> None:
        text = " ".join(skill_text("bas-preparation").split())
        start = text.index("5. **Review coding exceptions.**")
        step = text[start : text.index("6. **Variance check.**", start)]

        self.assertIn("Then test import GST on broker and courier invoices.", step)
        self.assertIn("coded to a cost account with no GST credit. Each is a possible missed credit, not a finding.", step)
        self.assertIn("As read on 4 November 2026, the ATO's [GST and imported goods]", step)
        self.assertIn("the finalised import declaration (N10, or N30 for goods cleared out of a warehouse)", step)
        self.assertIn("completes the customs formalities, itself or through a broker or agent (paragraphs 49 and 54)", step)
        self.assertIn("does not import them (paragraph 56)", step)
        self.assertIn("the named owner acted as its agent (paragraph 292)", step)
        self.assertIn("in which the GST on the importation was paid, even where the broker paid it and the entity reimbursed it later", step)
        # Deferred GST is reconciled, never offset in full by default.
        self.assertIn("whose deferred GST the ATO pre-fills at label 7A of the monthly BAS", step)
        self.assertIn("Reconcile that amount to the import declarations, and propose at 1B for the same period only the credit the evidence establishes (paragraph 291)", step)
        self.assertIn("says to claim the full deferred amount where the entity is entitled to a full credit", step)
        self.assertIn("carries a smaller credit (paragraph 18), and a portion the evidence does not establish stays unresolved", step)
        self.assertNotIn("test that match instead", step)
        self.assertIn("Take no second credit from a broker invoice", step)
        # Another importer is excluded only when it imported on its own account.
        self.assertIn("goods another entity imported on its own account", step)
        self.assertIn("sold them to this entity after importation (paragraphs 49, 72 and 73)", step)
        self.assertIn("Where the named owner may have acted as this entity's agent, do not exclude the item", step)
        self.assertIn("a supplier's or broker's recharge that is not import GST", step)
        self.assertIn("Propose no reclassification until the evidence above is supplied", step)
        self.assertIn("Each broker or courier import GST amount coded to cost is listed", text)
        self.assertIn("label 7A reconciles to the import declarations and 1B carries only the credit the evidence establishes", text)

        sources = SKILLS / "bas-preparation" / "sources.json"
        records = {s["url"]: s for s in json.loads(sources.read_text(encoding="utf-8"))["sources"]}
        international = (
            "https://www.ato.gov.au/businesses-and-organisations/gst-excise-and-indirect-taxes/gst/"
            "in-detail/rules-for-specific-transactions/international-transactions/"
        )
        imports = (
            international + "gst-and-imported-goods",
            international + "deferred-gst",
            "https://www.ato.gov.au/law/view/document?DocID=GST/GSTR200315/NAT/ATO/00001",
        )
        for url in imports:
            self.assertIn(f"]({url})", step)
            # Pending or reviewed; test_skill_metadata checks the record's form.
            self.assertIn(url, records)
        if any(records[url].get("verification_status") == "source-discovery-only-human-review-pending" for url in imports):
            self.assertIn("Its import GST records, which step 5 cites, are discovery-only and await human review.", text)

        card = (REPOSITORY / "validation" / "cases" / "bas-preparation-import-gst-coded-to-cost.md")
        card_text = card.read_text(encoding="utf-8")
        self.assertIn("  - bas-preparation\n", card_text)
        self.assertIn("It did not act as Entity D's agent.", card_text)
        self.assertIn("Exclude S-1's 80.00 because the supplier imported the goods on its own", card_text)
        deferred = (REPOSITORY / "validation" / "cases" / "bas-preparation-deferred-gst-partly-creditable.md")
        deferred_text = deferred.read_text(encoding="utf-8")
        self.assertIn("  - bas-preparation\n", deferred_text)
        self.assertIn("Leave declaration B's credit unresolved", deferred_text)
        self.assertIn("Do not propose the full 500.00 at 1B because it matches label 7A.", deferred_text)

    def test_tax_invoice_threshold_is_a_value_test_excluding_gst(self) -> None:
        act = "https://www.legislation.gov.au/C2004A00446/latest/text"
        regulations = "https://www.legislation.gov.au/F2019L00417/latest/text"
        ruling = "https://www.ato.gov.au/law/view/document?docid=GST/GSTR20131/NAT/ATO/00001"
        references = SKILLS / "bas-preparation" / "references" / "transaction-gst-review.md"
        surfaces = {
            "tax-invoice-review": " ".join(skill_text("tax-invoice-review").split()),
            "au-bookkeeping": " ".join(skill_text("au-bookkeeping").split()),
            "bas-preparation": " ".join(references.read_text(encoding="utf-8").split()),
        }
        for skill, text in surfaces.items():
            with self.subTest(skill=skill):
                self.assertIn("$75", text)
                self.assertIn("$82.50", text)
                self.assertRegex(text, r"\$75,? excluding GST|does not exceed \$75")
                self.assertRegex(text, r"\$82\.50 including GST")
                self.assertIn("for most supplies", text)
                self.assertIn("aggregate value", text)
                self.assertIn("taxable part", text)
                self.assertIn("(GSTR 2013/1, paragraph 58)", text)
                self.assertIn("s 29-80(1)", text)
                self.assertIn("s 29-80.01", text)
                self.assertRegex(text, r"[Hh]uman review pending")
                self.assertNotIn("$82.50 threshold", text)
                self.assertNotRegex(text, r"\$82\.50 excluding GST|\$75 including GST")
                recorded = {
                    s["url"]
                    for s in json.loads((SKILLS / skill / "sources.json").read_text(encoding="utf-8"))["sources"]
                }
                for url in (act, regulations, ruling):
                    self.assertIn(f"]({url})", text)
                    self.assertIn(url, recorded)

        step = surfaces["tax-invoice-review"]
        self.assertIn("a recipient can claim a credit without a tax invoice", step)
        self.assertIn("a supplier need not give one on request", step)
        self.assertIn("the price times 10/11 (s 9-75(1))", step)
        self.assertIn("work out the value of the taxable part (s 9-80)", step)
        self.assertIn("A credit at or under the threshold still needs a record", step)
        self.assertIn("An authorised human decides", step)

        bookkeeping = surfaces["au-bookkeeping"]
        self.assertIn("work out the value of the taxable part (s 9-80)", bookkeeping)
        self.assertIn("A purchase at or below the threshold still needs a receipt or other record", bookkeeping)
        self.assertIn("Whether the credit is claimable stays with the BAS workflow and the reviewer", bookkeeping)
        self.assertNotIn("A smaller purchase", bookkeeping)

        screen = surfaces["bas-preparation"]
        self.assertIn("| Missing record | A credit is claimed at or below the Missing document value", screen)
        self.assertIn("a missing record, not a missing tax invoice", screen)
        self.assertRegex(screen, r"A hit is a lead for a review unit, never a finding")

        card = (REPOSITORY / "validation" / "cases" / "tax-invoice-review-low-value-threshold.md")
        card_text = " ".join(card.read_text(encoding="utf-8").split())
        self.assertIn("- tax-invoice-review", card_text)

        # Independent figures: GSTR 2013/1 footnotes 39 and 44 pair a value of $75 with a
        # price of $82.50, and its Example 3 shows total GST of $7.30 on a sale of $85.30.
        # Value is price times 10/11 (s 9-75(1)), and the threshold allows exactly $75.
        def value(price: str) -> Fraction:
            return Fraction(price) * Fraction(10, 11)

        self.assertEqual(value("82.50"), 75)
        self.assertEqual(value("77.00"), 70)
        self.assertEqual(value("83.60"), 76)
        self.assertEqual(value("49.50") * 2, 90)
        self.assertEqual(value("80.30"), 73)
        self.assertEqual(Fraction("7.30") * 10, 73)
        self.assertEqual(value("55.00"), 50)
        self.assertEqual(Fraction("5.00") * 10, 50)
        for finding in (
            "P-1 has a value of 70.00",
            "P-2 has a value of 75.00, which does not exceed the threshold",
            "P-3 has a value of 76.00, which exceeds the threshold",
            "P-4 has an aggregate value of 90.00, which exceeds the threshold",
            "P-5 has an aggregate value of 73.00, which does not exceed the threshold",
            "P-5's amounts are adapted from GSTR 2013/1 Example 3",
            "| P-6 | One taxable item | 55.00 | 5.00 | None |",
            "no record of any kind for P-6",
            "P-6 needs no tax invoice but has no record, so keep its credit unresolved with the record needed "
            "and reviewer action",
            "Do not treat a purchase under the threshold as needing no record",
            "Do not decide whether a credit is claimable",
            "An authorised human makes the legal, tax and accounting decisions",
        ):
            self.assertIn(finding, card_text)

    def test_contractor_labour_split_cites_sgd_2026_d1_as_a_draft(self) -> None:
        text = skill_text("contractor-super-tpar")

        self.assertIn("SGD 2026/D1 gives the ATO's preliminary view of s 10A(1)(d)", text)
        self.assertIn("reasonable market value of the labour", text)
        self.assertIn("It is a draft: check whether a final determination has issued", text)
        self.assertIn("DocID=DSD/SGD2026D1/NAT/ATO/00001", text)
        self.assertIn("dated 2 September 2026", text)
        self.assertIn("a reasonably accurate estimate of market value", text)

    def test_div7a_flags_upes_on_loan_terms_and_prior_deemed_dividends(self) -> None:
        text = skill_text("div7a-compliance")

        self.assertIn("made subject to complying loan terms", text)
        self.assertIn("does not reinstate a satisfied or converted entitlement as a mere UPE ([34], [38])", text)
        self.assertIn("gives rise to a loan within s 109D(3) is treated as one", text)
        self.assertIn("seek an amendment within the amendment period or object outside it", text)
        self.assertIn("([40]-[42])", text)
        self.assertIn("do not decide whether to request an amendment or object", text)
        self.assertIn("trustee resolutions, accounting records and later dealings with the entitlement", text)


if __name__ == "__main__":
    unittest.main()
