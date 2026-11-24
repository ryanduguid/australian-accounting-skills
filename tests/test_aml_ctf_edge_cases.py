# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: Apache-2.0
"""AML/CTF edge cases added on 24 November 2026, each tied to the provision or guidance it rests on.

The tests check the wording a reader could get wrong: the firm's risk assessment and
policies come before a client's first service; a minor beneficiary is not left out; a
fixed review or screening interval is the firm's input; a sanctions match stops
the file; a suspicious matter report or a foreign politically exposed person sets
conditions, not an automatic exit; a new service alone does not end pre-commencement
status; and personnel engaged offshore are not left out. Every new source record waits
for a human. The helpers are in skill_prose.py.
"""

from __future__ import annotations

import unittest

from skill_prose import PENDING, PENDING_FACT, records, section, workflow_step

COVERAGE = "au-aml-ctf-client-coverage"
RELIANCE = "au-aml-ctf-cdd-reliance"
SERVICES = "au-aml-ctf-designated-services"
B = "https://www.austrac.gov.au/industry-and-business/obligations-and-guidance/"
RISK = B + "your-amlctf-program/develop-your-amlctf-programs/step-2-identify-and-assess-your-risks"
TFS = B + "your-amlctf-program/customer-due-diligence/persons-designated-targeted-financial-sanctions-tfs"
SMR = B + "your-amlctf-program/reporting-us/suspicious-matter-reports"
KIT = B + "program-starter-kits/accountant-program-starter-kit/accounting-program-starter-kit-getting-started"
PDD = B + "your-amlctf-program/personnel-due-diligence-and-training/personnel-due-diligence-pdd"


def flat(text: str) -> str:
    return " ".join(text.split())


class AmlCtfEdgeCases(unittest.TestCase):
    def test_policies_before_the_first_service_is_a_question_not_a_breach(self) -> None:
        step = flat(workflow_step(COVERAGE, 3))
        self.assertIn("Section 26F(8) of the AML/CTF Act says a reporting entity must not commence", step)
        self.assertIn("s 28(4)(a) of the AML/CTF Act", step)
        self.assertIn("not as a finding that a provision was contravened", step)
        self.assertIn("a senior manager approved the firm's ML/TF risk assessment", flat(section(COVERAGE, "Inputs")))

    def test_unit_holders_and_minor_beneficiaries_follow_the_provisions(self) -> None:
        step = flat(workflow_step(COVERAGE, 3))
        self.assertIn("ultimately owns, directly or indirectly, 25% or more of the person, or who controls it", step)
        self.assertIn("only where the nature of the trust means it is not possible to identify each beneficiary", step)
        self.assertIn("s 6-6(3) treats whether those persons are politically exposed", step)
        self.assertIn("Neither the Act nor the Rules as read sets an exception by a beneficiary's age", step)
        self.assertIn("with a screening date or a basis the officer has recorded that treats the matter as established", step)
        self.assertIn("route any instruction to leave one out because of age", step)

    def test_intervals_are_the_firms_input(self) -> None:
        step = flat(workflow_step(COVERAGE, 4))
        self.assertIn("are the firm's policy choices", step)
        self.assertIn("sets no interval, so take each interval from the firm's policies", step)
        self.assertIn("it sets no frequency", step)
        self.assertIn("at a frequency appropriate to the client's ML/TF risk", step)

    def test_new_pep_and_address_change_are_triggers(self) -> None:
        step = flat(workflow_step(COVERAGE, 4))
        self.assertIn("s 6-24(1) of the AML/CTF Rules", step)
        self.assertIn("s 5-5(1A) of the AML/CTF Rules", step)
        self.assertIn("a new designated service does not by itself end that status", step)
        self.assertIn("s 36(4) of the AML/CTF Act makes s 28(1) of the AML/CTF Act apply only if", step)
        self.assertIn("results in the client's ML/TF risk being medium or high", step)
        self.assertIn("The client ceases to be a pre-commencement customer when the firm complies with s 28(1) of the "
                      "AML/CTF Act, under s 36(2) of the AML/CTF Act", step)
        self.assertIn("a domestic or international organisation politically exposed person while the client's ML/TF risk is high", step)
        self.assertIn("Sections 5-5(2) and 6-24(2) of the AML/CTF Rules treat a foreign politically exposed person as "
                      "domestic where the service is provided at or through a permanent establishment in a foreign country "
                      "and the status comes from a connection to that same country", step)
        self.assertIn("once the firm has established that status on reasonable grounds, a senior manager determines, "
                      "as soon as practicable after those steps are completed", step)
        self.assertIn("decide none of them", step)

    def test_a_sanctions_match_stops_the_file(self) -> None:
        step = flat(workflow_step(RELIANCE, 7))
        self.assertIn("stop the file, give it the status `for the AML/CTF compliance officer`", step)
        self.assertIn("Section 5-3 of the AML/CTF Rules", step)
        self.assertIn("record that as the regulator's view", step)
        self.assertIn("apply step 7 of `au-aml-ctf-cdd-reliance`", flat(workflow_step(COVERAGE, 6)))

    def test_smr_and_foreign_pep_set_conditions(self) -> None:
        step = flat(workflow_step(RELIANCE, 3))
        self.assertIn("Section 32(b) of the AML/CTF Act also requires enhanced due diligence", step)
        self.assertIn("does not have to end a customer relationship", step)
        self.assertIn("set conditions for providing the service rather than a prohibition", step)
        self.assertIn("s 32(c) of the AML/CTF Act also covers any person acting on behalf of the client", step)
        self.assertIn("Record the suspicious matter reporting circumstance only where that officer has put it on this file", step)
        self.assertIn("as a question for that officer, without deciding whether s 32(e) applies", step)
        self.assertIn("s 32(e) where the service is provided, or proposed to be provided, as part of a nested services", step)
        self.assertIn("a provided or proposed service may be part of a nested services relationship", step)

    def test_offshore_personnel_are_not_left_out(self) -> None:
        step = flat(workflow_step(SERVICES, 7))
        self.assertIn("s 26F(4)(d) of the AML/CTF Act requires", step)
        self.assertIn("Section 26F(4)(e) of the AML/CTF Act requires", step)
        self.assertIn("so list personnel engaged offshore with the rest", step)
        self.assertIn("at or through a permanent establishment in Australia (s 26F(2) of the AML/CTF Act)", step)
        self.assertIn("who perform, or will perform, functions relevant to its obligations", step)
        self.assertIn("training for persons employed or otherwise engaged who perform, or will perform, those functions", step)
        self.assertIn("initial training on employment or engagement and ongoing training", step)
        self.assertIn("not a required check", step)
        self.assertIn("15 or fewer personnel", step)

    def test_new_sources_wait_for_a_human(self) -> None:
        for skill, urls in ((COVERAGE, (RISK, TFS)), (RELIANCE, (TFS, SMR)), (SERVICES, (RISK, KIT, PDD))):
            found = records(skill)
            text = flat(section(skill, "Workflow"))
            for url in urls:
                with self.subTest(skill=skill, url=url):
                    self.assertIn(f"]({url})", text)
                    record = found[url]
                    self.assertEqual(record["verification_status"], PENDING)
                    self.assertEqual(record["checked_at"], "")
                    self.assertEqual(record["fact"], PENDING_FACT)
                    self.assertEqual(record["review_required_since"], "2026-11-24")


if __name__ == "__main__":
    unittest.main()
