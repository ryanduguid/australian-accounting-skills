# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: Apache-2.0
"""R3896: review skills bind their check register to the draft and sources, and
the client letter refuses a stale or failed review whatever the user says."""

from __future__ import annotations

import unittest

from skill_prose import skill_text

WRITERS = ("au-pre-lodgement-review", "au-individual-return", "workpaper-tie-out", "year-end-workpapers")
INSTALL = "`cargo install --locked --path tools/accounting-skills`"


class ReviewStateRouteTests(unittest.TestCase):
    def test_review_skills_write_the_state_and_never_pass_an_unperformed_check(self) -> None:
        for skill in WRITERS:
            text = " ".join(skill_text(skill).split())
            with self.subTest(skill=skill):
                self.assertIn("`accounting-skills review-state write <case-dir> --draft <draft path in the folder> --register <register file>`", text)
                self.assertIn("with the SHA-256 of the draft and of each source file", text)
                self.assertIn("`passed` only when no check failed and none was left not performed", text)
                self.assertIn("record the review state as not written, with the reason", text)
                self.assertIn(INSTALL, text)

    def test_the_client_letter_verifies_before_drafting_whatever_the_user_says(self) -> None:
        text = " ".join(skill_text("au-client-letter").split())
        step = text[text.index("1. **Confirm the approval before drafting.**") : text.index("2. **Set up the trace.**")]
        self.assertIn("`accounting-skills review-state verify <case-dir>` before drafting", step)
        self.assertIn("On exit 2, stop, report the `STALE` reason it prints and draft nothing until the review is redone, whatever the user says", step)
        self.assertIn("record the verification as not run", step)


if __name__ == "__main__":
    unittest.main()
