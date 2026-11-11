# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The review steps added on 11 November 2026 keep their sources, conditions and limits.

Each test reads one step, screen or table row and checks what it must carry: the
provisions and dates read, the condition each result rests on, the `not run` and
`UNVERIFIED` outcomes and the decision left to a person. It checks wording, not
model behaviour. The helpers are in skill_prose.py.
"""

from __future__ import annotations

import re
import unittest

from skill_prose import (
    DO_NOT,
    ISO_DATE,
    PENDING,
    PENDING_FACT,
    SKILLS,
    affirms,
    raw_section,
    records,
    section,
    sentences,
    skill_text,
    workflow_step,
)

GST_ACT = "https://www.legislation.gov.au/C2004A00446/latest/text"
GST_REGULATIONS = "https://www.legislation.gov.au/F2019L00417/latest/text"
PCG_2026_1 = "https://www.ato.gov.au/law/view/document?docid=COG/PCG20261/NAT/ATO/00001"
FIRST_YEAR = (
    "https://www.ato.gov.au/businesses-and-organisations/super-for-employers/missed-or-late-payday-super-payments/"
    "getting-it-right-compliance-in-the-first-year-of-payday-super"
)
SELF_BILLING = "https://docs.peppol.eu/poac/aunz/pint-aunz-sb/bis/"
WITHDRAWAL_NOTICE = "https://www.ato.gov.au/law/view/document?DocID=GST/GSTR200010/NAT/ATO/00001"
GN11 = "https://a-nz-peppol.github.io/Guidance-documents/GuidanceNote11_Use_of_Tax_Category_Codes.html"
GN01 = "https://a-nz-peppol.github.io/Guidance-documents/GuidanceNote01_WETandLCT"
CLIENT_FIELDS = "https://central.xero.com/s/article/Create-a-client-in-Practice-Manager-AU"
STAPLED = (
    "https://www.ato.gov.au/businesses-and-organisations/super-for-employers/setting-up-super-for-your-business/"
    "offer-employees-a-choice-of-super-fund/stapled-super-funds-for-employers"
)
VALUING = (
    "https://www.ato.gov.au/individuals-and-families/super-for-individuals-and-families/self-managed-super-funds-smsf/"
    "smsf-administration-and-reporting/guide-to-valuing-smsf-assets"
)
SISR = "https://www.legislation.gov.au/F1996B00580/latest/text"
SGAA = "https://www.legislation.gov.au/C2004A04402/latest/text"
SGA_REGULATIONS = "https://www.legislation.gov.au/F2018L01289/latest/text"
QLD_PAYROLL_TAX_ACT = "https://www.legislation.qld.gov.au/view/whole/html/inforce/current/act-1971-037"


def screen_row(name: str) -> str:
    """The cells after the first of the transaction GST review's lead-screen row `name`."""
    path = SKILLS / "bas-preparation" / "references" / "transaction-gst-review.md"
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if line.startswith("|") and cells[0] == name:
            return " ".join(" | ".join(cells[1:]).split())
    raise AssertionError(f"the transaction GST review has no '{name}' screen")


class PracticeReviewStepTests(unittest.TestCase):
    def assert_carries(self, text: str, *terms: str) -> None:
        folded = text.casefold()
        for term in terms:
            with self.subTest(term=term):
                self.assertIn(term.casefold(), folded)

    def assert_sentence(self, text: str, *patterns: str, affirmed: tuple[str, ...] = ()) -> None:
        """One sentence of `text` matches every pattern, and each `affirmed` pattern unnegated."""
        with self.subTest(patterns=patterns, affirmed=affirmed):
            self.assertTrue(
                any(all(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)
                    and all(affirms(sentence, pattern) for pattern in affirmed)
                    for sentence in sentences(text)),
                f"no sentence matches all of {patterns} with {affirmed} affirmed",
            )

    def assert_pending(self, skill: str, *urls: str) -> None:
        """Each URL is linked from the skill and indexed as an agent read awaiting human review."""
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

    # bas-preparation: R0820 and R0824

    def test_manual_journal_screen_reads_the_source_column_and_stays_a_lead(self) -> None:
        row = screen_row("Manual journal to a GST account")
        self.assert_carries(row, "GST control account", "`Source`", "General Ledger Detail",
                            "Account Transactions", "Journal Report")
        self.assert_sentence(row, r"\bno supplied export shows the source\b", r"`not run`")
        self.assert_sentence(row, r"\bname that event or keep the line unresolved\b")

    def test_government_fee_screen_carries_division_81_and_its_exceptions(self) -> None:
        row = screen_row("Credit on a government fee")
        self.assert_carries(row, "Division 81", "compilation 96", "11 November 2026", "human review pending")
        # Both limbs of s 81-10, each with its qualifier, in the sentence that cites them.
        self.assert_sentence(row, r"\bnot consideration\b", r"\bAustralian tax \(s 81-5\(1\) of the GST Act\)",
                             r"\bthe provision, retention or amendment under an Australian law of a permission, "
                             r"exemption, authority or licence, or an application for one\b",
                             r"\bor to an agency recording, copying, modifying, allowing access to, receiving, "
                             r"processing or searching information \(s 81-10\(1\), \(4\) and \(5\) of the GST Act\)")
        # The regulations can reverse either exclusion, and agencies make taxable supplies too.
        self.assert_sentence(row, r"\btreat a prescribed tax, fee or charge as consideration \(ss 81-5\(2\) and 81-10\(2\) of the GST Act\)",
                             r"\bexclude others \(s 81-15 of the GST Act\)", r"\bcan also make taxable supplies\b")
        self.assert_sentence(row, r"\(compilation 5\)", r"\bno regulation for s 81-5\(2\)",
                             r"\breg 81-10\.01 of the GST Regulations 2019 prescribes as consideration\b", r"\bticketed or metered parking\b",
                             r"\broad tolls\b", r"\breg 81-15\.01 of the GST Regulations 2019 excludes\b", r"\bregulatory cost recovery\b",
                             r"\bcourt and tribunal fees\b", r"\breg 81-15\.02\b")
        # Only a national park's entry fee is outside reg 81-10.01(1)(c), not every national park charge.
        self.assertIn("'a fee for hire, use of, or entry to a facility, other than an entry fee to a national park'",
                      row)
        self.assertNotIn("facility other than a national park", row)
        indexed = records("bas-preparation")
        for url in (GST_ACT, GST_REGULATIONS):
            with self.subTest(url=url):
                self.assertIn(f"]({url})", row)
                self.assertEqual(indexed[url]["verification_status"], PENDING)

    def test_bas_preparation_routes_payroll_wages_to_the_payroll_tax_threshold_test(self) -> None:
        step = workflow_step("bas-preparation", 2)
        self.assert_sentence(step, r"\bstep 3 of `au-payroll-tax-states`", r"\binput 9\b",
                             r"\brevenue office page\b")
        # Registration turns on total Australian (or group) wages, monthly and annually, not local wages.
        self.assert_sentence(step, r"\bfor each state or territory where wages are paid, compare total Australian wages "
                             r"\(group wages where the entity is grouped\), not that jurisdiction's own wages\b",
                             r"\bthe month's total against its monthly threshold\b",
                             r"\bthe year-to-date total against its annual threshold\b")
        # A weekly registration amount is tested too; Queensland's applies whatever the annual total.
        self.assert_sentence(step, r"\bregistration page also sets a weekly amount, compare each week's total with it\b",
                             r"\bQueensland's page requires registration within 7 days of the first month in which "
                             r"Australian wages exceed its weekly amount\b",
                             r"\beven where wages for the year are expected to stay below its annual threshold\b")
        self.assert_sentence(step, r"`not run`", r"\bthe weekly totals a weekly amount needs\b")
        # Queensland's group member rule is a separate lead, not a threshold result.
        self.assert_sentence(step, r"\bSeparately, where the entity is a group member and pays Queensland wages with no "
                             r"Queensland registration recorded, list it whatever the thresholds show\b")
        self.assert_sentence(step, r"\bwhere wages are paid and the total exceeds a threshold with no registration recorded\b",
                             affirmed=(r"\blist each jurisdiction\b",))
        self.assertNotRegex(step, r"\bwhose (monthly or year-to-date )?wages exceed its threshold\b")
        self.assert_sentence(step, r"\bnot a liability or a registration decision\b",
                             r"\bgross is not taxable wages\b")
        self.assert_sentence(step, r"`not run`", r"\bwages by jurisdiction, total Australian or group wages\b",
                             r"`au-payroll-tax-states` is not installed\b")
        inputs = section("bas-preparation", "Inputs needed")
        self.assertRegex(inputs, r"\b9\. Where payroll is in scope, taxable wages by state or territory and total "
                                 r"Australian wages \(group wages where the entity is grouped\), each for the month "
                                 r"and the year to date, total Australian wages for each week of the month where "
                                 r"wages are paid in Queensland\b")
        checks = section("bas-preparation", "Checks before handing over")
        self.assertIn("the payroll tax screen compares total Australian wages (group wages where grouped) with each "
                      "paying jurisdiction's monthly and annual thresholds and any weekly amount its registration "
                      "page sets", checks)
        self.assertIn("and separately any Queensland group member paying Queensland wages with no registration "
                      "recorded", checks)
        owner = workflow_step("au-payroll-tax-states", 3)
        self.assert_sentence(owner, r"\bmonthly and annually, and each week's total against any weekly amount its "
                             r"registration page sets \(Queensland's does\)")
        self.assert_sentence(owner, r"\bSeparately, list each unregistered group member that paid Queensland taxable "
                             r"wages in a month, however small its or its group's wages\b",
                             r"\bss 52\(b\) and 53\(1\) of the \[Payroll Tax Act 1971 \(Qld\)\]",
                             r"\bwithin 7 days after the end of that month\b")
        self.assert_pending("au-payroll-tax-states", QLD_PAYROLL_TAX_ACT)

    # au-super-guarantee-charge: R0828

    def test_charge_register_records_the_first_year_risk_zone_from_dates_and_confirmed_facts(self) -> None:
        step = workflow_step("au-super-guarantee-charge", "5a")
        self.assert_carries(step, "PCG 2026/1", "28 January 2026", "Human review pending", "11 November 2026",
                            "1 July 2026 to 30 June 2027 inclusive")
        self.assert_sentence(step, r"\b1 July 2026 to 30 June 2027 inclusive, and for no later QE day\b")
        self.assert_sentence(step, r"\bdoes not change the law\b")
        self.assert_sentence(step, r"\bstill apply the law to a shortfall\b", r"\bparagraphs 3, 11 and 13\b")
        self.assert_sentence(step, r"\bRecord the `as_at` date the zones are assessed at\b")
        # Table 2's zones, each with its own condition, and the pending state before the medium deadline.
        self.assert_sentence(step, r"\blow: the employer attempted on-time contributions equal to or above the "
                             r"individual SG amount, some were not received\b",
                             r"\bas soon as reasonably practicable\b", r"\bindividual final SG shortfall nil\b")
        self.assert_sentence(step, r"\bmedium: low is not met\b",
                             r"\bby the end of 28 days after the end of the quarter in which the qualifying earnings were paid\b")
        self.assert_sentence(step, r"\bold quarterly timing cannot be low \(paragraph 18\)")
        self.assert_sentence(step, r"\bhigh: neither is met\b", r"\babove nil after that day\b")
        self.assert_sentence(step, r"\bpending: the `as_at` date falls on or before that day and a shortfall remains\b",
                             r"\bmedium test cannot yet fail\b")
        self.assert_sentence(step, DO_NOT + r"record such a QE day as high\b")
        # A contribution made without receipt evidence is not a contribution never made.
        self.assert_sentence(step, r"\ba contribution made whose fund receipt date is not evidenced makes the zone `UNKNOWN`",
                             r"\ba contribution never made, or made short, is a shortfall, and it puts the QE day in the "
                             r"high zone only if some of it is still unpaid after that day\b",
                             r"\bone made good by then is medium, as in paragraph 46\b")
        self.assert_sentence(step, r"\bif no errors have been received the employer can assume it was received on time\b")
        self.assert_sentence(step, r"\bleave the receipt date blank and the row's timing `UNKNOWN`",
                             r"\bnot fund receipt evidence\b")
        self.assert_sentence(step, r"\bwho confirmed them\b")
        self.assert_sentence(step, r"\bno one has confirmed the low-zone facts\b", r"'not high'", r"`UNVERIFIED`")
        self.assert_sentence(step, r"\bnot a charge, a penalty position or a finding that nothing is owed\b")
        handoff = section("au-super-guarantee-charge", "Hand-off and checks")
        self.assertIn("at a recorded `as_at` date", handoff)
        self.assertIn("who confirmed the low-zone facts", handoff)
        self.assert_pending("au-super-guarantee-charge", PCG_2026_1, FIRST_YEAR)

    # xero-exports: R0842

    def test_connector_route_ties_a_connector_total_to_the_on_screen_report_first(self) -> None:
        route = section("xero-exports", "Read-only connector route")
        self.assert_sentence(route, r"\bBefore relying on a connection for a client, tie it once to Xero's on-screen report\b")
        self.assert_sentence(route, r"\bsame organisation, date, basis and filters\b")
        self.assert_sentence(route, r"\bA person with access runs the on-screen report\b",
                             r"\bscreenshot or export kept as evidence\b")
        self.assert_sentence(route, r"\bagree to the cent and, for the aged receivables option, name the same contacts\b")
        self.assert_sentence(route, r"\bOn a difference, stop\b", r"\buse the file-export path\b")
        self.assert_sentence(route, r"\btie again when the connection, the organisation or the server changes\b")
        self.assert_sentence(route, r"\bRun completeness checks 1 and 3 above on what the read returns\b")
        self.assert_sentence(route, r"\bStop on a failure\b")

    # tax-invoice-review: R1012

    def test_einvoice_review_checks_tax_category_codes_and_wet_and_lct_lines(self) -> None:
        step = workflow_step("tax-invoice-review", 3)
        self.assert_carries(step, "Guidance Note 11", "version 1.2", "Guidance Note 01", "version 1.0.2",
                            "Human review pending", "11 November 2026", f"]({GN11})", f"]({GN01})")
        # Each code's meaning, closed by its list separator so a widened meaning fails.
        for code, meaning in (("S", r"for taxable supplies at a non-zero rate, which must show the legislated rate;"),
                              ("E", r"for input taxed supplies;"), ("Z", r"for GST-free supplies;"),
                              ("G", r"for GST-free exports only, never for goods and services sold or provided to "
                                    r"customers in Australia;"),
                              ("O", r"only on invoices from an entity that is neither registered nor required to be "
                                    r"registered for GST\.")):
            with self.subTest(code=code):
                self.assertRegex(step, rf"`{code}` {meaning}")
        self.assert_sentence(step, r"\bnever for goods and services sold or provided to customers in Australia\b")
        self.assert_sentence(step, r"\bnot the GST treatment\b", r"\bmatching code does not clear a line\b")
        self.assert_sentence(step, r"\breason code `ZZZ`", r"\bWET-inclusive amount\b",
                             r"\bseparate line coded `E` under the GST scheme\b")
        self.assert_sentence(step, DO_NOT + r"list such a line as an input taxed supply\b",
                             r"\bfrom the ATO at use time\b")
        self.assert_sentence(step, r"\bNeither guidance note is indexed\b", r"\boutside the reviewed fetch list\b")

    def test_peppol_rcti_meets_the_same_conditions_as_any_rcti(self) -> None:
        step = workflow_step("tax-invoice-review", 4)
        # Each code bound to its document type, so swapping them fails.
        self.assert_sentence(step, r"\bPINT A-NZ Self-billing specification\b",
                             r"\bdocument type code `389` for an invoice or `261` for a credit note\b")
        self.assert_sentence(step, r"\bnot validated\b", r"\bdoes not guarantee or enforce legal compliance\b")
        self.assert_sentence(step, r"\bApply every condition above to a Peppol RCTI as to any other\b",
                             r"\bdoes not show a written agreement\b")
        self.assert_pending("tax-invoice-review", SELF_BILLING)

    def test_rcti_withdrawal_dates_stay_with_the_withdrawal_notice(self) -> None:
        step = workflow_step("tax-invoice-review", 4)
        # Each date bound to its event in the sentence that names the notice, so a swapped
        # or unattributed date fails.
        self.assert_sentence(step, r"\[GSTR 2000/10W withdrawal notice\]",
                             r"\bwithdraws GSTR 2000/10 with effect from 29 July 2026\b",
                             r"\bcontinues to apply to RCTIs issued on or before 14 June 2023\b",
                             r"\bnot to RCTIs issued on or after 15 June 2023\b")
        self.assertEqual(step.count("14 June 2023"), 1)
        self.assert_pending("tax-invoice-review", WITHDRAWAL_NOTICE)
        limitations = " ".join(str(records("tax-invoice-review")[WITHDRAWAL_NOTICE]["limitations"]).split())
        self.assert_carries(limitations, "withdrawn with effect from 29 July 2026",
                            "on or before 14 June 2023", "on or after 15 June 2023", "F2023L00785",
                            "registered on 14 June 2023", "A reviewer must confirm both dates")

    # au-aml-ctf-client-coverage: R1019 and R1017

    def test_client_matching_names_the_code_field_and_reports_dual_code_mismatches(self) -> None:
        step = workflow_step("au-aml-ctf-client-coverage", 1)
        self.assert_sentence(step, r"\bRecord which field each record keys on\b")
        self.assert_sentence(step, r"\bclient reference code\b", r"\bolder \[Practice Manager 3\.0 API\]",
                             r"\bXero recommends version 3\.1\b", r"`ExportCode`",
                             r"\bwhether version 3\.1 returns it was not confirmed\b")
        self.assertNotIn("deprecated", step)
        self.assert_sentence(step, r"\bmatch on one code but not the other\b", r"\bcodes that match different clients\b",
                             affirmed=(r"\blist clients\b",))
        self.assert_sentence(step, r"\bkeyed on one field matched against the other stays `UNVERIFIED`")
        self.assert_sentence(step, r"\bleaves archived clients out\b", r"\bpossibly archived, not as an unknown client\b")
        self.assertIn("naming the field it comes from", section("au-aml-ctf-client-coverage", "Inputs"))
        self.assert_pending("au-aml-ctf-client-coverage", CLIENT_FIELDS)

    def test_trust_beneficial_owner_evidence_is_tested_role_by_role(self) -> None:
        step = workflow_step("au-aml-ctf-client-coverage", 3)
        self.assert_carries(step, "last updated 4 November 2026", "Human review pending", "11 November 2026")
        self.assert_sentence(step, r"\btrustees\b", r"\bsettlors, appointors, guardians and protectors\b",
                             r"\bother individual with control\b", r"\bbare trust\b")
        self.assert_sentence(step, r"\bcontrol structure\b", r"\bcan be cross-referenced with documents such as the trust deed\b",
                             r"\bowns or controls the trust\b")
        self.assert_sentence(step, r"\bscreening\b", r"\bthe trust, every trustee and any representative who engages "
                             r"with the firm, all identifiable beneficiaries\b",
                             r"\bevery individual settlor, appointor, guardian, protector\b",
                             r"\bwith control, unless an exemption applies\.")
        self.assert_sentence(step, r"\blist each role present by position \(such as trustee 1 of 2 or appointor 1 of 1\)",
                             r"\blist the trust itself, each representative and each identifiable beneficiary by "
                             r"position with its screening date\b")
        self.assert_sentence(step, r"\bno identity record\b", r"\bno verification evidence reference\b",
                             r"\bany person or the trust on that screening list with no screening date\b",
                             r"\bno recorded control structure\b",
                             affirmed=(r"\bList as a missing element\b",))
        self.assert_sentence(step, r"\bno record of the document it was checked against\b", r"\bas a question, not a missing element\b")
        self.assert_sentence(step, r"\bonly verified individual is a trustee\b")
        self.assert_sentence(step, r"\bWho owns or controls a trust\b", r"\bare for that officer\b")
        inputs = section("au-aml-ctf-client-coverage", "Inputs")
        self.assertIn("for a trust, the recorded control structure", inputs)
        self.assertIn("the screening dates for the trust itself, each representative who engages with the firm and each "
                      "identifiable beneficiary by position", inputs)

    # au-payroll-review: R1030

    def test_payroll_review_screens_new_employees_for_a_stapled_fund_request(self) -> None:
        step = workflow_step("au-payroll-review", "4b")
        self.assert_carries(step, "last updated 2 September 2026", "Human review pending", "11 November 2026")
        self.assert_sentence(step, r"\ban employer must request an employee's stapled fund details where the employee "
                             r"started after 1 November 2021\b", r"\beligible to choose a fund but does not\b",
                             r"\bnot eligible to choose\b")
        self.assert_sentence(step, r"\bin most cases a TFN declaration or a Single Touch Payroll pay event\b")
        self.assert_sentence(step, r"\bchosen fund, otherwise to the stapled fund\b",
                             r"\bdefault fund only where there is no stapled fund\b")
        # A default fund payment after the ATO returned no stapled fund is not a lead.
        self.assert_sentence(step, r"\bpaid to the default fund without a request outcome\b",
                             r"\bfund other than the chosen fund, the stapled fund or, where the ATO returned none, "
                             r"the default fund\b", affirmed=(r"\bList as a lead\b",))
        # Contributions s 32C treats as complying without a chosen or stapled fund are recorded, not listed.
        self.assert_sentence(step, r"\bFirst record whether the contribution is made under a route that s 32C\b",
                             r"\balthough the fund paid is not the chosen or stapled fund\b",
                             r"\bState industrial award \(s 32C\(8\) of the SGAA\)",
                             r"\benterprise agreement or workplace determination made before 1 January 2021 once the "
                             r"ATO has returned no stapled fund \(s 32C\(6\)\(g\), \(h\) and \(6AAA\) of the SGAA\)",
                             r"\bsuccessor fund to which the employee's interest in the default fund or the stapled "
                             r"fund was transferred without the employee's consent after the employer's last "
                             r"contribution to that fund \(s 32C\(2AB\) of the SGAA\)",
                             r"\bregulation 15\b.{0,200}\(s 32C\(9\) of the SGAA\)")
        self.assert_sentence(step, r"\bsuccessor fund transfer and its evidence\b",
                             r"\bleave whether it applies to the reviewer\b",
                             DO_NOT + r"list a contribution so recorded as a lead\b")
        self.assert_sentence(step, r"`not run`", r"\bstart dates or fund records\b")
        self.assert_sentence(step, DO_NOT + r"make the request\b", r"`au-super-guarantee-charge`")
        self.assertIn("a stapled fund screen result", section("au-payroll-review", "Hand-off and checks"))
        self.assert_pending("au-payroll-review", STAPLED, SGAA, SGA_REGULATIONS)

    # au-smsf-year-end: R0678

    def test_smsf_year_end_records_each_assets_market_value_basis_and_evidence(self) -> None:
        step = workflow_step("au-smsf-year-end", "1a")
        self.assert_carries(step, "Regulation 8.02B", "compilation 159", "s 35B(1)", "s 10(1)",
                            "last updated 15 May 2026", "Human review pending", "11 November 2026", f"]({SISR})")
        self.assert_sentence(step, r"\bvalued at its market value\b")
        self.assert_sentence(step, r"\bobjective and supportable data\b")
        self.assert_sentence(step, r"\bclosing price on their exchange or licensed market on 30 June\b",
                             r"\bpublished exit price\b")
        self.assert_sentence(step, r"\bmore than one item of evidence\b", r"\bcomparable sales\b",
                             r"\bassess and document whether it is still appropriate\b")
        self.assert_sentence(step, r"\bwhether that valuer is independent of the fund\b",
                             affirmed=(r"\bFor each asset record the value\b",))
        self.assert_sentence(step, r"\ban asset carried at cost or a prior-year value with no evidence that it is "
                             r"market value at the balance date\b",
                             r"\ban earlier valuation relied on without the trustee's documented assessment\b",
                             r"\ba value from any person or tool, automated or otherwise, whose data, method and "
                             r"assumptions are not recorded\b",
                             r"\ba collectable or personal use asset disposed of to a related party without a "
                             r"qualified independent valuer's valuation where the guide says the law requires one "
                             r"\(an asset acquired on or after 1 July 2011, or acquired earlier and disposed of after "
                             r"30 June 2016\)",
                             affirmed=(r"\bList as an exception\b",))
        self.assert_sentence(step, DO_NOT + r"set a value or conclude that a recorded value is market value\b")
        self.assertIn("an asset valuation schedule", raw_section("au-smsf-year-end", "Hand-off and checks"))
        self.assert_pending("au-smsf-year-end", VALUING)
        self.assertIn(SISR, records("au-smsf-year-end"))


if __name__ == "__main__":
    unittest.main()
