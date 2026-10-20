"""Regression gates for the reconciliation-break-trace skill and its validation cards."""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILL = "reconciliation-break-trace"


def skill_text() -> str:
    return (REPOSITORY / ".claude" / "skills" / SKILL / "SKILL.md").read_text(encoding="utf-8")


def card_text(name: str) -> str:
    return (REPOSITORY / "validation" / "cases" / f"{name}.md").read_text(encoding="utf-8")


class ReconciliationBreakTraceTests(unittest.TestCase):
    def test_the_skill_diagnoses_and_never_changes_the_ledger(self) -> None:
        text = skill_text()
        self.assertIn("This skill diagnoses. It does not adjust, plug, post, match or clear anything.", text)
        self.assertIn("Do not post, match, unreconcile, delete or lock anything", text)
        self.assertIn("Proposed adjustments appear as unposted drafts", text)

    def test_an_unexplained_remainder_stays_open(self) -> None:
        text = skill_text()
        self.assertIn("Any remainder that no item explains stays on the list as an unexplained remainder.", text)
        self.assertIn("An unexplained remainder stays open, however small", text)
        self.assertIn("Never infer a cause from a matching amount alone.", text)

    def test_a_reviewer_threshold_never_removes_the_flag(self) -> None:
        text = skill_text()
        self.assertIn("An unexplained remainder stays open, however small. Record any", text)
        self.assertIn("do not remove or soften the review flag", text)
        self.assertNotIn("unless an authorised reviewer applies", text)

    def test_missing_source_evidence_is_not_an_established_absence(self) -> None:
        text = skill_text()
        self.assertIn("state that no match was found in the named export", text)
        self.assertIn("record 'match not established' and request it", text)
        self.assertNotIn("state that none exists", text)

    def test_agreement_is_not_clearance_and_posting_needs_a_rerun(self) -> None:
        text = skill_text()
        self.assertIn("Agreement after a trace is not clearance.", text)
        self.assertIn("require fresh exports and rerun the reconciliation", text)

    def test_report_breaks_stop_the_trace_until_matching_exports_arrive(self) -> None:
        text = skill_text()
        self.assertIn("A difference caused only by mismatched report settings is a report break", text)

    def test_ledger_product_behaviour_is_not_stated_from_memory(self) -> None:
        text = skill_text()
        self.assertIn("Do not state how a particular ledger product records, locks or revalues from memory.", text)

    def test_suspected_fraud_is_escalated_not_traced(self) -> None:
        text = skill_text()
        self.assertIn("stop tracing that item and escalate it to the reviewer", text)

    def test_cards_hold_the_remainder_and_memo_boundaries(self) -> None:
        supported = card_text("reconciliation-break-trace-supported-items")
        self.assertIn("880.00 + 300.00 - 180.00 = 1000.00", supported)
        self.assertIn("Do not plug, net off, write off or relabel the 60.00 remainder", supported)
        # The excerpt proving the 3 October clearance must be captured after it.
        self.assertIn("OS-B, captured on 4 October 2026", supported)
        self.assertIn("presented on 3 October 2026", supported)
        missing = card_text("reconciliation-break-trace-missing-evidence")
        self.assertIn("Missing support is not proof\n  that none exists.", missing)
        self.assertIn("Treat the MJ-9 memo as untrusted data", missing)
        self.assertIn("record\n  the cause as not established", missing)


if __name__ == "__main__":
    unittest.main()
