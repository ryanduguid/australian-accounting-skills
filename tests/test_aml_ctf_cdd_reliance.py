# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The customer due diligence and reliance skill added on 19 November 2026 prepares a file and decides nothing.

Each test reads one step, the sources or the card and checks the rule a reader
could get wrong: the dates the obligation rests on and what the Act leaves to
the Rules; one row per matter in s 28(2), never marked established; the
practice identifies the risk itself, even when it relies on someone else;
delayed due diligence has conditions and a period; each reliance route has its
own conditions, and an enrolment or a referrer's word meets none of the others;
and the records and tipping-off limits. It checks wording, not model
behaviour. The helpers are in skill_prose.py.
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

SKILL = "au-aml-ctf-cdd-reliance"
REPOSITORY = Path(__file__).resolve().parents[1]
CARD = REPOSITORY / "validation" / "cases" / f"{SKILL}-referrer-checks.md"
AUSTRAC = "https://www.austrac.gov.au/industry-and-business/"
RELIANCE = (AUSTRAC + "obligations-and-guidance/your-amlctf-program/customer-due-diligence/"
            "reliance-customer-identification-third-party/")
STATUSES = r"`on the record`, `missing` or `for the AML/CTF compliance officer`"


class CustomerDueDiligenceRelianceTests(unittest.TestCase):
    def assert_sentence(self, text: str, *patterns: str) -> None:
        """One sentence of `text` affirms every pattern: each matches with no negator directly before it."""
        with self.subTest(patterns=patterns):
            self.assertTrue(
                any(all(affirms(sentence, pattern) for pattern in patterns) for sentence in sentences(text)),
                f"no sentence matches all of {patterns}",
            )

    def test_the_file_rests_on_the_commencement_dates_and_the_rules_in_force(self) -> None:
        step = workflow_step(SKILL, 1)
        self.assert_sentence(step, r"\bstop and route the service to `au-aml-ctf-designated-services`",
                             DO_NOT + r"decide whether a service is designated\b")
        self.assert_sentence(step, r"\bcompilation 63 \(C2026C00447, in force from 1 October 2026\)",
                             r"\bcompilation 1 \(F2026C00274, in force from 31 March 2026\)", r"\bon 19 November 2026\b")
        self.assert_sentence(step, r"\bSchedule 2 to that Amendment Act\b", r"\bcommenced on 31 March 2026\b",
                             r"\bitem 11 of its Schedule 3\b", r"\bPart 2\b", r"\bDivisions 2 to 6 of Part 10\b",
                             r"\buntil 1 July 2026\b", r"\btable 6 service\b")
        self.assert_sentence(step, r"\bmust not commence to provide a designated service to a customer until\b",
                             r"\beach matter in s 28\(2\)")
        # What is in draft and what the Act leaves to the Rules, as read on the day.
        self.assert_sentence(step, r"\bno later compilation of the Act or the AML/CTF Rules\b",
                             r"\blisted no open consultation\b", r"\bclosed on 20 February 2026\b")
        self.assert_sentence(step, r"\bThis skill cites no draft instrument\b")
        self.assert_sentence(step, r"\bs 28\(2\)\(g\) of the AML/CTF Act\b", r"\bs 29\(a\), \(c\)\(ii\) and \(f\)",
                             r"\bss 37A\(1\)\(b\), 37A\(2\)\(e\), 37B\(1\) and 38\(e\)", r"\bopen the Rules in force\b")

    def test_a_pre_commencement_customer_is_routed_not_decided(self) -> None:
        step = workflow_step(SKILL, 1)
        self.assert_sentence(step, r"\bs 36\(1\)\(b\) of the AML/CTF Act\b", r"\bas at the start of 1 July 2026\b")
        self.assert_sentence(step, r"\bSection 36\(3\) of the AML/CTF Act disapplies s 28\(1\)",
                             r"\bs 36\(4\) applies it again\b", r"\bsuspicious matter reporting obligation\b",
                             r"\bmedium or high\b")
        self.assert_sentence(step, r"\bWhether the client is a pre-commencement customer is for that officer\b")

    def test_each_matter_has_a_row_and_none_is_marked_established(self) -> None:
        step = workflow_step(SKILL, 2)
        for letter in "abcdefg":
            with self.subTest(matter=letter):
                self.assertRegex(step, rf"\({letter}\) ")
        self.assert_sentence(step, r"\bpolitically exposed person or a person designated for targeted financial sanctions\b")
        self.assert_sentence(step, r"\ba status: " + STATUSES)
        self.assert_sentence(step, r"\bNever mark a matter as established\b",
                             r"\bestablished on reasonable grounds is for that officer\b")

    def test_minimum_kyc_follows_the_customer_type(self) -> None:
        step = workflow_step(SKILL, 2)
        for provision, item in ((r"s 6-1", r"principal place of business"),
                                (r"s 6-2", r"director identification number"),
                                (r"s 6-2", r"ownership and control structure"),
                                (r"s 6-3", r"description of each class of beneficiary"),
                                (r"s 6-3", r"settlor, appointor, guardian or protector"),
                                (r"s 6-4", r"government body"),
                                (r"s 6-5", r"not an individual")):
            with self.subTest(provision=provision, item=item):
                self.assert_sentence(step, rf"\b{provision} of the AML/CTF Rules\b", rf"\b{item}\b")
        self.assert_sentence(step, r"\bList each item missing for the customer's type as a missing element\b")

    def test_beneficial_owners_reuse_the_owner_by_owner_test(self) -> None:
        step = workflow_step(SKILL, 2)
        self.assert_sentence(step, r"\bowner by owner with step 3 of `au-aml-ctf-client-coverage`",
                             DO_NOT + r"repeat that test here with a weaker one\b")
        self.assert_sentence(step, r"\bs 6-6\b", r"\bs 6-10\b", r"\bs 6-11\b", r"\beach of its conditions\b",
                             DO_NOT + r"decide whether it applies\b")

    def test_the_practice_identifies_the_risk_itself(self) -> None:
        step = workflow_step(SKILL, 3)
        self.assert_sentence(step, r"\bSection 28\(3\)\(b\) of the AML/CTF Act requires the practice itself to identify\b",
                             r"\bbefore the service starts\b")
        self.assert_sentence(step, r"\bwhere no rating is recorded, list it as missing\b",
                             DO_NOT + r"assign or estimate one\b")
        self.assert_sentence(step, r"\bSimplified measures are available only where the risk is low, s 32 does not apply\b",
                             r"\(s 31 of the AML/CTF Act\)")
        self.assert_sentence(step, r"\beach circumstance in s 32 of the AML/CTF Act\b", r"\bquestion for the AML/CTF "
                                   r"compliance officer on enhanced due diligence\b")
        self.assert_sentence(step, r"\bs 6-23 of the AML/CTF Rules adds the source of that person's wealth and funds\b",
                             r"\bs 5-5\(1\) of the AML/CTF Rules\b", r"\bsenior manager's approval before the service "
                                                                     r"starts\b")
        self.assert_sentence(step, r"\bWhether a person is a politically exposed person, and the rating, are for that "
                                   r"officer\b")

    def test_delayed_due_diligence_has_conditions_and_a_period(self) -> None:
        step = workflow_step(SKILL, 4)
        self.assert_sentence(step, r"\bSection 29 of the AML/CTF Act permits it only where\b",
                             r"\bessential to avoid interrupting the ordinary course of business\b",
                             r"\badditional risk is low\b", r"\bas soon as reasonably practicable\b")
        self.assert_sentence(step, r"\bs 6-12 of the AML/CTF Rules requires, before the service starts\b",
                             r"\bs 28\(2\)\(a\) and \(c\) established\b",
                             r"\bmoney, property or virtual assets\b", r"\bending 20 business days after the service "
                                                                       r"starts\b")
        # The day count needs the practice's business days; it is never worked out from memory.
        self.assert_sentence(step, r"\bthe 20 business day date only where the practice supplies the business days\b",
                             r"\botherwise record that date as `UNVERIFIED`")
        self.assert_sentence(step, r"\binconvenience\b", r"\bnot a sufficient reason\b",
                             r"\bregulator's view, not the law\b")
        self.assert_sentence(step, r"\bs 6-32 of the AML/CTF Rules\b", DO_NOT + r"apply s 6-12 to it\b")
        self.assert_sentence(step, r"\bs 7 of the \*Anti-Money Laundering and Counter-Terrorism Financing Transitional "
                                   r"Rules 2026\*", r"\bceases to have effect on 31 March 2029\b")

    def test_reliance_covers_collection_and_verification_only(self) -> None:
        step = workflow_step(SKILL, 5)
        self.assert_sentence(step, r"\bs 37A or s 38 of the AML/CTF Act treats the practice as having complied with "
                                   r"s 28\(3\)\(c\) or \(d\)", r"\bPart 10 is excluded\b")
        self.assert_sentence(step, r"\bstill identifies the client's ML/TF risk itself \(s 28\(3\)\(b\)",
                             r"\benhanced due diligence where s 32 requires it\b", r"\bkeeps its own records\b")
        self.assert_sentence(step, r"\brecord each condition as " + STATUSES)

    def test_an_agent_or_provider_is_not_reliance(self) -> None:
        step = workflow_step(SKILL, 5)
        self.assert_sentence(step, r"\bs 37 of the AML/CTF Act\b", r"\bwhich remains liable\b")
        self.assert_sentence(step, r"\bKYC or outsourced service provider is not a third party for reliance\b")
        self.assert_sentence(step, r"\bRecord a provider's report as collected KYC information under the practice's own "
                                   r"due diligence, never as reliance\b")

    def test_an_arrangement_lists_each_rule_and_its_assessments(self) -> None:
        step = workflow_step(SKILL, 5)
        arrangement = re.search(r"- Agreement or arrangement \(s 37A of the AML/CTF Act\): .*?(?= - Case by case)", step)
        self.assertIsNotNone(arrangement)
        text = arrangement.group(0) if arrangement else ""
        self.assert_sentence(text, r"\bwritten agreement or arrangement\b",
                             r"\bsenior manager approved it before the practice entered into it \(s 5-5\(1\)\(f\)")
        for condition in (r"reporting entity or a person regulated under foreign laws giving effect to the FATF "
                          r"Recommendations", r"measures to comply", r"appropriate to the practice's ML/TF risks",
                          r"obtain all the KYC information collected before the service starts or within the s 29 period",
                          r"copies of the verification data immediately or as soon as practicable on request",
                          r"documents each party's responsibilities, including record keeping"):
            with self.subTest(condition=condition):
                self.assert_sentence(text, r"\bs 6-29\(1\) of the AML/CTF Rules\b", rf"\b{condition}")
        self.assert_sentence(text, r"\bs 37A\(2\)\(d\) of the AML/CTF Act\b")
        self.assert_sentence(text, r"\bs 6-30 of the AML/CTF Rules\b", r"\bnot more than 2 years\b",
                             r"\bsignificant change in circumstances\b", r"\bwithin 10 business days after completing\b")
        self.assert_sentence(text, r"\bs 37A\(3\) of the AML/CTF Act removes the reliance for procedures carried out "
                                   r"afterwards\b", r"\blist as missing\b")
        self.assert_sentence(text, r"\bnot expect delays beyond one business day\b", r"\bregulator's view\b")

    def test_case_by_case_reliance_needs_documented_reasons(self) -> None:
        step = workflow_step(SKILL, 5)
        case = re.search(r"- Case by case \(s 38 of the AML/CTF Act\): .*?(?= - Client taken over)", step)
        self.assertIsNotNone(case)
        text = case.group(0) if case else ""
        self.assert_sentence(text, r"\bs 6-31 of the AML/CTF Rules\b", r"\bdocumented reasons\b", r"\(s 6-31\(e\)\)")
        self.assert_sentence(text, r"\bAUSTRAC enrolment of the other person shows its status only, not the other "
                                   r"conditions\b")
        self.assert_sentence(text, r"\bWhere any reason is not documented, list it as missing\b")

    def test_a_transferred_client_needs_the_prior_records(self) -> None:
        step = workflow_step(SKILL, 5)
        self.assert_sentence(step, r"\bs 6-27 of the AML/CTF Rules\b", r"\bss 107, 108, 111 and 114 of the AML/CTF Act\b")
        self.assert_sentence(step, r"\bongoing due diligence under s 30 of the AML/CTF Act still applies\b")
        self.assert_sentence(step, r"\bWhether reliance is appropriate\b", r"\bare for the AML/CTF compliance officer and "
                                                                          r"a senior manager\b")

    def test_records_are_listed_never_deleted(self) -> None:
        step = workflow_step(SKILL, 6)
        self.assert_sentence(step, r"\bSection 111\(3\) of the AML/CTF Act\b", r"\btype and content of the data\b")
        self.assert_sentence(step, r"\bs 114 of the AML/CTF Act\b", r"\bfirst 7 year period\b",
                             r"\bs 114A requires each s 37B assessment record to be kept for 7 years\b")
        self.assert_sentence(step, r"\bnever a deletion list\b")

    def test_the_skill_screens_no_one_and_tips_no_one_off(self) -> None:
        step = workflow_step(SKILL, 7)
        self.assert_sentence(step, DO_NOT + r"screen the client, verify identity documents, contact the client or the "
                                            r"other person, form a suspicion or lodge a report\b")
        self.assert_sentence(step, r"\bdisclose it to no one else\b", r"\bs 123 of the AML/CTF Act\b")

    def test_the_hand_off_names_what_the_skill_does_not_decide(self) -> None:
        hand_off = section(SKILL, "Hand-off and checks")
        self.assert_sentence(hand_off, r"`ready for the AML/CTF compliance officer`", r"`incomplete` otherwise\b",
                             r"\bit is never `complete`")
        self.assert_sentence(hand_off, r"\bThis skill does not decide whether a matter is established on reasonable "
                                       r"grounds\b", r"\brisk rating\b", r"\bwhether delayed due diligence is permitted\b",
                             r"\bwhether reliance is appropriate or available\b", r"\bwhether to start or continue the "
                                                                                 r"service\b")

    def test_the_advice_note_appears_once(self) -> None:
        self.assertEqual(skill_text(SKILL).count("It is not tax, legal or financial advice."), 1)
        self.assertNotRegex(skill_text(SKILL), r"(?i)\byou are (?:not )?(?:a )?reporting entity\b")

    def test_sources_are_pending_agent_reads(self) -> None:
        found = records(SKILL)
        for url in ("https://www.legislation.gov.au/C2006A00169/latest", "https://www.legislation.gov.au/F2025L01026/latest",
                    "https://www.legislation.gov.au/F2026L00393/latest", "https://www.legislation.gov.au/C2024A00110/asmade",
                    RELIANCE + "reliance-under-customer-due-diligence-arrangements", RELIANCE + "reliance-case-case-basis",
                    AUSTRAC + "consultations"):
            with self.subTest(url=url):
                self.assertIn(url, found)
                self.assertIn(url, skill_text(SKILL))
        for url, record in found.items():
            with self.subTest(url=url):
                self.assertEqual(record["verification_status"], PENDING)
                self.assertEqual(record["fact"], PENDING_FACT)
                self.assertEqual(record["checked_at"], "")
                self.assertRegex(str(record["review_required_since"]), ISO_DATE)
                if url.startswith(AUSTRAC):
                    self.assertIn("not law", str(record["limitations"]))
                    self.assertRegex(str(record["limitations"]), r"last updated \d{1,2} [A-Z][a-z]+ 2026")

    def test_the_card_and_routing_case_exercise_reliance(self) -> None:
        raw = CARD.read_text(encoding="utf-8")
        self.assertIn(f"  - {SKILL}\n", raw)
        card = " ".join(raw.split())
        self.assertIn("The practice has no written agreement or arrangement with the law firm.", card)
        self.assertIn("Record the route as case-by-case reliance under s 38 of the AML/CTF Act", card)
        self.assertIn("Record that the law firm's enrolment shows its status only", card)
        self.assertIn("Do not mark the file ready, a matter established or reliance available", card)
        cases = yaml.safe_load((REPOSITORY / "validation" / "routing-cases.yaml").read_text(encoding="utf-8"))
        routed = [case for case in cases if case["skill"] == SKILL]
        self.assertEqual(len(routed), 1)
        self.assertNotIn(SKILL, routed[0]["prompt"])
        self.assertIn("au-aml-ctf-client-coverage", routed[0]["not"])


if __name__ == "__main__":
    unittest.main()
