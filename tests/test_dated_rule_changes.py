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

    def test_agent_consent_record_covers_ai_tools(self) -> None:
        text = skill_text("au-tax-agent-obligations")
        confidentiality = step(text, "3. Check conflicts and confidentiality.", "4. Check professional indemnity")
        self.assertIn("each AI tool used in a tax agent service", confidentiality)
        self.assertIn("TPB(GS) 55/2026", confidentiality)
        self.assertIn("issued 22 July 2026", confidentiality)
        self.assertIn("depending on how the tool is configured and used", confidentiality)
        self.assertIn("(paragraph 23)", confidentiality)
        self.assertIn("(paragraph 24)", confidentiality)
        self.assertIn("(paragraph 25)", confidentiality)
        self.assertIn("is for the responsible practitioner", confidentiality)
        self.assertIn(
            "](https://github.com/ryanduguid/llm-tax-guardrails/blob/main/src/data/gs55-concordance.yaml)",
            confidentiality,
        )
        self.assertIn("AI tools used in tax agent services", step(text, "## Inputs", "## Workflow"))
        self.assert_cited_and_pending(
            "au-tax-agent-obligations",
            "https://www.tpb.gov.au/tpbgs-552026-use-artificial-intelligence-and-code-professional-conduct",
        )

    def test_trust_beneficiary_tfns_move_to_the_statement_of_distribution(self) -> None:
        text = skill_text("au-trust-distributions")
        components = step(text, "Keep one component schedule per beneficiary statement", "4. Flag reimbursement")
        self.assertIn("whether a TFN was quoted to the trustee and when", components)
        self.assertIn("not the TFN itself", components)
        self.assertIn("quarterly TFN report ceased from 1 July 2026", components)
        self.assertIn("due by 31 July 2026", components)
        self.assertIn("statement of distribution", components)
        self.assertIn("starting with the 2027 lodgment", components)
        self.assertIn("TFN withholding where a beneficiary has not quoted a TFN is unchanged", components)
        self.assertIn("beneficiary TFN quote records", step(text, "## Inputs", "## Workflow"))
        self.assert_cited_and_pending(
            "au-trust-distributions",
            "https://www.ato.gov.au/businesses-and-organisations/trusts/trusts-registration-and-reporting-obligations/"
            "closely-held-trusts/tfn-withholding-for-closely-held-trusts/what-trustees-need-to-do",
            "https://www.ato.gov.au/businesses-and-organisations/business-bulletins-newsroom/"
            "changes-to-beneficiary-tfn-reporting-for-closely-held-trusts",
        )

    def test_nonresident_cgt_events_from_1_october_2026_use_the_amended_tests(self) -> None:
        text = skill_text("au-nonresident-cgt")
        connection = step(text, "2. Test the asset's connection", "3. Prepare a supported")
        self.assertIn("For a CGT event on or after 1 October 2026", connection)
        self.assertIn("(Act No. 86 of 2026)", connection)
        self.assertIn("item 39(2)", connection)
        self.assertIn("new s 995-1(1) definition", connection)
        self.assertIn("water entitlements", connection)
        self.assertIn("at any time in the 365 days before it", connection)
        self.assertIn("s 855-25(1A)", connection)
        self.assertIn("For an earlier CGT event, apply Division 855 as it stood at the event", connection)
        self.assert_cited_and_pending(
            "au-nonresident-cgt",
            "https://www.legislation.gov.au/C2026A00086/asmade/text",
            "https://www.legislation.gov.au/C2004A05138/latest/text",
        )

    def test_stp_finalisation_asks_about_changed_reporting_identifiers(self) -> None:
        """stp-finalisation's index takes only human-dated records, so the step dates the agent read."""
        text = skill_text("stp-finalisation")
        identifiers = step(text, "Before finalising, ask whether the ABN", "3. **Super guarantee.**")
        self.assertIn("PAYG withholding branch, payroll software or subscription (BMS ID)", identifiers)
        self.assertIn("**Human review pending:** an agent read", identifiers)
        self.assertIn("a separate income statement for each combination of ABN, branch, BMS ID and Payroll ID", identifiers)
        self.assertIn("replacement method", identifiers)
        self.assertIn("zeroing out", identifiers)
        self.assertIn("duplicate income statements", identifiers)
        self.assertIn("starts from zero YTD under the new one", identifiers)
        self.assertIn("each combination is finalised separately", identifiers)
        self.assertIn("an action for the authorised person", identifiers)
        base = "https://www.ato.gov.au/businesses-and-organisations/hiring-and-paying-your-workers/single-touch-payroll/"
        self.assertIn(f"]({base}changing-your-payroll-solution-or-employees-payroll-ids)", identifiers)
        self.assertIn(f"]({base}correcting-information-reported-through-stp)", identifiers)
        self.assertIn("payroll software or employee Payroll IDs", step(text, "## Inputs needed", "## Workflow"))


if __name__ == "__main__":
    unittest.main()
