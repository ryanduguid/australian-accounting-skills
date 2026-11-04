# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""Skills that meet a 2026 rule change keep its start date, its scope and its source.

Each test reads one numbered workflow step and checks the dates, authorities,
exceptions and escalations it must carry, not its wording.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[1] / ".claude" / "skills"
PENDING = "source-discovery-only-human-review-pending"
PENDING_FACT = "Primary-source discovery only; no human-reviewed current-law fact is recorded."
ISO_DATE = r"^\d{4}-\d{2}-\d{2}$"


def skill_text(skill: str) -> str:
    return (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")


def raw_section(skill: str, heading: str) -> str:
    """The Markdown under the first `## <heading>...` until the next `## ` heading."""
    text = skill_text(skill)
    start = re.search(rf"^## {re.escape(heading)}.*$", text, re.MULTILINE)
    assert start, f"{skill} has no '## {heading}' section"
    end = re.compile(r"^## ", re.MULTILINE).search(text, start.end())
    return text[start.end() : end.start() if end else len(text)]


def section(skill: str, heading: str) -> str:
    return " ".join(raw_section(skill, heading).split())


def workflow_step(skill: str, number: int) -> str:
    """Workflow step `number` with its indented continuation paragraphs, up to the next step."""
    workflow = raw_section(skill, "Workflow")
    start = re.search(rf"^{number}\. ", workflow, re.MULTILINE)
    assert start, f"{skill} has no workflow step {number}"
    end = re.compile(r"^\d+[a-z]?\. ", re.MULTILINE).search(workflow, start.end())
    return " ".join(workflow[start.start() : end.start() if end else len(workflow)].split())


def records(skill: str) -> dict[str, dict[str, object]]:
    payload = json.loads((SKILLS / skill / "sources.json").read_text(encoding="utf-8"))
    return {str(source["url"]): source for source in payload["sources"]}


class DatedRuleChangeTests(unittest.TestCase):
    def assert_carries(self, text: str, *terms: str) -> None:
        folded = text.casefold()
        for term in terms:
            with self.subTest(term=term):
                self.assertIn(term.casefold(), folded)

    def assert_cited_and_recorded(self, skill: str, *urls: str) -> None:
        text = skill_text(skill)
        indexed = records(skill)
        for url in urls:
            with self.subTest(skill=skill, url=url):
                self.assertIn(f"]({url})", text)
                record = indexed[url]
                # Either explicitly pending or human-dated, so a person can accept the
                # record; test_coverage_matrix checks an accepted record's digest binding.
                if record.get("verification_status") == PENDING:
                    self.assertEqual(record["checked_at"], "")
                    self.assertRegex(str(record["review_required_since"]), ISO_DATE)
                    self.assertEqual(record["fact"], PENDING_FACT)
                else:
                    self.assertRegex(str(record["checked_at"]), ISO_DATE)

    def test_smsf_lrba_real_property_must_be_business_real_property(self) -> None:
        self.assert_carries(
            workflow_step("au-smsf-year-end", 4),
            "10 August 2026", "Schedule 5", "s 67A(2)(c)", "business real property", "s 66",
            # Exclusions: earlier borrowings and their refinancing, and earlier contracts settling later.
            "refinanc", "settle",
            "life of the LRBA", "s 67(1)", "escalate", "auditor",
        )
        self.assert_carries(section("au-smsf-year-end", "Inputs"), "LRBA")
        self.assert_cited_and_recorded(
            "au-smsf-year-end",
            "https://www.legislation.gov.au/C2026A00049/asmade/text",
            "https://www.legislation.gov.au/C2004A04633/latest/text",
            "https://www.ato.gov.au/individuals-and-families/super-for-individuals-and-families/"
            "self-managed-super-funds-smsf/smsf-investing/restrictions-on-smsf-investments/"
            "smsf-borrowing-restrictions/limited-recourse-borrowing-arrangements/"
            "changes-to-limited-recourse-borrowing-arrangements",
        )

    def test_rental_holiday_home_costs_are_denied_before_apportionment(self) -> None:
        self.assert_carries(
            workflow_step("au-rental-property", 4),
            "s 26-50", "s 26-50(3)(b)(ii)", "at all times", "mainly", "apportion",
            "s 8-1", "advertising", "s 26-50(4)",
            "TR 2026/1", "Appendix 2", "1 July 2026", "fraud", "amended assessment",
            "PCG 2026/3", "cost base",
        )
        self.assert_cited_and_recorded(
            "au-rental-property",
            "https://www.ato.gov.au/law/view/document?DocID=TXR/TR20261/NAT/ATO/00001",
            "https://www.ato.gov.au/law/view/document?DocID=COG/PCG20263/NAT/ATO/00001",
            "https://www.legislation.gov.au/C2004A05138/latest/text",
        )

    def test_agent_consent_record_covers_ai_tools(self) -> None:
        self.assert_carries(
            workflow_step("au-tax-agent-obligations", 3),
            "Code item 6", "AI tool", "TPB(GS) 55/2026", "22 July 2026", "paragraph 23",
            "permission", "due diligence", "responsible practitioner",
            "https://github.com/ryanduguid/llm-tax-guardrails/blob/main/src/data/gs55-concordance.yaml",
        )
        self.assert_carries(section("au-tax-agent-obligations", "Inputs"), "AI tools")
        self.assert_cited_and_recorded(
            "au-tax-agent-obligations",
            "https://www.tpb.gov.au/tpbgs-552026-use-artificial-intelligence-and-code-professional-conduct",
        )

    def test_trust_beneficiary_tfns_move_to_the_statement_of_distribution(self) -> None:
        self.assert_carries(
            workflow_step("au-trust-distributions", 3),
            "closely held trust", "TFN", "1 July 2026", "31 July 2026",
            "statement of distribution", "2027", "withholding",
            # The workpaper records the quote, never the number.
            "TFN itself",
        )
        self.assert_carries(section("au-trust-distributions", "Inputs"), "TFN")
        self.assert_cited_and_recorded(
            "au-trust-distributions",
            "https://www.ato.gov.au/businesses-and-organisations/trusts/trusts-registration-and-reporting-obligations/"
            "closely-held-trusts/tfn-withholding-for-closely-held-trusts/what-trustees-need-to-do",
            "https://www.ato.gov.au/businesses-and-organisations/business-bulletins-newsroom/"
            "changes-to-beneficiary-tfn-reporting-for-closely-held-trusts",
        )

    def test_nonresident_cgt_events_from_1_october_2026_use_the_amended_tests(self) -> None:
        self.assert_carries(
            workflow_step("au-nonresident-cgt", 2),
            "1 October 2026", "Act No. 86 of 2026", "item 39(2)", "s 995-1(1)",
            "water entitlement", "s 855-20", "365 days", "s 855-25(1)(b)", "s 855-25(1A)", "market",
        )
        self.assert_cited_and_recorded(
            "au-nonresident-cgt",
            "https://www.legislation.gov.au/C2026A00086/asmade/text",
            "https://www.legislation.gov.au/C2004A05138/latest/text",
        )

    def test_stp_finalisation_asks_about_changed_reporting_identifiers(self) -> None:
        """stp-finalisation's index takes only human-dated records, so the step dates the agent read."""
        base = "https://www.ato.gov.au/businesses-and-organisations/hiring-and-paying-your-workers/single-touch-payroll/"
        self.assert_carries(
            workflow_step("stp-finalisation", 2),
            "ABN", "branch", "BMS ID", "Payroll ID", "income statement", "duplicate",
            "replacement method", "zeroing out", "finalise", "cancelled",
            "Human review pending", "authorised person",
            f"]({base}changing-your-payroll-solution-or-employees-payroll-ids)",
            f"]({base}correcting-information-reported-through-stp)",
        )
        self.assert_carries(section("stp-finalisation", "Inputs"), "Payroll ID")


if __name__ == "__main__":
    unittest.main()
