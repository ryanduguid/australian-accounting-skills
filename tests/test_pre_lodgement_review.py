"""Regression gates for the au-pre-lodgement-review skill and its validation cards."""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILL = "au-pre-lodgement-review"


def skill_text() -> str:
    return (REPOSITORY / ".claude" / "skills" / SKILL / "SKILL.md").read_text(encoding="utf-8")


def card_text(name: str) -> str:
    return (REPOSITORY / "validation" / "cases" / f"{name}.md").read_text(encoding="utf-8")


class PreLodgementReviewTests(unittest.TestCase):
    def test_every_check_carries_a_status_and_skips_never_pass(self) -> None:
        text = skill_text()
        self.assertIn("performed, not performed (with the missing input named)", text)
        self.assertIn("is reported as not performed, never as passed or as a clean result", text)

    def test_no_rating_clearance_or_review_likelihood(self) -> None:
        text = skill_text()
        self.assertIn("This list gives no risk rating, score or band", text)
        self.assertIn("never says a return is safe to lodge", text)
        self.assertIn("Do not estimate the chance of an ATO review", text)

    def test_claims_rest_on_entitlement_not_review_chance(self) -> None:
        text = skill_text()
        self.assertIn("do not raise, lower or set any claim by reference to it", text)
        self.assertIn("a claim rests on entitlement and the evidence for it", text)

    def test_a_supplied_rating_is_only_a_heuristic_indicator(self) -> None:
        text = skill_text()
        self.assertIn("record it as a heuristic indicator, not a finding", text)
        self.assertIn("carry its skipped checks into the register as not performed", text)
        self.assertIn("the lodgement decision stay with the authorised human", text)

    def test_focus_areas_come_only_from_pages_opened_at_use_time(self) -> None:
        text = skill_text()
        self.assertIn("Cite only an ato.gov.au page opened at use time", text)
        self.assertIn("Do not repeat a focus list from memory", text)
        self.assertIn("an out-of-range ratio is a question for the reviewer, not a finding", text)

    def test_cards_hold_the_rating_and_calibration_boundaries(self) -> None:
        rating = card_text("au-pre-lodgement-review-rating-not-clearance")
        self.assertIn("Carry the two skipped checks into the register as not performed", rating)
        self.assertIn("Do not describe the return as cleared", rating)
        calibration = card_text("au-pre-lodgement-review-claim-calibration")
        self.assertIn("Do not supply a claim amount, a review threshold or a likelihood", calibration)
        self.assertIn("a claim rests on entitlement and the evidence for it", calibration)


if __name__ == "__main__":
    unittest.main()
