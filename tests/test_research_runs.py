# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: Apache-2.0
"""The shared research-run pattern keeps every run in one note and never sends the client draft.

The tests read the rules file and the 3 skills that adopt it and check the wording a
reader could get wrong: the 5 run sections in order; numbered questions that name the
conclusion they could change; earlier runs kept, never overwritten; a later run that
says what changed; and a client draft addressed to the practitioner, holding nothing
the latest run does not, marked not approved and never sent. The helpers are in
skill_prose.py.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from skill_prose import section, workflow_step

RULES = Path(__file__).resolve().parents[1] / ".claude" / "rules" / "research-runs.md"
RUN = ("### Summary", "### Legislation and guidance", "### Analysis", "### Risk",
       "### Draft recommendations for the reviewer")


def flat(text: str) -> str:
    return " ".join(text.split())


class ResearchRunPattern(unittest.TestCase):
    text = RULES.read_text(encoding="utf-8")

    def test_runs_questions_answers_and_draft_are_in_order(self) -> None:
        heads = ["## Original request", "## Run 1", "## Clarifying questions after run 1",
                 "## Answers received", "## Run 2", "## Client draft (for the practitioner, not sent)",
                 "## Reviewer decision"]
        at = [self.text.index(h) for h in heads]
        self.assertEqual(at, sorted(at))
        for run in ("## Run 1", "## Run 2"):
            start = self.text.index(run)
            positions = [self.text.index(h, start) for h in RUN]
            self.assertEqual(positions, sorted(positions), run)
        self.assertLess(self.text.index("### What changed since run 1"), self.text.index("### Summary", self.text.index("## Run 2")))

    def test_earlier_runs_are_kept_and_questions_name_their_conclusion(self) -> None:
        body = flat(self.text)
        self.assertIn("Never overwrite or delete an earlier run, question or answer", body)
        self.assertIn("never reuse a number", body)
        self.assertIn("A question states no position or likely answer", body)
        self.assertIn("Recheck every source the run relies on; do not carry a source forward unread", body)
        self.assertIn("marked `UNVERIFIED`", body)

    def test_client_draft_is_for_the_practitioner_and_never_sent(self) -> None:
        body = flat(self.text)
        for heading in ("### Background", "### Advice summary", "### Scope and limitations"):
            self.assertIn(heading, self.text)
        self.assertIn("Address it to the practitioner", body)
        self.assertIn("adding no fact, figure, condition or conclusion the run does not hold", body)
        self.assertIn("that the advice is not approved", body)
        self.assertIn("sent_to_client: no", self.text)
        self.assertIn("Never send, email, upload or lodge the note, the client draft", body)
        self.assertIn("`au-client-letter` turns the approved text into a letter", body)

    def test_three_skills_adopt_it(self) -> None:
        link = "](https://github.com/ryanduguid/australian-accounting-skills/blob/main/.claude/rules/research-runs.md)"
        research = flat(workflow_step("au-tax-research", 7))
        self.assertIn(link, research)
        self.assertIn("never overwrite an earlier run", research)
        self.assertIn("approved advice goes to a client only through `au-client-letter`", research)
        planning = flat(workflow_step("au-tax-planning-review", 6))
        self.assertIn(link, planning)
        self.assertIn("is never sent", planning)
        letter = flat(section("au-client-letter", "Workflow"))
        self.assertIn(link, letter)
        self.assertIn("use its text only once the practitioner records approval of it", letter)


if __name__ == "__main__":
    unittest.main()
