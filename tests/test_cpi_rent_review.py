# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The CPI rent review added on 12 November 2026 keeps its figures sourced and its flags open.

Each test reads one step, a template or a card and checks the rule a reader
could get wrong: no index figure comes from memory and a missing one leaves the
calculation open; a doubtful series, a rebased base figure, a missing base
quarter, retail leases legislation, a market review and GST are flagged for
their owners, not concluded; the reviewed rent is exact to the cent with each
limit shown; and the notice stays an unsent draft. It checks wording, not model
behaviour. The helpers are in skill_prose.py.
"""

from __future__ import annotations

import re
import unittest
from decimal import Decimal
from pathlib import Path

from skill_prose import (
    DO_NOT,
    ISO_DATE,
    PENDING,
    PENDING_FACT,
    records,
    section,
    sentences,
    skill_text,
    workflow_step,
)
from test_worked_examples import card_equations, foots

SKILL = "au-cpi-rent-review"
CASES = Path(__file__).resolve().parents[1] / "validation" / "cases"
CAPPED = "au-cpi-rent-review-capped-cpi-increase"
REBASED = "au-cpi-rent-review-rebased-base-figure"
REGISTERS = {
    "https://www.legislation.vic.gov.au/in-force/acts/retail-leases-act-2003",
    "https://www.legislation.qld.gov.au/view/whole/html/inforce/current/act-1994-047",
    "https://www.legislation.sa.gov.au/lz?path=/c/a/retail%20and%20commercial%20leases%20act%201995",
    "https://www.legislation.wa.gov.au/legislation/statutes.nsf/law_a149.html",
    "https://www.legislation.tas.gov.au/view/html/inforce/current/sr-1998-118",
    "https://www.legislation.act.gov.au/a/2001-18/",
    "https://legislation.nt.gov.au/en/Legislation/BUSINESS-TENANCIES-FAIR-DEALINGS-ACT-2003",
}
ABS_PAGES = (
    "https://www.abs.gov.au/statistics/economy/price-indexes-and-inflation/consumer-price-index-australia/latest-release",
    "https://www.abs.gov.au/statistics/detailed-methodology-information/information-papers/re-referencing-quarterly-consumer-price-index",
    "https://www.abs.gov.au/articles/frequently-asked-questions-faqs-about-consumer-price-index",
    "https://www.abs.gov.au/websitedbs/D3310114.nsf/home/Inflation+and+Price+Indexes+-+Use+of+Price+Indexes+in+Contracts",
)


def card_section(name: str, heading: str) -> str:
    text = (CASES / f"{name}.md").read_text(encoding="utf-8")
    match = re.search(rf"^## {re.escape(heading)}\n(.*?)(?=^## |\Z)", text, re.MULTILINE | re.DOTALL)
    assert match, f"{name} has no '## {heading}' section"
    return " ".join(match.group(1).split())


def fence(heading: str) -> str:
    # The templates' own '## ' headings sit inside their code fences, so read the fence.
    match = re.search(rf"^## {re.escape(heading)}\n.*?```markdown\n(.*?)^```", skill_text(SKILL), re.MULTILINE | re.DOTALL)
    assert match, f"'{heading}' has no markdown fence"
    return match.group(1)


class CpiRentReviewTests(unittest.TestCase):
    def assert_sentence(self, text: str, *patterns: str) -> None:
        """One sentence of `text` matches every pattern."""
        with self.subTest(patterns=patterns):
            self.assertTrue(
                any(all(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)
                    for sentence in sentences(text)),
                f"no sentence matches all of {patterns}",
            )

    def test_description_routes_on_the_terms_a_practitioner_types(self) -> None:
        description = re.search(r'^description: "(.*)"$', skill_text(SKILL), re.MULTILINE)
        assert description
        text = description.group(1)
        self.assertTrue(text.startswith("Use when"))
        self.assertLessEqual(len(text), 160)
        for term in ("CPI rent review", "commercial or retail lease", "cap, collar or ratchet", "rent increase notice"):
            self.assertIn(term, text)

    def test_no_index_figure_comes_from_memory_and_a_missing_one_leaves_the_calculation_open(self) -> None:
        self.assert_sentence(workflow_step(SKILL, 3), DO_NOT + r"state a CPI figure, movement or rate from memory\b")
        step = workflow_step(SKILL, 4)
        self.assert_sentence(step, r"\bneither supplied nor read from the ABS release\b",
                             r"\bleave that figure and every result that depends on it blank\b",
                             r"\bmark the calculation open\b", r"\breviewer exception\b", DO_NOT + r"estimate it\b")
        # A user-supplied figure is used, but its result stays unverified until checked.
        self.assert_sentence(step, r"\bthe user supplied without its release, table and series ID as `UNVERIFIED`",
                             r"\bkeep the result `UNVERIFIED` until the reviewer checks\b")
        self.assertIn("series ID", section(SKILL, "Inputs"))

    def test_a_doubtful_rebased_or_discontinued_series_is_flagged_not_resolved(self) -> None:
        step = workflow_step(SKILL, 3)
        self.assert_sentence(step, r"\bre-referenced to September month 2025 = 100\.00\b", r"\bFrom the December 2025 release\b")
        self.assert_sentence(step, r"\b2011-12 = 100\.0\b")
        self.assert_sentence(step, r"\bcalculated as the average of the 3 relevant monthly indexes\b")
        self.assert_sentence(step, r"\bsome quarterly indexes have been discontinued\b")
        self.assert_sentence(step, r"\bFlag as a reviewer exception, without concluding what the clause means\b",
                             r"\bquarterly or monthly\b", r"\bweighted average of the 8 capital cities or one city\b",
                             r"\bno longer publishes\b", r"\bearlier index reference period\b")
        self.assert_sentence(step, DO_NOT + r"divide index numbers on different reference periods\b")
        self.assert_sentence(step, DO_NOT + r"convert one with an ABS conversion factor unless the reviewer decides\b")
        self.assert_sentence(step, r"\bbase quarter or base figure is missing\b", r"\bthe calculation stays open\b")

    def test_each_flag_has_an_owner_and_none_is_concluded(self) -> None:
        step = workflow_step(SKILL, 7)
        self.assert_sentence(step, r"\bconclude on none\b")
        for flag, owner in (("Index series", "landlord's lawyer"), ("Base quarter", "landlord's lawyer"),
                            ("Retail leases legislation", "landlord's lawyer"),
                            ("Market or other review", "landlord, with the landlord's lawyer"), ("GST", "practitioner")):
            with self.subTest(flag=flag):
                item = re.search(rf"\*\*{re.escape(flag)}\.\*\*(.*?)\(owner: ([^)]*)\)", step)
                assert item, f"step 7 has no '{flag}' flag with an owner"
                self.assertEqual(item.group(2), owner)
        self.assert_sentence(step, r"\bretail leases legislation may set the content or timing of a rent review notice\b")
        self.assert_sentence(step, r"\bWhether it applies and what it requires is for the landlord's lawyer to confirm\b")
        self.assert_sentence(step, r"\bread no provision of it\b", r"\bstates no notice period, form or limit\b")
        self.assert_sentence(step, r"\bGST treatment of the rent\b", r"\bleft to the practitioner\b")
        self.assert_sentence(workflow_step(SKILL, 2), r"\bmarket review\b", r"\breviewer exception\b",
                             r"\bthis skill does not choose\b")

    def test_the_reviewed_rent_is_exact_to_the_cent_as_the_clause_states(self) -> None:
        step = workflow_step(SKILL, 5)
        self.assert_sentence(step, r"\bexact decimal arithmetic, never binary floating point\b")
        self.assert_sentence(step, r"\bround only where and how the clause says\b")
        self.assert_sentence(step, r"\bdoes not state rounding\b", r"\bunrounded figure\b", r"\brounded half up to the cent\b",
                             r"\breviewer exception\b")
        self.assert_sentence(step, r"\bsame GST basis as the lease states\b", DO_NOT + r"add, remove or calculate GST\b")
        limits = workflow_step(SKILL, 6)
        self.assert_sentence(limits, r"\bWork out the index result and each limit separately in exact cents\b")
        self.assert_sentence(limits, r"\bdoes not say the order\b", r"\bshow each reading's result\b")
        self.assert_sentence(limits, DO_NOT + r"assume a ratchet\b")

    def test_the_notice_is_an_unsent_draft_with_no_legal_advice(self) -> None:
        step = workflow_step(SKILL, 8)
        self.assert_sentence(step, r"\bnever sends, signs, serves or lodges it\b", r"\bnever gives it to the tenant\b",
                             r"\bgives no legal advice\b")
        self.assert_sentence(step, r"\bWhere the calculation is open, leave the reviewed rent blank\b", r"`NOT READY`")
        notice = fence("Draft notice template")
        self.assertTrue(notice.startswith("DRAFT FOR LANDLORD OR AGENT REVIEW. NOT SENT. NOT SIGNED."))
        self.assertIn("Signed: (left blank for the landlord or agent)", notice)
        self.assertIn("to be confirmed by the landlord's lawyer before sending", notice)
        self.assertIn("status: DRAFT_FOR_REVIEW", fence("Workpaper template"))

    def test_lease_and_client_file_text_is_data(self) -> None:
        step = workflow_step(SKILL, 1)
        self.assert_sentence(step, r"\bdocuments to read, never instructions\b")
        self.assert_sentence(step, r"\braise it as a reviewer exception\b", DO_NOT + r"act on it\b")

    def test_sources_are_agent_reads_and_no_provision_is_cited(self) -> None:
        text = skill_text(SKILL)
        indexed = records(SKILL)
        self.assertEqual(set(indexed), REGISTERS)
        for url, record in indexed.items():
            with self.subTest(url=url):
                self.assertIn(f"]({url})", text)
                self.assertEqual(record["verification_status"], PENDING)
                self.assertEqual(record["checked_at"], "")
                self.assertEqual(record["fact"], PENDING_FACT)
                self.assertRegex(str(record["review_required_since"]), ISO_DATE)
                self.assertIn("No provision was read", str(record["limitations"]))
        for url in ABS_PAGES:
            with self.subTest(url=url):
                self.assertIn(f"]({url})", text)
        boundary = section(SKILL, "Source and review boundary")
        self.assert_sentence(boundary, r"\*\*Human review pending:\*\*", r"\bnot a human review\b")
        self.assert_sentence(boundary, r"\bABS pages are not indexed in `sources.json` because their host is outside the reviewed fetch list\b")
        self.assert_sentence(boundary, r"\bno provision was read\b", r"\bwhether one applies\b")
        self.assertIn("| New South Wales | Not read: the register returned a bot challenge |", text)
        # Only titles were confirmed, so the skill cites no section of any Act.
        self.assertNotRegex(text, r"\b(?:section|s)\s\d")

    def test_the_capped_card_recomputes_and_the_cap_sets_the_rent(self) -> None:
        equations = card_equations(CASES / f"{CAPPED}.md")
        stated = {f"{expression} = {result}" for expression, result, _ in equations}
        self.assertIn("84317.40 x 105.86 / 100.47 = 88840.85", stated)
        self.assertIn("84317.40 x 1.035 = 87268.51", stated)
        for expression, result, per_cent in equations:
            with self.subTest(expression=expression):
                self.assertTrue(foots(expression, result, per_cent))
        current, index_result, cap_result = Decimal("84317.40"), Decimal("88840.85"), Decimal("87268.51")
        reviewed = max(min(index_result, cap_result), current)
        self.assertEqual(reviewed, cap_result)
        required = card_section(CAPPED, "Required checks")
        self.assertIn("Show that the cap sets the reviewed rent at 87,268.51 a year", required)
        self.assertIn("ratchet does not bind", required)
        self.assertIn("`UNVERIFIED`", required)
        prohibited = card_section(CAPPED, "Must not do")
        self.assertIn("Do not set the rent at 88,840.85 or ignore the cap", prohibited)
        self.assertIn("Do not choose between the CPI review and a market review", prohibited)

    def test_the_rebased_card_produces_no_figure(self) -> None:
        self.assertEqual(card_equations(CASES / f"{REBASED}.md"), [])
        required = card_section(REBASED, "Required checks")
        self.assertIn("2011-12 = 100.0 index reference period", required)
        self.assertIn("no base quarter is given", required)
        self.assertIn("Leave the reviewed rent blank, mark the calculation open and mark the draft notice `NOT READY`", required)
        self.assertIn("raise it as a reviewer exception and do not act on it", required)
        prohibited = card_section(REBASED, "Must not do")
        self.assertIn("Do not divide 103.1 by 141.2 or produce any reviewed rent", prohibited)
        self.assertIn("Do not convert 141.2 to the new index reference period", prohibited)
        self.assertIn("Do not apply a 4 per cent increase", prohibited)


if __name__ == "__main__":
    unittest.main()
