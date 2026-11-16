# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The designated services skill added on 16 November 2026 classifies services and decides no grey area.

Each test reads one step, the sources or the card and checks the rule a reader
could get wrong: table 6's 9 items are tested from the Act, item 3 last; each
service gets one of 3 results, and a grey area the facts do not settle stays
undetermined; AUSTRAC's guidance is the regulator's view, never the law; each
obligation carries its provision and date; and what the skill leaves out is
named. It checks wording, not model behaviour. The helpers are in
skill_prose.py.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

import yaml

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

SKILL = "au-aml-ctf-designated-services"
REPOSITORY = Path(__file__).resolve().parents[1]
CARD = REPOSITORY / "validation" / "cases" / f"{SKILL}-grey-area-services.md"
AUSTRAC_PDS = "https://www.austrac.gov.au/new-austrac/designated-services-newly-regulated-entities/professional-designated-services"
AMENDING_ACT = "https://www.legislation.gov.au/C2024A00110/asmade"
TRANSITIONAL_RULES = "https://www.legislation.gov.au/F2026L00393/latest"


class DesignatedServicesTests(unittest.TestCase):
    def assert_sentence(self, text: str, *patterns: str) -> None:
        """One sentence of `text` matches every pattern."""
        with self.subTest(patterns=patterns):
            self.assertTrue(
                any(all(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)
                    for sentence in sentences(text)),
                f"no sentence matches all of {patterns}",
            )

    def test_a_service_known_only_by_name_stays_undetermined(self) -> None:
        step = workflow_step(SKILL, 1)
        self.assert_sentence(step, r"\brecorded only by a name\b", r"`UNDETERMINED` until its steps are recorded\b",
                             DO_NOT + r"infer the steps from the name\b")
        self.assert_sentence(step, r"\bone row per service, not per client\b")

    def test_threshold_facts_cite_the_geographical_link_and_business_groups(self) -> None:
        step = workflow_step(SKILL, 2)
        self.assert_sentence(step, r"\bcompilation 63 \(C2026C00447, in force from 1 October 2026\) on 16 November 2026\b")
        self.assert_sentence(step, r"\bs 6\(6\) of the AML/CTF Act\b", r"\bpermanent establishment\b")
        self.assert_sentence(step, r"\bs 6\(6A\) of the AML/CTF Act\b",
                             r"\bleave whether the conditions are met to the AML/CTF compliance officer\b")

    def test_table_6_lists_its_9_items_and_tests_item_3_last(self) -> None:
        step = workflow_step(SKILL, 3)
        self.assert_sentence(step, r"\btable 6, the professional services table in s 6\(5B\) of the AML/CTF Act\b")
        for item, subject in ((1, r"real estate"), (2, r"body corporate or legal arrangement"),
                              (3, r"s 6\(5C\) of the AML/CTF Act"), (4, r"equity or debt financing"),
                              (5, r"shelf company"), (6, r"creation or restructuring"),
                              (7, r"s 6\(5E\) of the AML/CTF Act"), (8, r"nominee shareholder"),
                              (9, r"registered office or principal place of business address")):
            with self.subTest(item=item):
                self.assertRegex(step, rf"- item {item}: [^;]*{subject}")
        self.assertNotRegex(step, r"- item 10:")
        self.assert_sentence(step, r"\bs 6\(5C\)\(b\) of the AML/CTF Act\b", r"\bno designated service other than item 3\b",
                             r"\btest item 3 last\b")

    def test_austrac_guidance_is_the_regulators_view_not_the_law(self) -> None:
        step = workflow_step(SKILL, 4)
        self.assert_sentence(step, r"\brecord it as the regulator's view, never as the law\b",
                             r"\bdepends on the facts, ask for those facts\b")
        self.assert_sentence(workflow_step(SKILL, 2), r"\blast updated 25 September 2026\b",
                             r"\bregulator's view, not the law\b")
        hand_off = section(SKILL, "Hand-off and checks")
        self.assert_sentence(hand_off, r"\bAUSTRAC guidance relied on labelled as the regulator's view with its last updated date\b")
        # Each grey area asks for the facts that decide it.
        for item, question in (("Items 1, 2, 4 and 6", r"Ask whether the practice is instructed to act"),
                               ("Item 6", r"Ask whether the work creates an entity or changes its legal form"),
                               ("Item 3", r"Ask whether money passes through an account the practice controls"),
                               ("Item 7", r"Ask who holds each position, on whose behalf"),
                               ("Item 9", r"Ask whether the client entity operates from the address")):
            with self.subTest(item=item):
                self.assertRegex(step, rf"- {item}: (?:(?!- Item).)*{question}")

    def test_each_service_gets_one_of_3_results_and_a_grey_area_is_not_decided(self) -> None:
        step = workflow_step(SKILL, 6)
        self.assert_sentence(step, r"`item N`", r"\bmeet every element of the item\b")
        self.assert_sentence(step, r"`none`", r"\brule out an element of every item\b")
        self.assert_sentence(step, r"`UNDETERMINED`: a fact is missing\b", r"\bthe facts recorded do not settle it\b")
        self.assert_sentence(step, r"\bName the missing fact or the professional view needed, and who should form it\b")
        self.assert_sentence(step, r"\bWhere the facts leave a grey area unsettled, return `UNDETERMINED`",
                             r"\bprofessional view is needed\b")
        self.assert_sentence(step, DO_NOT + r"choose the more or less cautious answer\b",
                             DO_NOT + r"treat AUSTRAC's guidance as settling a question\b")
        self.assertIn("Every service has exactly one result.", section(SKILL, "Hand-off and checks"))

    def test_each_obligation_carries_its_provision_and_date(self) -> None:
        step = workflow_step(SKILL, 7)
        self.assert_sentence(step, r"\bSchedule 3 to the \*Anti-Money Laundering and Counter-Terrorism Financing Amendment Act 2024\* inserted table 6 and commenced on 31 March 2026\b",
                             r"\bitem 2 of that Act's commencement table\b")
        self.assert_sentence(step, r"\bItem 11 of that Schedule\b", r"\bPart 1A\b", r"\bPart 2\b", r"\bPart 3\b",
                             r"\bDivisions 2 to 6 of Part 10\b", r"\buntil 1 July 2026\b")
        self.assert_sentence(step, r"\bwithin 28 days after first providing a designated service \(s 51B\(1\) of the AML/CTF Act\)")
        self.assert_sentence(step, r"\bbefore 1 July 2026\b", r"\bno other designated service\b",
                             r"\bitem 12 of that Schedule sets the date as 29 July 2026\b")
        self.assertRegex(step, r"s 26M\(1\) of the AML/CTF Act\), which s 19 of the \*Anti-Money Laundering and "
                               r"Counter-Terrorism Financing Transitional Rules 2026\*")
        for provision in (r"ss 26C to 26E", r"s 26F\(8\)", r"ss 26J and 26K", r"ss 26N and 26P", r"s 28 ", r"s 30 ",
                          r"s 41 ", r"s 43 ", r"s 47 ", r"ss 107 and 108", r"s 111 ", r"s 116 "):
            with self.subTest(provision=provision):
                self.assertRegex(step, rf"\({provision}[^)]*of the AML/CTF Act\)")
        self.assert_sentence(step, r"\bs 9-9 of the AML/CTF Rules\b")
        self.assert_sentence(step, r"\bpre-commencement customer rules in s 36 of the AML/CTF Act\b")
        self.assert_sentence(step, r"\blist them as conditional on that result\b")
        self.assert_sentence(step, r"`au-tax-agent-obligations` step 8a", r"`au-aml-ctf-client-coverage`", r"`au-client-acceptance`")

    def test_what_the_skill_leaves_out_is_named(self) -> None:
        step = workflow_step(SKILL, 8)
        self.assert_sentence(step, r"\bclient's ML/TF risk\b", r"\bcontent of the AML/CTF program\b",
                             r"\bnot covered by any skill in this pack\b")
        self.assert_sentence(step, r"\bclient email or engagement template\b", r"\breliance on another entity's customer due diligence\b",
                             r"\bnot covered\b")

    def test_the_advice_note_appears_once(self) -> None:
        self.assertEqual(skill_text(SKILL).count("It is not tax, legal or financial advice."), 1)
        self.assertNotRegex(skill_text(SKILL), r"(?i)\byou are (?:not )?(?:a )?reporting entity\b")

    def test_sources_are_pending_agent_reads(self) -> None:
        found = records(SKILL)
        for url in (AUSTRAC_PDS, AMENDING_ACT, TRANSITIONAL_RULES, "https://www.legislation.gov.au/C2006A00169/latest",
                    "https://www.legislation.gov.au/F2025L01026/latest", "https://www.legislation.gov.au/F2007L01000/latest"):
            with self.subTest(url=url):
                self.assertIn(url, found)
        for url, record in found.items():
            with self.subTest(url=url):
                self.assertEqual(record["verification_status"], PENDING)
                self.assertEqual(record["fact"], PENDING_FACT)
                self.assertEqual(record["checked_at"], "")
                self.assertRegex(str(record["review_required_since"]), ISO_DATE)
        self.assertIn("last updated 25 September 2026", str(found[AUSTRAC_PDS]["limitations"]))
        self.assertIn("not law", str(found[AUSTRAC_PDS]["limitations"]))

    def test_the_card_and_routing_case_exercise_the_grey_area(self) -> None:
        card = " ".join(CARD.read_text(encoding="utf-8").split())
        self.assertIn(f"  - {SKILL}\n", CARD.read_text(encoding="utf-8"))
        self.assertIn("Record S3 as undetermined", card)
        self.assertIn("Do not record S3 as not designated because the partner says so", card)
        self.assertIn("Record S4 as undetermined until its steps are recorded", card)
        cases = yaml.safe_load((REPOSITORY / "validation" / "routing-cases.yaml").read_text(encoding="utf-8"))
        self.assertIn(SKILL, {case["skill"] for case in cases})


if __name__ == "__main__":
    unittest.main()
