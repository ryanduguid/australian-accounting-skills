# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""Keep payroll source routes and statutory differences with their jurisdictions."""

from __future__ import annotations

import unittest

import test_dated_rule_changes as gates

JURISDICTIONS = (
    ("New South Wales", "Revenue NSW", "legislation.nsw.gov.au", "revenue.nsw.gov.au"),
    ("Victoria", "State Revenue Office Victoria", "legislation.vic.gov.au", "sro.vic.gov.au"),
    ("Queensland", "Queensland Revenue Office", "legislation.qld.gov.au", "qro.qld.gov.au"),
    ("Western Australia", "RevenueWA", "legislation.wa.gov.au", "wa.gov.au"),
    ("South Australia", "RevenueSA", "legislation.sa.gov.au", "revenuesa.sa.gov.au"),
    ("Tasmania", "State Revenue Office of Tasmania", "legislation.tas.gov.au", "sro.tas.gov.au"),
    ("Australian Capital Territory", "ACT Revenue Office", "legislation.act.gov.au", "revenue.act.gov.au"),
    ("Northern Territory", "Territory Revenue Office", "legislation.nt.gov.au", "treasury.nt.gov.au"),
)


class PayrollJurisdictionTests(unittest.TestCase):
    def assert_sentence(self, text: str, *patterns: str) -> None:
        self.assertTrue(
            any(all(gates.affirms(sentence, pattern) for pattern in patterns)
                for sentence in gates.sentences(text)),
            f"No affirmative sentence carries {patterns}: {text}",
        )

    def test_each_state_routes_grouping_registration_and_reconciliation(self) -> None:
        for name, office, act_host, revenue_host in JURISDICTIONS:
            with self.subTest(jurisdiction=name):
                cells = gates.table_row("au-payroll-tax-states", "Primary-source starting point", name)
                self.assertEqual(len(cells), 5)
                self.assertIn(office, cells[0])
                self.assertIn(act_host, cells[1])
                self.assertIn(revenue_host, cells[2])
                if name == "Northern Territory":
                    self.assertIn("same guide", cells[3])
                    self.assertIn("same guide", cells[4])
                else:
                    self.assertIn(revenue_host, cells[3])
                    self.assertIn(revenue_host, cells[4])
        step = gates.workflow_step("au-payroll-tax-states", 3)
        self.assert_sentence(step, r"\bread who in a group must register\b", r"\bjurisdiction's own\b")
        self.assert_sentence(step, r"\bdo not carry one office's rule to another\b")

    def test_each_contractor_route_has_its_own_act_and_revenue_office(self) -> None:
        for name, _, act_host, revenue_host in JURISDICTIONS:
            with self.subTest(jurisdiction=name):
                cells = gates.table_row("payroll-tax-contractors", "Other states and territories", name)
                self.assertEqual(len(cells), 4)
                self.assertIn(revenue_host, cells[0])
                self.assertIn(act_host, cells[1])
        intro = gates.skill_text("payroll-tax-contractors").split("## Inputs needed", 1)[0]
        self.assert_sentence(intro, r"\bNSW steps do not decide it\b")

    def test_victorian_and_queensland_exclusions_stay_out_of_nsw(self) -> None:
        vic = gates.table_row("payroll-tax-contractors", "Other states and territories", "Victoria")[3]
        self.assert_sentence(vic, r"\bexcludes services solely\b", r"\bprocurement\b", r"s 32\(2\)\(d\)\(ii\)")
        self.assert_sentence(vic, r"\bdoor-to-door sale\b", r"\bsolely for domestic purposes\b", r"s 32\(2\)\(d\)\(iii\)")
        qld = gates.table_row("payroll-tax-contractors", "Other states and territories", "Queensland")[3]
        self.assert_sentence(qld, r"\bexcludes insurance procurement\b", r"\bdoor-to-door sales\b", r"13B\(2\)\(d\)")

    def test_wa_does_not_import_relevant_contract_exemptions(self) -> None:
        wa = gates.table_row("payroll-tax-contractors", "Other states and territories", "Western Australia")
        self.assert_sentence(wa[1], r"\b(?:has|contains) no relevant contract provisions\b")
        self.assert_sentence(wa[1], r"\bnot harmonised\b", r"\bcontractors\b")
        self.assert_sentence(wa[1], r"\bakin to employment\b", r"\btotality of the relationship\b")
        self.assert_sentence(wa[3], r"\b(?:do not|never) apply steps 3 to 6\b")
        self.assert_sentence(wa[3], r"\bread the regulations\b", r"9AA\(1\)\(c\)")

    def test_act_does_not_import_day_count_or_engagement_exclusions(self) -> None:
        act = gates.table_row("payroll-tax-contractors", "Other states and territories", "Australian Capital Territory")[3]
        self.assert_sentence(act, r"\bhas no day-count (?:exclusion|exemption)\b", r"\bno exclusion for a contractor who engages others\b")
        self.assert_sentence(act, r"\bhas only (?:4|four) exclusions\b", r"32\(2\)\(b\)\(ii\)", r"32\(2\)\(c\)")

    def test_sa_unread_act_and_tas_nt_numbering_limits_remain_explicit(self) -> None:
        scope = gates.section("payroll-tax-contractors", "Other states and territories")
        self.assert_sentence(scope, r"\bSouth Australian register refused\b", r"\brow rests on RevenueSA's (?:published )?guidance\b")
        sa = gates.table_row("payroll-tax-contractors", "Other states and territories", "South Australia")[3]
        self.assert_sentence(sa, r"\bread the Act\b", r"\bbefore citing any other section\b")
        for name in ("Tasmania", "Northern Territory"):
            row = gates.table_row("payroll-tax-contractors", "Other states and territories", name)
            self.assertIn("ss 37 to 42", row[2])
            self.assert_sentence(row[3], r"\bhas no s 36A\b", r"\bno counterpart\b")

    def test_new_guidance_records_remain_discovery_only(self) -> None:
        for skill, heading in (("au-payroll-tax-states", "Primary-source starting point"),
                               ("payroll-tax-contractors", "Other states and territories")):
            scope = gates.section(skill, heading)
            self.assertIn("Human review pending", scope)
            self.assertIn("not a human review", scope)
            pending = [record for record in gates.records(skill).values()
                       if record.get("review_required_since") == "2026-11-04"]
            self.assertEqual(len(pending), 8 if skill == "au-payroll-tax-states" else 7)
            for record in pending:
                self.assertEqual(record["verification_status"], gates.PENDING)
                self.assertEqual(record["checked_at"], "")
                self.assertEqual(record["fact"], gates.PENDING_FACT)

    def test_no_revenue_office_contact_authority_is_added(self) -> None:
        text = gates.section("payroll-tax-contractors", "Boundaries")
        self.assert_sentence(text, r"\bdo not lodge, register, or correspond\b", r"\bany other revenue office\b")


if __name__ == "__main__":
    unittest.main()
