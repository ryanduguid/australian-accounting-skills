# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""The client acceptance skill keeps proof of identity apart from AML/CTF."""

import unittest
from pathlib import Path

SKILL = (
    Path(__file__).resolve().parents[1] / ".claude" / "skills" / "au-client-acceptance" / "SKILL.md"
)


class ProofOfIdentityStep(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SKILL.read_text(encoding="utf-8")
        start = self.text.index("4. For tax agent or BAS agent services, record the proof of identity")
        self.step = self.text[start : self.text.index("5. Where the practice's assessment", start)]

    def test_step_comes_before_aml_routing_and_is_independent_of_it(self) -> None:
        self.assertIn("separately from AML/CTF", self.step)
        self.assertIn("whether or not a service is designated", self.step)
        self.assertIn("an AML/CTF status alone does not show them", self.step)

    def test_step_cites_the_guidance_not_a_legislated_requirement(self) -> None:
        self.assertIn("TPB(GS) 42/2022", self.step)
        self.assertIn("the TASA has no specific proof of identity requirement", self.step)

    def test_representatives_and_their_authority_are_covered(self) -> None:
        self.assertIn("each individual representative", self.step)
        self.assertIn("evidence of a representative's authority", self.step)
        self.assertIn("still leaves the representative's authority to be sighted", self.step)

    def test_risk_based_routes_stay_available_and_are_not_decided_here(self) -> None:
        for route in ("well-established assessment", "without conventional documents", "UNVERIFIED"):
            self.assertIn(route, self.step)
        self.assertIn("is for the authorised practitioner", self.step)

    def test_employer_route_needs_written_confirmation_and_escalation(self) -> None:
        self.assertIn("employer client instructing the practice for its employees", self.step)
        self.assertIn("written confirmation", self.step)
        self.assertIn("at least equal to this guidance", self.step)
        self.assertIn("escalated before any lodgement", self.step)

    def test_records_expected_follow_the_route(self) -> None:
        self.assertIn("where documents were sighted", self.step)
        self.assertIn("no newly sighted documents are needed", self.step)

    def test_transferred_records_flag_code_item_6(self) -> None:
        self.assertIn("client consent or a legal duty", self.step)
        self.assertIn("Code item 6", self.step)

    def test_no_document_collection_or_retention(self) -> None:
        self.assertIn("Do not sight, collect or assess identity documents here", self.step)
        self.assertIn("neither requires nor recommends keeping the documents", self.step)

    def test_the_pack_and_sources_carry_the_status(self) -> None:
        self.assertIn("the proof of identity status, the AML/CTF routing status", self.text)
        self.assertIn("tpb-gs-42-2022-proof-identity-requirements-client-verification", self.text)


if __name__ == "__main__":
    unittest.main()
