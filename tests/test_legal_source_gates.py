# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: Apache-2.0
"""Regression gates for the reviewed legal and tax source boundaries."""

from __future__ import annotations

import json
import re
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

    #: Each pinned australian-tax-calculators release, its tagged commit and the
    #: aus-accounting-mcp release that runs it.
    RELEASES = {
        "1.0.0": ("6ac566682829731d52a1b4456708a0b9d29b5695", "0.10.0"),
        "1.1.0": ("c4a716a25f065ccc957c5db83dec711251cb4121", "0.11.0"),
        "1.2.0": ("31ecb4022aa0127ae9f672798d1d9fbfe6388e85", "0.12.0"),
        "1.4.0": ("007d4271766269f50c22d0224b94b49e70ccfd17", "0.13.0"),
    }

    #: The aus-accounting-mcp release each commit the plugin may start is.
    PLUGIN_SERVERS = {"704cbd9eb79a4608d607028c4cde67ae98b956e7": "0.13.0"}

    def test_every_pinned_calculators_release_runs_on_the_plugin_server(self) -> None:
        """Each server accepts only the calculators release it runs, so a skill pinning
        another one has every calculator call refused."""
        plugin = json.loads((REPOSITORY / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        commit = re.search(r"@([0-9a-f]{40})#", plugin["mcpServers"]["aus-accounting"]["args"][1])
        if commit is None:
            self.fail("the plugin must start aus-accounting-mcp from a pinned commit")
        server = self.PLUGIN_SERVERS.get(commit.group(1))
        self.assertIsNotNone(server, "add the plugin's aus-accounting-mcp commit to PLUGIN_SERVERS")
        accepted = {version for version, (_, runs) in self.RELEASES.items() if runs == server}
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            pins = set(re.findall(r"australian-tax-calculators/v(\d+\.\d+\.\d+)", path.read_text(encoding="utf-8")))
            for version in pins:
                with self.subTest(skill=path.parent.name, version=version):
                    self.assertIn(version, accepted)

    def assert_released_calculators(self, name: str, *commands: str, version: str = "1.4.0") -> str:
        """The skill pins an australian-tax-calculators release, names the aus-accounting-mcp
        release that runs it, verifies it before use and keeps the written method as the result."""
        text = " ".join(skill_text(name).split())
        revision, server = self.RELEASES[version]
        release = f"https://github.com/ryanduguid/australian-accounting/releases/tag/australian-tax-calculators/v{version}"
        tree = f"https://github.com/ryanduguid/australian-accounting/tree/{revision}/packages/australian-tax-calculators"
        records = json.loads((SKILLS / name / "sources.json").read_text(encoding="utf-8"))["sources"]
        for url in (release, tree):
            with self.subTest(skill=name, url=url):
                self.assertIn(url, text)
                record = next((record for record in records if record["url"] == url), {})
                self.assertEqual(record.get("verification_status"), "source-discovery-only-human-review-pending")
        # A downloaded archive is trusted only after its provenance and checksum, both pinned to the tag.
        pins = (
            f"--repo ryanduguid/australian-accounting --source-ref refs/tags/australian-tax-calculators/v{version} "
            f"--source-digest {revision} --signer-workflow ryanduguid/release-policy/.github/workflows/release-binary.yml"
        )
        self.assertIn(f"gh attestation verify SHA256SUMS {pins}", text)
        self.assertIn("sha256sum --check --ignore-missing SHA256SUMS", text)
        self.assertIn(f"gh attestation verify <archive> {pins}", text)
        self.assertIn("Stop if any of the 4 fails.", text)
        self.assertIn(
            f"cargo install --locked --root <tool-dir> --git https://github.com/ryanduguid/australian-accounting --rev {revision} australian-tax-calculators",
            text,
        )
        self.assertIn(f"must show `australian-tax-calculators v{version}` with that commit in its source", text)
        self.assertIn("never one found on `PATH`", text)
        self.assertIn(f"check that `--version` prints exactly `australian-tax-calculators {version}`", text)
        self.assertIn(f"the executable `aus-accounting-mcp` {server} also runs for its tax worksheets", text)
        self.assertNotIn("runs the earlier", text)
        # A skill pins one release: a second tag would leave a reader two executables to verify.
        for other in self.RELEASES:
            if other != version:
                self.assertNotIn(f"australian-tax-calculators/v{other}", text)
        self.assertIn("A calculator's figure checks the written method, which is always completed", text)
        self.assertIn("record the difference for the reviewer and adopt neither", text)
        self.assertIn("Without the executable, follow the written method.", text)
        # 1.0.0 refuses `kind` on balancing-adjustment, trade-in, business-capital-expenditure and the classifier.
        self.assertIn("without the `kind` field that only `periods` takes", text)
        self.assertNotIn("e18d60b", text)
        for command in commands:
            with self.subTest(skill=name, command=command):
                self.assertIn(f"`{command}`", text)
        return text

    def test_skills_route_business_costs_and_cars_to_the_released_calculators(self) -> None:
        depreciation = self.assert_released_calculators(
            "au-depreciation-schedule", "business-capital-expenditure", "balancing-adjustment", "trade-in",
            "depreciation-low-value-pool", "depreciation-small-business-pool", version="1.4.0",
        )
        # The pool commands take step 4's established amounts; pool entry and taxable use stay with the step.
        pools = depreciation[depreciation.index("4. Apply the pools.") : depreciation.index("5. Apply caps.")]
        self.assertIn("with `depreciation-low-value-pool`", pools)
        self.assertIn("with `depreciation-small-business-pool`", pools)
        self.assertIn("Both cover the income years 2020-21 to 2026-27", pools)
        self.assertIn("each taxable use percentage or which assets the instant asset write-off or temporary full expensing took instead: those stay with this step", pools)
        # 0.12.0 runs the executable only by the released digest or one the operator names.
        self.assertIn("From `aus-accounting-mcp` 0.12.0 that worksheet runs", depreciation)
        self.assertIn("the value in `AUS_TAX_CALCULATORS_SHA256`", depreciation)
        self.assertIn("An earlier server, such as 0.11.0 or 0.12.0, accepts only an earlier release and refuses this one; the development plugin starts 0.13.0.", depreciation)
        # s 40-880: the 5 year rule and the start-up exception from the Act; the judgements stay the reviewer's.
        step = depreciation[depreciation.index("6a. **Business capital expenditure.**") : depreciation.index("7. Keep capital works")]
        self.assertIn("https://www.ato.gov.au/law/view/document?docid=PAC/19970038/40-880", step)
        self.assertIn("in equal proportions over 5 income years starting in the year it is incurred (s 40-880(2) of the ITAA 1997)", step)
        self.assertIn("a start-up expense that meets s 40-880(2A)", step)
        self.assertIn("having regard to any relevant circumstances, it is reasonable to conclude that it is proposed to be carried on within a reasonable time (s 40-880(7))", step)
        self.assertIn("the reasonable time test in s 40-880(7) of the ITAA 1997 and the entity tests in s 40-880(2A) and (2B) of the ITAA 1997 are reviewer decisions", step)
        self.assertIn("are reviewer decisions: record the evidence for each, not a conclusion", step)
        self.assertIn("refuses an outlay that forms part of a depreciating asset's cost (s 40-880(5)(a) of the ITAA 1997)", step)
        self.assertIn("so it refuses until the executable in [Tax calculators](#tax-calculators) is on `PATH`", depreciation)
        self.assertIn("Prefer the variable, naming the executable verified as that section describes", depreciation)

        cars = self.assert_released_calculators("au-car-expenses", "balancing-adjustment")
        self.assertIn("https://www.ato.gov.au/law/view/document?docid=PAC/19970038/40-370", cars)
        self.assertIn("a car claimed only by the cents per kilometre method has nothing assessable or deductible (s 40-370(1) Note 2)", cars)
        self.assertIn("give `asset` as `car`, one row per income year held with its `method` and `days_held`", cars)

        fbt = self.assert_released_calculators(
            "fbt-annual-workflow", "fbt-car-statutory", "fbt-car-operating-cost", version="1.4.0"
        )
        self.assertIn("used only where a valid logbook supports the operating cost method", fbt)
        self.assertIn("the statutory result's `taxable_value_before_exemption` as `statutory_formula_taxable_value`", fbt)
        self.assertIn("Their results are taxable values before gross-up, and neither applies the reportable fringe benefits threshold", fbt)

    def test_rental_skill_spreads_borrowing_expenses_under_s_25_25_and_routes_to_the_released_calculator(self) -> None:
        text = self.assert_released_calculators(
            "au-rental-property",
            "borrowing-expenses",
            "borrowing-expenses-schedule",
            "rental-property",
            "capital-works",
            version="1.4.0",
        )
        step = text[text.index("2a. Borrowing expenses:") : text.index("3. Trace borrowed funds")]
        self.assertIn("https://www.ato.gov.au/law/view/document?docid=PAC/19970038/25-25", step)
        # s 25-25(5) as read on 19 November 2026: the shortest of the 3 periods.
        self.assertIn(
            "the shortest of the period in the original loan contract, the period from the first day the money was "
            "borrowed to the day the loan is repaid, and 5 years from that first day (s 25-25(5) of the ITAA 1997)",
            step,
        )
        self.assertIn("the method statement in s 25-25(4) of the ITAA 1997", step)
        self.assertIn("the amount s 25-25(6) of the ITAA 1997 sets", step)
        self.assertIn("record the use of refinanced or redrawn money as a reviewer question", step)
        # borrowing-expenses, unchanged in 1.2.0: one loan, one year, 2017-18 to 2027-28, and its scope conditions.
        self.assertIn("one loan's deduction for one income year from 2017-18 to 2027-28", text)
        self.assertIn("all the expenditure to be incurred in the income year the loan began and one income-producing share throughout the loan", text)
        self.assertIn("and every income year after 2027-28; for 2027-28 it flags the result for the s 26-155 check", text)
        self.assertNotIn("29 February", text)
        # The schedule spreads several loans, refinancing included, and leaves the money's use to the reviewer.
        self.assertIn("for a loan that refinances an earlier one, which loan it repaid", text)
        self.assertIn("Which costs are borrowing expenses, the money's use and the tracing of redraws stay with steps 2a and 3", text)
        # 1.2.0's rental-property and capital-works: their years, scope and refusals; the facts stay with the steps.
        self.assertIn("one owner and income year from 2020-21 to 2026-27", text)
        self.assertIn("it does not support 2027-28, from which s 26-155 of the ITAA 1997 can quarantine rental deductions", text)
        self.assertIn("the use of borrowed money and each asset's decline in value stay with steps 1 to 4", text)
        self.assertIn("It refuses works begun before 16 September 1987, the higher rate for works begun before 27 February 1992", text)
        self.assertIn("which it does not carry forward, stay with step 2", text)

    def test_fuel_skill_sets_out_the_small_claimant_methods_without_their_figures(self) -> None:
        text = " ".join(skill_text("fuel-tax-credits").split())
        step = text[text.index("7a. **Use a small claimant method") : text.index("8. **Price litres")]
        # PCG 2016/2 para 11 limits Method 2 to an indexation change; the ATO page omits the condition.
        self.assertIn("changes within a tax period because of indexation", step)
        self.assertIn("the guideline does not cover it: price each litre by acquisition date under step 8", step)
        # Method 1 prices come from AIP's current retail page, which is read at use time, not stored.
        self.assertIn("](https://aip.com.au/pricing/pump-prices-retail)", step)
        self.assertIn("so Method 1 cannot be used for that fuel", step)
        self.assertIn("it is not indexed in `sources.json`", step)
        # PCG 2021/2 paras 9 to 12, with the ceiling and the derived percentage left to the guideline.
        self.assertIn("by the percentage para 9 sets", step)
        self.assertIn("never with the PCG 2016/11 percentages (para 12)", step)
        self.assertIn("Where the released `fuel-tax-credits` command in [Tax calculators](#tax-calculators) is installed", step)
        records = json.loads((SKILLS / "fuel-tax-credits" / "sources.json").read_text(encoding="utf-8"))["sources"]
        self.assertFalse([record["url"] for record in records if "aip.com.au" in record["url"]])

    #: Skills routed on 22 November 2026 to commands first released in, or
    #: otherwise unrouted before, australian-tax-calculators 1.1.0.
    ROUTES_1_1_0 = {
        "fuel-tax-credits": ("fuel-tax-credits",),
        "au-payroll-tax-states": ("payroll-tax",),
        "au-small-business-cgt": ("sb-cgt-concessions",),
        "au-main-residence": ("main-residence",),
        "au-working-holiday-makers": ("working-holiday-maker-withholding", "dasp-tax"),
        "au-gst-property": ("gst-margin-scheme",),
        "au-etp-redundancy": ("termination-payment", "etp-tax-free-component", "unused-leave-payment"),
        "au-medicare-review": ("medicare-levy", "medicare-levy-surcharge", "income-tests"),
        "au-sapto": ("seniors-pensioners-tax-offset",),
        "au-lump-sum-arrears": ("lump-sum-arrears-tax-offset",),
        "au-division-293": ("division-293",),
        "au-division-296": ("division-296",),
        "au-not-for-profit": ("dgr-check",),
        "au-super-contribution-caps": ("fhss",),
        "plant-and-equipment-costing": ("hire-purchase-schedule", "chattel-mortgage-schedule", "loan-transactions"),
        "fbt-annual-workflow": (
            "fbt", "fbt-return", "fbt-loan", "fbt-meal-entertainment", "fbt-car-parking", "fbt-debt-waiver",
            "fbt-expense-payment", "fbt-property", "fbt-residual", "fbt-housing", "fbt-lafha", "fbt-board",
            "fbt-tax-exempt-body-entertainment", "fbt-ev-exemption-check", "fbt-meal-entertainment-register",
            "fbt-minor-benefit-check",
        ),
    }

    def test_rd_and_residency_skills_route_their_1_2_0_commands(self) -> None:
        rd = self.assert_released_calculators("au-rd-incentive", "rd-tax-offset", version="1.4.0")
        residency = self.assert_released_calculators(
            "au-tax-residency", "residency-tests", "lodgment-required", version="1.4.0"
        )
        for text in (rd, residency):
            self.assertIn("`worksheet-catalogue` command", text)
            self.assertIn("never a client's name, address, TFN, ABN or other identifier", text)
        # Each command's years and refusals; registration, residency facts and treaty questions stay with the skill.
        self.assertIn("for an income year from 2021-22 to 2026-27. It refuses earlier years", rd)
        self.assertIn("registration and eligibility stay with the workflow above", rd)
        self.assertIn("never inferred from the dates or anything else", residency)
        self.assertIn("a tax treaty's tie-breaker may then apply; that question stays with the workflow above", residency)
        self.assertIn("It refuses 2026-27, as no instrument for that year was on the register on 22 November 2026", residency)

    def test_super_and_penalty_skills_route_their_1_2_0_commands(self) -> None:
        sup = self.assert_released_calculators(
            "au-smsf-death-benefits", "super-benefit-tax", "super-withholding", version="1.4.0"
        )
        pen = self.assert_released_calculators("au-ato-penalties-interest", "ato-interest-penalties", version="1.4.0")
        for text in (sup, pen):
            self.assertIn("`worksheet-catalogue` command", text)
            self.assertIn("never a client's name, address, TFN, ABN or other identifier", text)
        # Each command's years and refusals; dependency, the schedule read and culpability stay with the skill.
        self.assertIn("each part can bear in 2020-21 to 2026-27", sup)
        self.assertIn("never replaces step 6's record of the provision that governs each recipient", sup)
        self.assertIn("paid from 13 October 2020 to 30 June 2027", sup)
        self.assertIn("Step 7 still reads the current withholding schedule at use time", sup)
        self.assertIn("for an income year from 2020-21 to 2027-28", pen)
        self.assertIn("the culpability and any remission request stay with the workflow above", pen)

    def test_bas_skill_routes_the_gst_adjustment_commands_to_the_1_2_0_release(self) -> None:
        text = self.assert_released_calculators(
            "bas-preparation", "gst", "wine-equalisation-tax", "luxury-car-tax", "gst-creditable-purpose-change",
            "gst-annual-apportionment", "gst-financial-acquisitions-threshold", "gst-going-concern",
            "gst-second-hand-goods", "gst-bad-debt", version="1.4.0",
        )
        self.assertIn("`worksheet-catalogue` command", text)
        self.assertIn("never a client's name, address, TFN, ABN or other identifier", text)
        # The adjustment commands' years and refusals; the adjustment, its period and the labels stay with the skill.
        self.assertIn("and the financial acquisitions threshold tests, each for 2020-21 to 2026-27", text)
        self.assertIn("goods divided for resupply, goods leased before sale and valuable metal", text)
        self.assertIn("the BAS labels come from the supported workpapers, never from the command", text)

    def test_individual_and_business_skills_route_their_1_2_0_commands(self) -> None:
        individual = self.assert_released_calculators(
            "au-individual-return", "resident-tax", "foreign-resident-tax", "low-income-tax-offset",
            "study-loan-repayment", "personal-tax-estimate", "work-expenses", "private-health-insurance-rebate",
            "beneficiary-tax-offset", "invalid-carer-tax-offset", "zone-tax-offset",
            "net-medical-expenses-tax-offset", "government-super-amounts", version="1.4.0",
        )
        psi = self.assert_released_calculators("au-psi-review", "psi-test", version="1.4.0")
        sbito = self.assert_released_calculators(
            "au-small-business-income-offset", "small-business-income-offset", version="1.4.0"
        )
        ncl = self.assert_released_calculators("au-non-commercial-losses", "non-commercial-losses", version="1.4.0")
        dt = self.assert_released_calculators("au-financial-statements", "deferred-tax", version="1.4.0")
        for text in (individual, psi, sbito, ncl, dt):
            self.assertIn("`worksheet-catalogue` command", text)
            self.assertIn("never a client's name, address, TFN, ABN or other identifier", text)
        # Each command's years and refusals; the facts and judgements stay with the skill's workflow.
        self.assertIn("so steps 3 and 4 stay as written", individual)
        self.assertIn("refuses premiums paid from 1 April 2027", individual)
        self.assertIn("from 2020-21 to 2025-26, run once for each dependant", individual)
        self.assertIn("so route that to `au-sapto`", individual)
        self.assertIn("covers only 2016-17, 2017-18 and 2018-19", individual)
        self.assertIn("https://duguid.com.au/tools/individual-tax/government-super/", individual)
        self.assertIn("for a full-year resident the `private-health-insurance-rebate` command", individual)
        self.assertIn("the evidence for each answer stays with steps 1 to 3", psi)
        self.assertIn("are the operator's established figures from steps 2 to 4", sbito)
        self.assertIn("does not decide the Commissioner's discretion, which step 4 records", ncl)
        self.assertIn("the judgement whether future taxable profit is probable", dt)
        trader = " ".join(skill_text("au-sole-trader").split())
        self.assertIn("https://duguid.com.au/tools/individual-tax/sole-trader/", trader)
        self.assertIn("never as a fallback when a local tool refuses", trader)

    def test_withholding_skills_route_the_1_2_0_schedule_commands(self) -> None:
        payroll = self.assert_released_calculators(
            "au-payroll-review", "payg-gross-up", "schedule-5-method-a", "schedule-5-method-b-i",
            "schedule-5-method-b-ii", "seniors-pensioners-withholding", "daily-casual-withholding",
            "horticulture-shearing-withholding", "entertainer-withholding", "return-to-work-withholding",
            "annuity-withholding", "upward-variation-withholding", "payg-withholding", "study-loan-withholding",
            version="1.4.0",
        )
        bas = self.assert_released_calculators(
            "bas-preparation", "no-abn-withholding", "voluntary-agreement-withholding", version="1.4.0"
        )
        for text in (payroll, bas):
            self.assertIn("never a client's name, address, TFN, ABN or other identifier", text)
        # Each schedule's years and refusals; whether a payee falls under it stays with the workflow.
        self.assertIn("for payments from 1 July 2024 to 30 June 2027", payroll)
        self.assertIn("Whether a payee or payment falls under a schedule stays with step 5", payroll)
        self.assertIn("so another schedule's amount is worked with its own command first", payroll)
        self.assertIn("record them as step 5a says", payroll)
        self.assertIn("the operator establishes that the rule applies and that none of its exceptions does", bas)
        self.assertIn("stay with the payroll and payables records, never with the command", bas)

    def test_medicare_super_and_stp_skills_route_their_1_2_0_commands(self) -> None:
        medicare = self.assert_released_calculators(
            "au-medicare-review", "medicare-levy", "medicare-levy-surcharge", "income-tests",
            "private-health-insurance-rebate", version="1.4.0",
        )
        caps = self.assert_released_calculators(
            "au-super-contribution-caps", "fhss", "contribution-caps", "government-super-amounts", version="1.4.0"
        )
        stp = self.assert_released_calculators(
            "stp-finalisation", "payg-withholding", "study-loan-withholding", "quarterly-sg", version="1.4.0"
        )
        sgc = self.assert_released_calculators("au-super-guarantee-charge", "quarterly-sg", version="1.4.0")
        for text in (medicare, caps, stp, sgc):
            self.assertIn("`worksheet-catalogue` command", text)
            self.assertIn("never a client's name, address, TFN, ABN or other identifier", text)
        # Each command's years and refusals in its own codes; eligibility and the facts stay with the steps.
        self.assertIn("for an income year from 2020-21 to 2026-27, from step 1's statement lines", medicare)
        self.assertIn("(`private_health_insurance_rebate.rate_unpublished`)", medicare)
        self.assertIn("the supplied tax claim code stay with step 1", medicare)
        self.assertIn("a total offset of 144.94 and no excess", medicare)
        # Scope limits the catalogue states, kept beside the positive routes.
        self.assertIn("every person insured is an eligible person under the *Health Insurance Act 1973*", medicare)
        self.assertIn("leaves out defined benefit interests and notional taxed contributions", caps)
        self.assertIn("a deceased person's annualised income, interest on late payments", caps)
        self.assertIn("no bring-forward period started in either of the 2 previous years", caps)
        self.assertIn("(`contribution_caps.defined_benefit_interest`)", caps)
        self.assertIn("it never applies step 3's proposed July 2026 relief", caps)
        self.assertIn("(`government_super_amounts.fact_not_supplied`)", caps)
        self.assertIn("15,000 unused from 2020-21, 10,000 of it applied, 45,000 available, 5,000 headroom", caps)
        self.assertIn("never to rebuild the year's total", stp)
        self.assertIn("(`payg.pay_date_before_schedule`)", stp)
        self.assertIn("the command decides none of them", stp)
        self.assertIn("a lead for `au-super-guarantee-charge`, not a charge", stp)
        # The quarterly minimum is the required contribution, never the shortfall on salary or wages.
        for text in (stp, sgc):
            self.assertIn("one complete quarter of 2025-26", text)
            self.assertIn("It refuses 2026-27 (`period.unsupported`)", text)
        self.assertIn("so its additional contribution is never the shortfall or a charge", sgc)
        self.assertIn("returned a 1,560.00 minimum and a 65.00 additional contribution", sgc)

    def test_individual_and_super_skills_route_the_1_3_0_commands(self) -> None:
        ess = self.assert_released_calculators("au-employee-share-schemes", "ess-discount")
        foreign = self.assert_released_calculators(
            "au-foreign-income", "foreign-income-conversion", "foreign-income-tax-offset"
        )
        pension = self.assert_released_calculators("au-foreign-pensions", "foreign-pension-upp")
        individual = self.assert_released_calculators("au-individual-return", "minors-income", "help-indexation")
        smsf = self.assert_released_calculators("au-smsf-year-end", "smsf-tax")
        death = self.assert_released_calculators("au-smsf-death-benefits", "transfer-balance")
        for text in (ess, foreign, pension, individual, smsf, death):
            self.assertIn("`worksheet-catalogue` command", text)
            self.assertIn("never a client's name, address, TFN, ABN or other identifier", text)
        # Each refusal in its own code, the facts left with the workflow step, and the executable's figures.
        self.assertIn("(`ess_discount.foreign_employment`), so step 5 stays as written", ess)
        self.assertIn("returned a 1,500.00 discount taxed upfront, a 1,000.00 reduction and a 500.00 assessable discount", ess)
        self.assertIn("refuses a specific rate for any other day (`foreign_income_conversion.rate_date`)", foreign)
        self.assertIn("(`foreign_income_tax_offset.worked_year`)", foreign)
        self.assertIn("returned a deduction of 1,363.64 AUD", foreign)
        self.assertIn("returned a limit and offset of 2,198.80, with 1,201.20 above the limit", foreign)
        self.assertIn("(`foreign_pension_upp.part_year`) and one partly commuted (`foreign_pension_upp.commuted`)", pension)
        self.assertIn("returned a deductible amount of 2,500.00 and an assessable amount of 9,500.00", pension)
        self.assertIn("as the Commissioner's opinion settles them; the command decides none of them", individual)
        self.assertIn("(`minors_income.special_income_component`)", individual)
        self.assertIn("(`help_indexation.location_preferred`)", individual)
        self.assertIn("an accumulated debt of 83,104.00 on 1 June 2025", individual)
        self.assertIn("returned basic income tax of 2,468.00, 900.00 of it on the eligible income", individual)
        self.assertIn("(`smsf_tax.non_complying`)", smsf)
        self.assertIn("(`smsf_tax.disregarded_small_fund_assets`)", smsf)
        self.assertIn("gross tax of 17,565.00, 44,435.00 of offsets refunded, a 259.00 supervisory levy and 44,176.00 refundable", smsf)
        self.assertIn("so a reversionary credit and a child recipient's modified cap stay with step 5's written method", death)
        self.assertIn("returned a transfer balance of 800,000.00, a personal cap of 2,050,000.00 and no excess", death)

    def test_capital_gains_routes_cost_base_adjustments_to_the_1_2_0_release(self) -> None:
        text = self.assert_released_calculators(
            "au-capital-gains", "cgt-parcels", "capital-gains", "cgt-cost-base-adjustments", version="1.4.0"
        )
        self.assertIn("`worksheet-catalogue` command", text)
        self.assertIn("never a client's name, address, TFN, ABN or other identifier", text)
        # 1.2.0's cost base adjustments: its years, events and refusals; the amounts stay with the records.
        self.assertIn("from 1 July 2018 to the end of an income year from 2018-19 to 2026-27", text)
        self.assertIn("It refuses events before 1 July 2018 or after the year, a demerger it does not carry", text)
        self.assertIn("come from the statements and records in step 2", text)
        self.assertIn("the command does not work them out", text)

    def test_skills_route_the_1_1_0_commands_to_the_pinned_release(self) -> None:
        for name, commands in self.ROUTES_1_1_0.items():
            with self.subTest(skill=name):
                text = self.assert_released_calculators(name, *commands, version="1.4.0")
                # The route reads each worksheet's own scope and keeps the client out of the input.
                self.assertIn("`worksheet-catalogue` command", text)
                identifiers = (
                    "never employee names" if name == "fbt-annual-workflow"
                    else "never a client's name, address, TFN, ABN or other identifier"
                )
                self.assertIn(identifiers, text)
        # A refusal is stated in the command's own terms, not the figure behind it.
        fuel = " ".join(skill_text("fuel-tax-credits").split())
        self.assertIn("a simplified method without the small claimant statement", fuel)
        # From 1.2.0 Method 2 keeps each line's acquisition day across a period of flat rates.
        self.assertIn("where every applicable rate stays flat it keeps each line's acquisition day", fuel)
        sb = " ".join(skill_text("au-small-business-cgt").split())
        self.assertIn("refuses an active-day total that falls on the boundary of the active asset test's period", sb)
        gst = " ".join(skill_text("au-gst-property").split())
        # From 1.2.0 an approved valuation's day is checked against the facts s 75-10(3) fixes it by.
        self.assertIn("refuses a day s 75-10(3) of the GST Act does not fix for them", gst)
        for field in ("improved_on_1_july_2000", "registration_effective_day", "applied_for_registration",
                      "registration_application_day", "supply_day"):
            self.assertIn(f"`{field}`", gst)
        self.assertIn("It refers a possible overlap of items 2 and 3 for separate review.", gst)
        self.assertNotIn("takes the valuation date as given", gst)
        dgr = " ".join(skill_text("au-not-for-profit").split())
        self.assertIn("it never says a payment is deductible", dgr)
        self.assertIn("send the recipient's details only, never the donor's", dgr)
        # dgr-check refuses scope_confirmed, and its data holds no ended endorsement.
        self.assertIn("`dgr-check` takes no `scope_confirmed` flag", dgr)
        self.assertNotIn("a `scope_confirmed` flag: set it", dgr)
        self.assertIn("confirm every finding you rely on at ABN Lookup", dgr)
        fbt = " ".join(skill_text("fbt-annual-workflow").split())
        self.assertIn("use labels such as `Employer` and `E1`, never names", fbt)
        # The FHSS route leaves the figure to the determination and states the cutoff the release refuses past.
        fhss = " ".join(skill_text("au-super-contribution-caps").split())
        self.assertIn("The Commissioner's determination governs", fhss)
        self.assertIn("its associated earnings are labelled `estimate`", fhss)
        self.assertIn("after 31 December 2026, the last quarter whose shortfall interest charge rate", fhss)
        self.assertIn("(`fhss.contribution_kind_invalid`)", fhss)
        self.assertIn("do not request, release or notify anything", fhss)
        self.assertIn("do not rely on its `fhss_tax_if_not_used` or `recontribution_required`", fhss)
        # Item 30(4) exempts only what relates to or results from a qualifying item 30(1) action.
        self.assertIn("relating to, or resulting from, directly or indirectly, a transitional action", fhss)
        self.assertIn("A later release unrelated to such an action keeps those rules.", fhss)
        # Each of item 30(1)'s 4 conditions must hold.
        self.assertIn("a determination was made from 1 July 2018 to 14 September 2024", fhss)
        self.assertIn(
            "after it, the individual began holding an interest in real property or land of a kind "
            "TAA 1953 Sch 1 s 138-10(2)(a) mentions",
            fhss,
        )
        self.assertIn(
            "from 15 September 2024 to 14 September 2027 the individual applied to amend that determination, "
            "amended the valid release request or applied to vary a release authority for it",
            fhss,
        )
        self.assertIn("when that action was taken the Commissioner had not begun treating any FHSS credit", fhss)
        self.assertIn("the maximum release amount when none is given, as the amount released", fhss)
        individual = " ".join(skill_text("au-individual-return").split())
        self.assertIn("`au-super-contribution-caps` for a first home super saver (FHSS) release", individual)
        # 1.4.0's fbt-return takes employer_kind; fbt itself stays with ordinary taxable employers.
        self.assertIn("A rebatable or exempt employer is outside `fbt`; given `employer_kind`, `fbt-return` also composes", fbt)

    def test_div7a_skill_records_the_pinned_servers_term_refusals(self) -> None:
        text = " ".join(skill_text("div7a-compliance").split())
        self.assertIn("The plugin pins `aus-accounting-mcp` 0.13.0, whose `review_div7a_loan` refuses, with no figure", text)
        self.assertIn("Record the refusal and its code as an exception", text)

    def test_site_vehicle_and_div7a_routes_keep_the_decision_with_the_reviewer(self) -> None:
        site = "https://duguid.com.au/tools/business-calculators/"
        div7a = " ".join(skill_text("div7a-compliance").split())
        self.assertIn(f"{site}div7a/", div7a)
        self.assertIn(f"{site}div7a-schedule/", div7a)
        # The pages read the site's rate table, so the ato.gov.au rate from step 3 comes first.
        self.assertIn("only where the page's rate for the year matches the ato.gov.au rate", div7a)
        self.assertIn("a page's figure is a cross-check, never the assessed repayment", div7a)
        car = " ".join(skill_text("au-car-expenses").split())
        self.assertIn(f"{site}vehicle-class/", car)
        self.assertIn("It leaves the car limit undecided for a dual cab, a single cab ute and a panel van", car)
        self.assertIn("stop the car methods for that vehicle and carry the question to the reviewer", car)
        fbt = " ".join(skill_text("fbt-annual-workflow").split())
        self.assertIn(f"{site}vehicle-class/", fbt)
        self.assertIn(f"{site}fbt-car/", fbt)
        self.assertIn("It does not decide whether private use was minor, infrequent and irregular", fbt)
        self.assertIn("evidence for the exemption decision in step 2, which stays the reviewer's", fbt)
        for text in (div7a, car, fbt):
            self.assertIn("Record what it consumed: the page, the date run, the inputs", text)

    def test_fbt_skill_routes_entertainment_lines_to_the_pinned_classifier(self) -> None:
        text = self.assert_released_calculators("fbt-annual-workflow", "fbt-entertainment-classifier", version="1.4.0")
        self.assertIn('Send `{"kind": "fbt_entertainment_classifier"}` to its `periods` command first', text)
        # Each line and class it cannot settle goes to the reviewer; nothing it says is the reviewer's decision.
        self.assertIn("leaves a line or class `undetermined` where a fact is missing and names the fact", text)
        self.assertIn("shows the minor benefits exemption only as possible", text)
        self.assertIn("Carry each undetermined line or class and each possible minor benefit to the reviewer", text)
        self.assertIn("record the refusal and its code as an open item, and do not change the facts to get past it", text)
        self.assertIn("Send only the line facts above, amounts and head counts, never employee names or identifiers", text)
        # The classifier's scope also requires GST registration and facts the operator must establish.
        self.assertIn("Where the employer is registered for GST and not exempt from income tax", text)
        self.assertIn("set `scope_confirmed` only once each of those and each line's facts are evidenced", text)
        # Each condition the pinned scope statement (src/texts.rs at that commit) says the operator establishes.
        for condition in (
            "covers only an employer registered for GST and not exempt from income tax",
            "every attendee on a `travel_meal` line is travelling for work",
            "nothing is provided under a salary packaging arrangement",
            "as an in-house benefit",
            "by an associate of the employer",
            "none of the exceptions it names applies",
            "Record the evidence for each condition it lists",
        ):
            with self.subTest(condition=condition):
                self.assertIn(condition, text)
        self.assertIn("carry the affected lines to the reviewer unclassified", text)
        # Review round 1: a plain refusal prints no code; the 12 week register needs its percentage; a
        # reimbursed employee's share must be its own line, or the benefit type stays composite.
        self.assertIn("pass `--refusal-json` after the command so a refusal (exit 2) prints its code", text)
        self.assertIn("`income_tax_register_percentage` where that method is `12_week_register`", text)
        self.assertIn("give the reimbursed employee's share as its own classifier line", text)
        self.assertIn("never as the reviewer's decision on a position", text)
        # Review round 3: a remote calculator also needs fabricated or firm-approved inputs (shared rule 7).
        self.assertIn("explicitly permitted that call for this question, on fabricated or firm-approved inputs", text)
        self.assertIn("Without the classifier, classify each line from the primary sources", text)

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
        self.assertIn("Section 111(3) of the AML/CTF Act requires records", step)
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
                # SKILL.md bodies write AUD 75 (test_skill_figures.py says why); the reference keeps $75.
                aud = r"\$" if skill == "bas-preparation" else "AUD "
                self.assertRegex(text, aud + r"75\b")
                self.assertRegex(text, aud + r"82\.50")
                self.assertRegex(text, aud + r"75,? excluding GST|does not exceed " + aud + "75")
                self.assertRegex(text, aud + r"82\.50 including GST")
                self.assertIn("for most supplies", text)
                self.assertIn("aggregate value", text)
                self.assertIn("taxable part", text)
                self.assertIn("(GSTR 2013/1, paragraph 58)", text)
                self.assertIn("s 29-80(1)", text)
                self.assertIn("s 29-80.01", text)
                self.assertRegex(text, r"[Hh]uman review pending")
                self.assertNotRegex(text, aud + r"82\.50 threshold")
                self.assertNotRegex(text, aud + r"82\.50 excluding GST|" + aud + "75 including GST")
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

    def test_depreciation_pools_route_leaves_pool_entry_and_taxable_use_to_the_schedule(self) -> None:
        text = " ".join(skill_text("au-depreciation-schedule").split())
        self.assertIn("https://duguid.com.au/tools/business-calculators/depreciation-pools/", text)
        # The page takes amounts after the preparer's choices, so those choices stay in the schedule.
        self.assertIn("an income year from 2020-21 to 2026-27", text)
        self.assertIn("it does not decide which assets may go into a pool", text)
        self.assertIn("refuses works begun before 16 September 1987", text)
        self.assertIn("never the client's name, an asset serial number or a property address", text)

    def test_work_expenses_route_leaves_evidence_and_occupancy_to_the_workpaper(self) -> None:
        url = "https://duguid.com.au/tools/individual-tax/work-expenses/"
        wfh = " ".join(skill_text("au-wfh-deductions").split())
        car = " ".join(skill_text("au-car-expenses").split())
        self.assertIn(url, wfh)
        self.assertIn(url, car)
        # The page compares methods; the rate read, the hours evidence and occupancy stay with the skill.
        self.assertIn("read the year's rate from the ATO page in step 1 regardless", wfh)
        self.assertIn("step 5 and the hours and evidence of step 2 stay as written", wfh)
        self.assertIn("never the person's name or TFN", wfh)
        self.assertIn("It refuses a car the person did not own or lease", car)
        self.assertIn("so step 4 stays as written", car)

    #: Live site pages routed on 23 November 2026: each skill, the page and a
    #: boundary the page leaves to the skill's own workflow.
    SITE_PAGE_ROUTES = {
        "au-rental-property": (
            "business-calculators/rental-property/",
            "Ownership shares, the periods of use and the classification of each expense stay with steps 2 to 4",
        ),
        "au-ato-penalties-interest": (
            "business-calculators/ato-penalties-interest/",
            "GIC after 31 December 2026 unless a rate is assumed, which makes the result an estimate",
        ),
        "au-payg-instalment-variation": (
            "business-calculators/payg-instalments/",
            "or whether either option may be chosen, so steps 2 and 3 stay as written",
        ),
        "au-transfer-duty": (
            "business-calculators/first-home-owner-grant/",
            "takes the 4 eligibility facts as stated rather than testing them",
        ),
        "au-land-tax": (
            "business-calculators/foreign-surcharge/",
            "It does not decide which land is taxable, which rates apply, whether an owner is a foreign person",
        ),
        "au-ato-objection": (
            "business-calculators/objection-deadline/",
            "It does not know public holidays, so check the last day and the day after it",
        ),
        "au-psi-review": (
            "business-calculators/psi-determination/",
            "so the evidence for each stays with the workflow above",
        ),
        "au-company-tax": (
            "business-calculators/company-tax/",
            "with connected entities and affiliates, stay with step 2",
        ),
        "au-super-guarantee-charge": (
            "business-calculators/sgc-payday/",
            "amounts not yet received by the fund",
        ),
        "au-super-contribution-caps": (
            "individual-tax/concessional-catch-up/",
            "It works the cap only",
        ),
        "workers-compensation-premium": (
            "business-calculators/workers-compensation/",
            "The classification, the rate and which wages count stay with the workflow above",
        ),
        "au-professional-firm-profits": (
            "business-calculators/pcg-2021-4-allocation/",
            "a green zone is not a ruling: Part IVA can still apply",
        ),
        "au-etp-redundancy": (
            "business-calculators/long-service-leave/",
            "whether a break keeps service continuous",
        ),
        "coal-lsl-levy": ("coal-lsl-levy/", "never names, dates of birth or Coal LSL numbers"),
        "au-depreciation-schedule": ("depreciation-rates/", "Check each life against the registered determination"),
        "bas-preparation": ("bas-due-dates/", "the date on the activity statement governs"),
    }

    def test_site_page_routes_leave_the_skills_decisions_with_the_workflow(self) -> None:
        for name, (page, boundary) in self.SITE_PAGE_ROUTES.items():
            with self.subTest(skill=name):
                text = " ".join(skill_text(name).split())
                self.assertIn(f"https://duguid.com.au/tools/{page}", text)
                self.assertIn(boundary, text)
                # A page is a cross-check: never the fallback for a refusal, and its labels stay its own.
                self.assertIn("never as a fallback when a local tool refuses", text)
                self.assertIn("Keep the page's own labels as its own", text)

    #: Site pages live from 24 November 2026: each skill, the page and what the
    #: page refuses or leaves to the skill's own workflow.
    SITE_PAGE_ROUTES_24_NOV = (
        ("au-rd-incentive", "business-calculators/rd-tax-offset/", "registration and eligibility stay with steps 1 to 4"),
        ("au-rd-incentive", "business-calculators/rd-tax-offset/", "It refuses 2020-21 and earlier years"),
        ("bas-preparation", "business-calculators/gst-adjustments/", "Take the BAS labels from the supported workpapers"),
        ("bas-preparation", "business-calculators/gst-adjustments/", "the margin scheme and other special rules"),
        ("au-financial-statements", "business-calculators/deferred-tax/", "the judgement whether future taxable profit"),
        ("au-financial-statements", "business-calculators/deferred-tax/", "It refuses business combinations"),
        ("au-individual-return", "individual-tax/income-tax/", "It refuses taxable income that includes a special income component"),
        ("au-individual-return", "individual-tax/income-tax/", "does not decide whether the person was entitled to the offset"),
        ("au-foreign-income", "individual-tax/income-tax/", "Which tax counts and what a treaty allows stay with step 3"),
        ("au-foreign-income", "individual-tax/income-tax/", "it refuses a rate for a day other than the one the rule names"),
        ("au-non-commercial-losses", "individual-tax/sole-trader/", "the Commissioner's discretion is never decided there"),
        ("au-super-contribution-caps", "individual-tax/transfer-balance/", "It refuses reversionary income streams"),
        ("au-super-contribution-caps", "individual-tax/transfer-balance/", "The ATO's determination or assessment governs"),
        ("au-smsf-year-end", "individual-tax/pension-minimum/", "the test of payments made by 30 June stay with step 3"),
        ("au-smsf-year-end", "individual-tax/pension-minimum/", "does not apply the halved factors of 2019-20 to 2022-23"),
    )

    def test_24_november_site_page_routes_keep_the_skills_decisions(self) -> None:
        for name, page, boundary in self.SITE_PAGE_ROUTES_24_NOV:
            with self.subTest(skill=name, boundary=boundary):
                text = " ".join(skill_text(name).split())
                self.assertIn(f"https://duguid.com.au/tools/{page}", text)
                self.assertIn(boundary, text)
                self.assertIn("never as a fallback when a local tool refuses", text)
                self.assertIn("Keep the page's own labels as its own", text)
                self.assertIn("read 24 November 2026", text)

    def test_k8_routes_the_lease_page_and_leaves_business_days_unrouted(self) -> None:
        """K8, 26 November 2026: au-financial-statements step 4 measures leases, so it takes the
        AASB 16 lease page; no bas-preparation step counts business days, so that page is not routed."""
        text = " ".join(skill_text("au-financial-statements").split())
        step = text[text.index("4. Apply documented accounting policies") : text.index("5. Cross-check statements")]
        self.assertIn("For a lessee's lease under AASB 16, cross-check the lease liability", step)
        self.assertIn("https://duguid.com.au/tools/business-calculators/lease/", text)
        self.assertIn("read 26 November 2026", text)
        self.assertIn("It does not decide whether a contract is or contains a lease, the lease term, the discount rate", text)
        self.assertIn("never as a fallback when a local tool refuses", text)
        self.assertIn("Keep the page's own labels as its own", text)
        self.assertIn("never the lessee's or lessor's name, an ABN or an asset identifier", text)
        self.assertNotIn("business-calculators/business-days/", skill_text("bas-preparation"))

    def test_designated_services_lists_governing_body_oversight(self) -> None:
        """AUSTRAC's Your obligations page heads governance with 3 roles; s 26H of the AML/CTF Act
        is the governing body's duty, which step 7's obligation list lacked."""
        text = " ".join(skill_text("au-aml-ctf-designated-services").split())
        self.assertIn("the governing body's ongoing oversight", text)
        self.assertIn("(s 26H of the AML/CTF Act)", text)
        self.assertIn("https://www.austrac.gov.au/industry-and-business/obligations-and-guidance/your-obligations", text)

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

    def test_super_lump_sum_route_leaves_components_and_dependency_to_the_workflow(self) -> None:
        text = " ".join(skill_text("au-smsf-death-benefits").split())
        self.assertIn("https://duguid.com.au/tools/business-calculators/super-benefit-tax/", text)
        # The page takes the components and dependency as given and gives ceilings, not the tax payable.
        self.assertIn("paid from 1 July 2020 to 30 June 2027", text)
        self.assertIn("you state those, so step 6 stays as written", text)
        self.assertIn("death benefits paid to a deceased estate", text)
        self.assertIn("The fund's payment summary and the recipient's assessment, not the page, settle the tax", text)

    def test_gic_payment_plan_route_leaves_the_debt_and_the_plan_to_step_2_and_the_ato(self) -> None:
        text = " ".join(skill_text("au-ato-penalties-interest").split())
        self.assertIn("https://duguid.com.au/tools/business-calculators/gic-payment-plan/", text)
        # The page projects a plan; the accrued GIC and the real instalments are not its to give.
        self.assertIn("It does not work out the debt, its due date or GIC that accrued before the plan starts", text)
        self.assertIn("mark a result that relies on an assumed rate as an estimate", text)
        self.assertIn("the page's figure is an estimate for the reviewer, never the amount payable", text)
        self.assertIn("never the taxpayer's name or reference", text)

    def test_asic_fees_route_leaves_due_dates_and_payment_to_asic_and_the_officeholder(self) -> None:
        text = " ".join(skill_text("au-asic-company-changes").split())
        self.assertIn("https://duguid.com.au/tools/business-calculators/asic-fees/", text)
        # The page holds one fee year and works out no due date, so those stay with ASIC's records.
        self.assertIn("it takes due and received dates from 1 July 2026 to 30 June 2027 only", text)
        self.assertIn("It does not work out a due date, move one for a weekend or public holiday", text)
        self.assertIn("Check every amount against ASIC's invoice or fee table", text)
        self.assertIn("never the company's name, ACN or officeholders", text)

    def test_wet_and_lct_routes_leave_the_labels_to_the_workpapers(self) -> None:
        text = " ".join(skill_text("bas-preparation").split())
        self.assertIn("https://duguid.com.au/tools/business-calculators/wine-equalisation-tax/", text)
        self.assertIn("https://duguid.com.au/tools/business-calculators/luxury-car-tax/", text)
        # Each page holds its own years and leaves the tax period and classification to the preparer.
        self.assertIn("a financial year from 2023-24 to 2027-28", text)
        self.assertIn("a tax period in a financial year from 2019-20 to 2026-27", text)
        self.assertIn("flags rebates claimed above the cap without working out the excess", text)
        self.assertIn("Neither page decides which tax period a dealing or line belongs to", text)
        self.assertIn("Take labels 1C, 1D, 1E and 1F from the supported workpapers, never from the page", text)


    def test_business_and_state_tax_skills_route_their_1_3_0_and_1_4_0_commands(self) -> None:
        """Commands first released in calculators 1.3.0 or 1.4.0, routed on 26 November 2026. Each
        step names its command; the facts, eligibility and decisions stay with the skill."""
        routes = {
            "bas-preparation": ("gst-error-correction", "payg-instalment"),
            "au-payg-instalment-variation": ("payg-instalment",),
            "fbt-annual-workflow": ("fbt-instalment",),
            "au-payroll-tax-states": ("payroll-tax", "payroll-tax-group"),
            "au-land-tax": ("land-tax", "foreign-purchaser-surcharge", "vic-property-taxes"),
            "au-transfer-duty": ("transfer-duty", "foreign-purchaser-surcharge", "first-home-owner-grant"),
            "coal-lsl-levy": ("portable-lsl-levy",),
            "workers-compensation-premium": ("workers-compensation-premium",),
            "au-professional-firm-profits": ("pcg-2021-4",),
            "au-not-for-profit": ("dgr-check", "endorsement-review"),
            "au-asic-company-changes": ("asic-fees",),
            "au-depreciation-schedule": ("instant-asset-write-off",),
            "au-company-tax": ("prepayments", "trading-stock"),
            "au-financial-statements": ("deferred-tax", "impairment-test", "deferred-revenue"),
            "au-aml-ctf-client-coverage": ("aml-cdd-review",),
            "au-etp-redundancy": ("notice-period", "long-service-leave"),
            "au-mit-amit-trustee": ("cgt-cost-base-adjustments", "non-resident-withholding"),
        }
        texts = {name: self.assert_released_calculators(name, *commands) for name, commands in routes.items()}
        for name, text in texts.items():
            with self.subTest(skill=name):
                # Every figure quoted is the released executable's output on fabricated facts.
                self.assertIn("(run on 26 November 2026 with the verified 1.4.0 Windows executable)", text)
                self.assertRegex(text, r"Send only [^.]*, never [^.]*identifiers?\.")
        self.assertIn("it works no amount and amends nothing", texts["bas-preparation"])
        self.assertIn("the decision in step 7 stays with the authorised human", texts["bas-preparation"])
        self.assertIn("use it to check step 4's arithmetic only", texts["au-payg-instalment-variation"])
        self.assertIn("so step 6 still ties each instalment to the tax account", texts["fbt-annual-workflow"])
        self.assertIn("any exclusion order and the designated employer stay with steps 2 and 6", texts["au-payroll-tax-states"])
        self.assertIn("only the land tax surcharge belongs in this workpaper", texts["au-land-tax"])
        self.assertIn("so step 5's record of them stands", texts["au-land-tax"])
        self.assertIn("it has nothing to check until step 2 has a dutiable value", texts["au-transfer-duty"])
        self.assertIn("takes the 4 eligibility facts as stated without testing them", texts["au-transfer-duty"])
        self.assertIn("The released `portable-lsl-levy` command in [Tax calculators](#tax-calculators) is such a local tool.", texts["coal-lsl-levy"])
        self.assertIn("leaves the classification, the rate and which wages count to steps 1 to 4", texts["workers-compensation-premium"])
        self.assertIn("its zone is not a ruling", texts["au-professional-firm-profits"])
        self.assertIn("It checks no register and decides no status", texts["au-not-for-profit"])
        self.assertIn("The operator gives the due date: it never works one out from a review date", texts["au-asic-company-changes"])
        self.assertIn("does not decide the lock-out rules, so step 4 stays as written", texts["au-depreciation-schedule"])
        self.assertIn("it gave no deduction for 2025-26 and 24,000.00 for 2026-27", texts["au-company-tax"])
        self.assertIn("the policy, the estimates and the judgements stay with this step", texts["au-financial-statements"])
        # The practice's risk rating is recorded, never assigned by the command.
        self.assertIn("It takes the client's risk rating as recorded and never assigns one", texts["au-aml-ctf-client-coverage"])
        self.assertIn("an award, agreement or contract can give more", texts["au-etp-redundancy"])
        self.assertIn("It does not decide whether the trust is a withholding MIT", texts["au-mit-amit-trustee"])
        # charity-check needs the client's own ABN, which these skills never send to a calculator.
        self.assertNotIn("`charity-check`", texts["au-not-for-profit"])

    def test_leftover_routes_name_their_1_4_0_commands(self) -> None:
        """esic, foreign-resident-withholding and contract-register, routed on 26 November 2026.
        year-end-workpapers left its source exemption to hold the release records."""
        individual = self.assert_released_calculators("au-individual-return", "esic")
        nonresident = self.assert_released_calculators("au-nonresident-cgt", "foreign-resident-withholding")
        workpapers = self.assert_released_calculators("year-end-workpapers", "contract-register")
        for text in (individual, nonresident, workpapers):
            self.assertIn("(run on 26 November 2026 with the verified 1.4.0 Windows executable)", text)
            self.assertIn("never one found on `PATH`", text)
        self.assertIn("(`esic.trust_or_partnership_unsupported`)", individual)
        self.assertIn("the command decides none of them", individual)
        self.assertIn("it returned a tax offset of 8,000.00", individual)
        self.assertIn("(`foreign_resident_withholding.asset_unsupported`)", nonresident)
        self.assertIn("it is not the vendor's tax", nonresident)
        self.assertIn("it returned an amount payable of 123,000.00 (run", nonresident)
        self.assertIn("(`contract_register.kind_unsupported`)", workpapers)
        self.assertIn("Fill `contract`, `client` and `financier` with workpaper references.", workpapers)
        self.assertIn("never a client's or financier's name, a contract number, address, TFN, ABN or other identifier", workpapers)
        self.assertIn("it returned 39,852.89 outstanding, 11,933.23 current and 27,919.66 non-current", workpapers)
        self.assertFalse((SKILLS / "year-end-workpapers" / "sources.exempt.json").exists())

    NATIVE_COMMIT = "527f3ad4b0d87316ea66da5665d7b0e94cf9f97b"

    def assert_native_check(self, name: str, package: str, *commands: str) -> str:
        """The skill pins a 1.0.0 native executable (the-exchequer-tally or solomons-sword) at its tagged
        commit, verifies it before use, passes it no identifiers and keeps the written method as the result."""
        text = " ".join(skill_text(name).split())
        release = f"https://github.com/ryanduguid/australian-accounting/releases/tag/{package}/v1.0.0"
        tree = f"https://github.com/ryanduguid/australian-accounting/tree/{self.NATIVE_COMMIT}/packages/{package}"
        records = json.loads((SKILLS / name / "sources.json").read_text(encoding="utf-8"))["sources"]
        for url in (release, tree):
            with self.subTest(skill=name, url=url):
                self.assertIn(url, text)
                record = next((record for record in records if record["url"] == url), {})
                self.assertEqual(record.get("verification_status"), "source-discovery-only-human-review-pending")
        pins = (
            f"--repo ryanduguid/australian-accounting --source-ref refs/tags/{package}/v1.0.0 "
            f"--source-digest {self.NATIVE_COMMIT} --signer-workflow ryanduguid/release-policy/.github/workflows/release-binary.yml"
        )
        self.assertIn(f"gh attestation verify SHA256SUMS {pins}", text)
        self.assertIn("sha256sum --check --ignore-missing SHA256SUMS", text)
        self.assertIn(f"gh attestation verify <archive> {pins}", text)
        self.assertIn("Stop if any of the 4 fails.", text)
        self.assertIn(f"--rev {self.NATIVE_COMMIT} {package}", text)
        self.assertIn(f"check that `--version` prints exactly `{package} 1.0.0`", text)
        self.assertIn("never one found on `PATH`", text)
        self.assertIn("never a client's name, address, TFN, ABN or other identifier", text)
        self.assertIn("A tool's figure checks the written method, which is always completed", text)
        self.assertIn("Without the executable, follow the written method.", text)
        self.assertNotIn(f"/tree/main/packages/{package}", text)
        for command in commands:
            with self.subTest(skill=name, command=command):
                self.assertIn(f"`{command}`", text)
        self.assertIn("run on 27 November 2026 with the verified 1.0.0 Windows executable", text)
        return text

    def test_company_trust_and_partnership_skills_route_the_native_1_0_0_commands(self) -> None:
        """The Exchequer Tally and Solomon's Sword 1.0.0 shipped on 24 November 2026; routed on 27 November."""
        company = self.assert_native_check("au-company-tax", "the-exchequer-tally", "corporate-tax", "company-tax-statement")
        franking = self.assert_native_check(
            "au-franking-account", "the-exchequer-tally", "max-franking-rate", "franking-account", "benchmark", "statement"
        )
        partnership = self.assert_native_check("au-partnership-tax", "solomons-sword", "partnership-net-income")
        losses = self.assert_native_check("au-trust-losses", "solomons-sword", "trust-loss-tests")
        distributions = self.assert_native_check(
            "au-trust-distributions", "solomons-sword", "trust-resolution", "proportionate-share", "trustee-assessment", "s99b-liability", "s100a-check"
        )
        self.assertIn("it gave calculation statement label A 70,000.00, B 17,500.00 and S 13,500.00", company)
        self.assertIn("which the command never judges", company)
        self.assertIn("a closing balance of -2,000.00, franking deficit tax of 2,000.00 and an offset of 1,400.00", franking)
        self.assertIn("a second distribution franked at `75.00%` and a franking debit of 833.33", franking)
        self.assertIn("it gave net income of 90,000.00, shares of 54,000.00 and 36,000.00 and no partnership loss", partnership)
        self.assertIn("the reviewer decides whether each loss can be deducted", losses)
        self.assertIn("trustee tax of 11,250.00", distributions)
        self.assertIn("treat it as client data", distributions)
        for text in (company, franking, partnership, losses, distributions):
            self.assertNotIn("An optional local check, [`", text)


if __name__ == "__main__":
    unittest.main()
