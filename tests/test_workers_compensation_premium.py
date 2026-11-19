# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The workers compensation premium skill: scheme by scheme, the insurer decides, no rate held."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILL = REPOSITORY / ".claude" / "skills" / "workers-compensation-premium"


def text() -> str:
    return " ".join((SKILL / "SKILL.md").read_text(encoding="utf-8").split())


def step(number: int) -> str:
    body = text()
    start = body.index(f"{number}. **")
    end = body.find(f"{number + 1}. **", start)
    return body[start : end if end != -1 else body.index("## Hand-off and checks")]


class WorkersCompensationPremiumTests(unittest.TestCase):
    def test_every_link_has_a_pending_source_record(self) -> None:
        links = set(re.findall(r"\]\((https://[^)]+)\)", text()))
        records = json.loads((SKILL / "sources.json").read_text(encoding="utf-8"))["sources"]
        self.assertEqual(links, {record["url"] for record in records})
        for record in records:
            with self.subTest(url=record["url"]):
                self.assertEqual(
                    record["verification_status"], "source-discovery-only-human-review-pending"
                )
                self.assertEqual(record["checked_at"], "")

    def test_each_scheme_keeps_its_own_wages_definition(self) -> None:
        mapping = step(3)
        self.assertIn("Never carry one scheme's treatment to another", mapping)
        self.assertIn(
            "never use payroll tax wages in place of these: route payroll tax to `au-payroll-tax-states`",
            mapping,
        )
        # The differences read on 19 November 2026 that a single payroll treatment would get wrong.
        self.assertIn(
            "icare includes employer superannuation contributions, fringe benefits at their grossed-up value "
            "and lump sum termination payments for leave, and leaves out the GST in a payment",
            mapping,
        )
        self.assertIn(
            "leaves out work-related expense reimbursements and lump sum termination payments",
            mapping,
        )
        self.assertIn(
            "applies from 4 pm on 30 June 2025 under the *Workers Compensation and Injury Management Regulations 2024* (WA)",
            mapping,
        )

    def test_the_insurer_decides_and_the_skill_states_no_rate(self) -> None:
        body = text()
        self.assertIn(
            "this skill states no rate, chooses no classification and decides no one's worker status",
            body,
        )
        notice = step(5)
        self.assertIn("never choose a classification", notice)
        self.assertIn("do not recompute the insurer's claims component", notice)
        self.assertIn("do not copy the table into the workpaper", notice)
        self.assertIn("Worker status is the reviewer's decision", step(2))
        self.assertIn(
            "Take the declaration due date and the consequence of not declaring from the notice or the "
            "scheme's page at use time; never supply them from memory",
            step(6),
        )
        self.assertIn(
            "Comcare employers, which are all experience rated, self-insurers and Seacare employers are "
            "outside this skill",
            step(1),
        )

    def test_gst_and_levies_stay_separate_and_route_to_the_bas(self) -> None:
        lines = step(7)
        self.assertIn("ReturnToWorkSA's work health and safety fee does not", lines)
        self.assertIn("s 11-15 of the GST Act", lines)
        self.assertIn("`bas-preparation`", lines)


if __name__ == "__main__":
    unittest.main()
