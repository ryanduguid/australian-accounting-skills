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
    affirms,
    records,
    section,
    sentences,
    skill_text,
    workflow_step,
)

SKILL = "au-aml-ctf-designated-services"
REPOSITORY = Path(__file__).resolve().parents[1]
CARD = REPOSITORY / "validation" / "cases" / f"{SKILL}-grey-area-services.md"
INCIDENTAL_CARD = REPOSITORY / "validation" / "cases" / f"{SKILL}-incidental-payments-purpose.md"
AUSTRAC_PDS = "https://www.austrac.gov.au/new-austrac/designated-services-newly-regulated-entities/professional-designated-services"
AMENDING_ACT = "https://www.legislation.gov.au/C2024A00110/asmade"
TRANSITIONAL_RULES = "https://www.legislation.gov.au/F2026L00393/latest"


class DesignatedServicesTests(unittest.TestCase):
    def assert_sentence(self, text: str, *patterns: str) -> None:
        """One sentence of `text` affirms every pattern: each matches with no negator directly before it."""
        with self.subTest(patterns=patterns):
            self.assertTrue(
                any(all(affirms(sentence, pattern) for pattern in patterns) for sentence in sentences(text)),
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
        # The incidental payments circumstance cannot clear item 3 while another service is open.
        self.assert_sentence(step, r"\bWhile any other service is `UNDETERMINED`, s 6\(5C\)\(b\) of the AML/CTF Act "
                                   r"cannot be relied on\b", r"\balso `UNDETERMINED`")
        # Review round 3: s 6(5C)(b)(i) bars a designated service in any table, and this skill tests table 6 only.
        self.assert_sentence(step, r"\bs 6\(5C\)\(b\)\(i\) of the AML/CTF Act\b", r"\bany table in s 6\b",
                             r"\bconditional on the AML/CTF compliance officer's view of every other table\b")

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
                               ("Item 3", r"Ask whether the money passes through an account the practice holds"),
                               ("Item 7", r"Ask who holds each position, on whose behalf"),
                               ("Item 9", r"Ask whether the address is made available for that use, now or for an "
                                          r"entity not yet registered, and whether the client entity operates from the "
                                          r"address")):
            with self.subTest(item=item):
                self.assertRegex(step, rf"- {item}: (?:(?!- Item).)*{question}")
        # Advice alone is not ruled out: AUSTRAC treats advice complete enough to act on as item 6.
        self.assert_sentence(step, r"\bcomplete enough for the client to create it without further professional help\b",
                             r"\bassisting under item 6\b")
        self.assert_sentence(step, r"\bwhere the practice only advises, ask whether its advice is that complete\b")
        # Money through the practice's own account is receiving, holding and controlling whatever the
        # client instructs; discretion goes only to managing.
        self.assert_sentence(step, r"\bmoney passes through an account the practice holds and the practice pays it out\b",
                             r"\blikely to be receiving, holding and controlling even where the client instructs each "
                             r"payment\b", r"\bwhich goes to managing\b")
        # Review round 1: none of these may be ruled out on a narrower test than the source states.
        self.assert_sentence(step, r"\bFor item 1\b", r"\bneed not be identified by name, agree the price\b",
                             r"\bauction that meets its reserve succeeds\b",
                             DO_NOT + r"rule item 1 out because no buyer is named\b")
        self.assert_sentence(step, r"\bredirect funds, substitute a party or materially vary the purpose of a dealing\b")
        self.assert_sentence(step, r"\bmade available for an entity to use, or intend to use, as its registered office\b",
                             r"\bfrom the time it is made available\b")
        self.assertRegex(workflow_step(SKILL, 3), r"- item 3: [^;]*securities and securities accounts")
        # Review round 2: item 3 asks AUSTRAC's direct-advancement and what-is-transferred questions for all
        # covered property, and stays undetermined until they are answered.
        item_3 = re.search(r"- Item 3: .*", step)
        self.assertIsNotNone(item_3)
        item_3_text = item_3.group(0) if item_3 else ""
        self.assert_sentence(item_3_text, r"\bsecurities and securities accounts, virtual assets or other property\b",
                             r"\bdirectly advances a transaction rather than merely influencing it\b")
        self.assert_sentence(item_3_text, r"\bAsk what money or other property the practice deals with\b",
                             r"\bwhether its dealing directly advances that transaction\b")
        self.assert_sentence(item_3_text, r"\bmaterially change who is paid or what is transferred\b")
        self.assert_sentence(item_3_text, r"\bitem 3 stays `UNDETERMINED`")
        # Review round 3: known facts that fail an element rule item 3 out; they do not record it.
        self.assert_sentence(item_3_text, r"\bRecord item 3 only where the facts meet each element\b",
                             r"\bdirect-advancement test as the regulator's view\b")
        self.assert_sentence(item_3_text, r"\bonly influences the transaction\b",
                             r"\bname that element as ruled out, labelled as AUSTRAC's view\b")
        self.assert_sentence(item_3_text, r"\bmanaging is less likely, not ruled out\b", r"\bstep 6\b")
        self.assertNotRegex(item_3_text, r"\bonce the facts establish them\b")

    def test_the_second_limb_of_s_6_5c_b_holds_item_3_open_once_the_first_is_met(self) -> None:
        # Review round 3: s 6(5C)(b) has a second limb, payments reasonably incidental to a service that is not
        # designated, and a result resting on it stays open until both limbs are recorded as met.
        item_3 = re.search(r"- Item 3: .*", workflow_step(SKILL, 4))
        self.assertIsNotNone(item_3)
        item_3_text = item_3.group(0) if item_3 else ""
        self.assert_sentence(item_3_text, r"\bs 6\(5C\)\(b\)\(ii\) of the AML/CTF Act\b",
                             r"\bwhich service that is not a designated service the payments support\b",
                             r"\bonly for payments reasonably incidental to that service\b")
        self.assert_sentence(item_3_text, r"\bde facto bank account\b", r"\blabelled as AUSTRAC's view\b")
        self.assert_sentence(item_3_text, r"\bUntil both limbs of s 6\(5C\)\(b\) of the AML/CTF Act are recorded as "
                                          r"met\b", r"\bstays `UNDETERMINED`")
        # Review round 4: the grey-area card's S2 defeats the first limb, so a separate card meets it and leaves
        # only the second open.
        raw = INCIDENTAL_CARD.read_text(encoding="utf-8")
        self.assertIn(f"  - {SKILL}\n", raw)
        card = " ".join(raw.split())
        self.assertIn("The AML/CTF compliance officer has recorded that the practice provides no designated service "
                      "in any table in s 6 of the AML/CTF Act other than item 3 of table 6.", card)
        self.assertIn("Which service that is not a designated service, if any, the S2 payments support", card)
        self.assertIn("Record S2 as undetermined: name the missing fact on which service that is not a designated "
                      "service the payments support", card)
        self.assertIn("Do not clear S2 under s 6(5C)(b) on the first limb alone", card)

    def test_each_service_gets_one_of_3_results_and_a_grey_area_is_not_decided(self) -> None:
        step = workflow_step(SKILL, 6)
        self.assert_sentence(step, r"`item N`", r"\bmeet every element of the item\b")
        self.assert_sentence(step, r"`none`", r"\brule out an element of every item\b")
        # A wrong none is the costly error: guidance that leaves a fact open cannot rule an element out.
        self.assert_sentence(step, r"\bAn element is not ruled out while AUSTRAC's guidance makes it depend on a fact "
                                   r"still missing\b", r"\bonly on AUSTRAC's view, not the Act's words, is labelled as "
                                   r"the regulator's view\b")
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
        # Item 12 also excludes a practice that had commenced, but not yet provided, another service.
        self.assert_sentence(step, r"\bbefore 1 July 2026\b",
                             r"\bneither provided nor had commenced to provide any other designated service\b",
                             r"\bitem 12 of that Schedule sets the date as 29 July 2026\b")
        # Review round 2: item 12 also covers item 2 of table 2 and table 5, which this skill does not test.
        self.assert_sentence(step, r"\bitem 12 of that Schedule\b",
                             r"\bcovered by item 2 of table 2, or an item of table 5 or 6, in s 6 of the AML/CTF Act\b")
        # Review round 3: item 12(1)(b) bars another designated service in any table, so the date is conditional
        # on every other table, not only item 2 of table 2 and table 5.
        self.assert_sentence(step, r"\b29 July 2026 date as conditional on the AML/CTF compliance officer's view of "
                                   r"every other table in s 6 of the AML/CTF Act\b", r"\bitem 2 of table 2 or table 5\b",
                             r"\bunder any other table\b")
        # Review round 2: s 26F(8) bars commencing a designated service to a customer, in the Act's words.
        self.assert_sentence(step, r"\bmust not commence to provide a designated service to a customer\b",
                             r"\(s 26F\(8\) of the AML/CTF Act\)")
        self.assertNotRegex(step, r"\bbegins to provide designated services\b")
        # Documenting the program (s 26N) and approving the assessment and policies (s 26P) are separate duties.
        self.assert_sentence(step, r"\bprogram documented \(s 26N of the AML/CTF Act\)",
                             r"\bapproved by a senior manager \(s 26P of the AML/CTF Act\)")
        self.assertRegex(step, r"s 26M\(1\) of the AML/CTF Act\), which s 19 of the \*Anti-Money Laundering and "
                               r"Counter-Terrorism Financing Transitional Rules 2026\*")
        for provision in (r"ss 26C to 26E", r"s 26F\(8\)", r"ss 26J and 26K", r"s 26N ", r"s 26P ", r"s 28 ", r"s 30 ",
                          r"s 41 ", r"s 43 ", r"s 47 ", r"ss 107 and 108", r"s 111 ", r"s 116 "):
            with self.subTest(provision=provision):
                self.assertRegex(step, rf"\({provision}[^)]*of the AML/CTF Act\)")
        # Review round 3: rule 9-9 sets periods for compliance reports, not for ss 41 and 43.
        self.assert_sentence(step, r"\bs 9-9 of the AML/CTF Rules apply to AML/CTF compliance reports only\b")
        self.assert_sentence(step, r"\bpre-commencement customer rules in s 36 of the AML/CTF Act\b")
        self.assert_sentence(step, r"\blist them as conditional on that result\b")
        self.assert_sentence(step, r"`au-tax-agent-obligations` step 8a", r"`au-aml-ctf-client-coverage`", r"`au-client-acceptance`")

    def test_what_the_skill_leaves_out_is_named(self) -> None:
        step = workflow_step(SKILL, 8)
        self.assert_sentence(step, r"\btests table 6 only\b",
                             r"`none` means no table 6 item, not that the practice provides no designated service\b",
                             r"\banother table in s 6 of the AML/CTF Act\b")
        self.assert_sentence(step, r"\bclient's ML/TF risk\b", r"\bcontent of the AML/CTF program\b",
                             r"\bnot covered by any skill in this pack\b")
        self.assert_sentence(step, r"\bclient email or engagement template\b", r"\breliance on another entity's customer due diligence\b",
                             r"\bnot covered\b")

    def test_the_example_classifies_recorded_steps_not_service_names(self) -> None:
        # Review round 3: step 1 forbids a result from a name, so each service in the example carries its steps.
        example = " ".join(section(SKILL, "Fabricated acceptance example").split())
        self.assert_sentence(example, r"\beach recorded with its steps\b")
        for service, steps in (("tax returns", r"holds no client money and takes no part in any sale, financing or "
                                               r"restructure"),
                               ("trust setup", r"drafts a new trust's deed and arranges its execution"),
                               ("bill paying", r"receives clients' money into its own bank account"),
                               ("address", r"makes its office address available")):
            with self.subTest(service=service):
                self.assertRegex(example, rf"{service}[^;]*{steps}")

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
        # S3 is grey only while it is unknown whose account the money passes through.
        self.assertIn("name the missing facts on whose account the money passes through and on discretion", card)
        self.assertIn("Do not record S3 as not designated because the partner says so", card)
        self.assertIn("Record S4 as undetermined until its steps are recorded", card)
        cases = yaml.safe_load((REPOSITORY / "validation" / "routing-cases.yaml").read_text(encoding="utf-8"))
        self.assertIn(SKILL, {case["skill"] for case in cases})


if __name__ == "__main__":
    unittest.main()
