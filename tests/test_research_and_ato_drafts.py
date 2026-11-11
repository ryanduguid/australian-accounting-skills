# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The research and ATO draft steps added on 12 November 2026 keep their limits.

The partnership agreement abstract lists questions for a solicitor and decides
nothing, the Budget measure screen records facts, status and routes without
applying or recommending a measure, the research fact request states no
position and the remission draft restates only evidenced facts and is not sent.
Each test reads one step and checks what it must carry. It checks wording, not
model behaviour. The helpers are in skill_prose.py.
"""

from __future__ import annotations

import re
import unittest

from skill_prose import (
    DO_NOT,
    ISO_DATE,
    PENDING,
    PENDING_FACT,
    affirms,
    raw_section,
    records,
    section,
    sentences,
    skill_text,
    workflow_step,
)

PARTNERSHIP = "au-partnership-tax"
RESEARCH = "au-tax-research"
PENALTIES = "au-ato-penalties-interest"
ITAA_1936 = "https://www.legislation.gov.au/C1936A00027/latest/text"
TR_94_8 = "https://www.ato.gov.au/law/view/document?DocID=TXR/TR948/NAT/ATO/00001"
PS_LA_2011_12 = "https://www.ato.gov.au/law/view/document?DocID=PSR/PS201112/NAT/ATO/00001"
PS_LA_2006_8 = "https://www.ato.gov.au/law/view/document?DocID=PSR/PS20068/NAT/ATO/00001"


def lead_paragraph(skill: str, title: str) -> str:
    """The Workflow paragraph that opens with `**<title>.**`, normalised."""
    workflow = raw_section(skill, "Workflow")
    match = re.search(rf"^\*\*{re.escape(title)}\.\*\*.*$", workflow, re.MULTILINE)
    assert match, f"{skill} has no '{title}' paragraph"
    return " ".join(match[0].split())


class ResearchAndAtoDraftTests(unittest.TestCase):
    def assert_carries(self, text: str, *terms: str) -> None:
        folded = text.casefold()
        for term in terms:
            with self.subTest(term=term):
                self.assertIn(term.casefold(), folded)

    def assert_sentence(self, text: str, *patterns: str, affirmed: tuple[str, ...] = ()) -> None:
        """One sentence of `text` matches every pattern, and each `affirmed` pattern unnegated."""
        with self.subTest(patterns=patterns, affirmed=affirmed):
            self.assertTrue(
                any(all(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)
                    and all(affirms(sentence, pattern) for pattern in affirmed)
                    for sentence in sentences(text)),
                f"no sentence matches all of {patterns} with {affirmed} affirmed",
            )

    def assert_pending(self, skill: str, *urls: str) -> None:
        """Each URL is linked from the skill and indexed as an agent read awaiting human review."""
        text = skill_text(skill)
        indexed = records(skill)
        for url in urls:
            with self.subTest(skill=skill, url=url):
                self.assertIn(f"]({url})", text)
                record = indexed[url]
                self.assertEqual(record["verification_status"], PENDING)
                self.assertEqual(record["checked_at"], "")
                self.assertEqual(record["fact"], PENDING_FACT)
                self.assertRegex(str(record["review_required_since"]), ISO_DATE)

    # au-partnership-tax: row 13

    def test_partnership_abstract_registers_every_instrument_and_each_clause(self) -> None:
        step = workflow_step(PARTNERSHIP, "1a")
        self.assert_sentence(step, r"\bdocument register\b", r"\bevery variation\b", r"\bexecution evidence\b")
        self.assert_sentence(step, r"\bas missing\b", DO_NOT + r"assume it\b")
        self.assert_sentence(step, r"\bprofit and loss sharing\b", r"\bpartner salaries\b", r"\binterest on capital\b",
                             r"\bdrawings\b", r"\bcapital\b", r"\badmission\b", r"\bretirement\b", r"\bdissolution\b",
                             r"\bvariation clauses\b", r"\bclause number\b", r"\bwithout interpreting\b")
        self.assert_sentence(step, r"\bactual allocation and drawings\b", r"\beach clause\b")

    def test_partnership_variation_without_evidence_shows_both_clauses_and_changes_nothing(self) -> None:
        step = workflow_step(PARTNERSHIP, "1a")
        # Both splits side by side, the earlier clause kept in the schedule and the variation left open.
        self.assert_sentence(step, r"\blacks execution evidence\b", r"\bpart-way through the year\b",
                             r"\bearlier and the varied clause side by side\b",
                             r"\bkeep the earlier clause in the allocation schedule\b",
                             r"\bleave the variation unresolved\b")
        self.assert_sentence(step, r"\bno written agreement\b", r"\bconduct the evidence shows\b", r"\bTR 94/8\b",
                             r"\bparagraph 4\b")

    def test_partnership_abstract_lists_questions_and_decides_and_drafts_nothing(self) -> None:
        step = workflow_step(PARTNERSHIP, "1a")
        self.assert_sentence(step, r"\bnumbered list of questions for the partners' solicitor\b",
                             r"\bonly the facts and the clause references\b")
        self.assert_sentence(step, r"\bsolicitor decides validity and construction\b",
                             DO_NOT + r"decide whether a clause or variation is valid\b",
                             DO_NOT + r"draft a variation\b")
        self.assertIn("questions for the partners' solicitor", section(PARTNERSHIP, "Hand-off and checks"))

    def test_partnership_sources_are_indexed_and_pending(self) -> None:
        step = workflow_step(PARTNERSHIP, "1a")
        self.assert_sentence(step, r"^Section 92\(1\) of the \[\*Income Tax Assessment Act 1936\*\]",
                             r"\(compilation 193\)", r"\bs 90 of the ITAA 1936\b", r"\bnot a conclusion\b")
        self.assert_carries(step, "Human review pending", "12 November 2026")
        self.assert_pending(PARTNERSHIP, ITAA_1936, TR_94_8)

    # au-tax-research: row 26 and the fact request beside row 69

    def test_budget_screen_records_source_facts_status_and_routes(self) -> None:
        screen = lead_paragraph(RESEARCH, "Budget measure screen")
        self.assert_sentence(screen, r"\bBudget Paper No\. 2 \(Budget Measures\)", r"\bthe list the user supplies\b",
                             r"\bthe paper, the measure title and its page\b")
        self.assert_sentence(screen, r"\bclient facts that would bring it into play\b",
                             r"\byes, no or unknown, with the evidence\b", r"\bstatus under step 2\b",
                             r"\bstated start date\b")
        self.assert_sentence(screen, r"\broutes only\b", r"\byes or unknown\b", r"\bskill or reviewer\b",
                             r"\bfacts to request\b")

    def test_budget_screen_applies_and_recommends_nothing(self) -> None:
        screen = lead_paragraph(RESEARCH, "Budget measure screen")
        self.assert_sentence(screen, DO_NOT + r"apply a measure before it commences\b",
                             r"\brecommend any action\b", r"\bgives no advice\b")

    def test_research_fact_request_is_a_draft_with_no_position(self) -> None:
        step = workflow_step(RESEARCH, 1)
        self.assert_sentence(step, r"`facts_not_established`", r"\bdraft request for the reviewer\b",
                             r"\bevidence that would establish it\b")
        self.assert_sentence(step, r"\bState no position, conclusion or likely answer\b")
        self.assert_sentence(step, DO_NOT + r"send it\b", r"\breviewer decides whether and how the client is asked\b")

    # au-ato-penalties-interest: row 38

    def test_remission_draft_holds_the_schedules_amount_and_evidenced_facts(self) -> None:
        step = workflow_step(PENALTIES, 7)
        self.assert_sentence(step, r"\btaxpayer reference as a placeholder\b",
                             r"\beach liability and period from the step 1 to 5 schedules\b",
                             r"\bamount asked to be remitted, as the reviewer sets it\b",
                             r"\beach fact from the evidence pack with its evidence reference\b")
        self.assert_sentence(step, r"^Restate only facts the evidence pack holds\.$")

    def test_remission_draft_excludes_unevidenced_facts_and_is_not_sent(self) -> None:
        step = workflow_step(PENALTIES, 7)
        self.assert_sentence(step, r"\bfact without evidence stays out of the draft\b", r"\bexception list\b",
                             affirmed=(r"stays out of the draft",))
        self.assert_sentence(step, r"\bunsigned\b", r"\bregistered agent to review and send\b")
        # The existing prohibition stays as it was.
        self.assert_sentence(step, r"\bPrepare a draft request\b", DO_NOT + r"send it\b")
        self.assertIn("exception list", section(PENALTIES, "Hand-off and checks"))

    def test_remission_practice_statements_are_indexed_and_pending(self) -> None:
        step = workflow_step(PENALTIES, 7)
        self.assert_sentence(step, r"\bPS LA 2011/12\b", r"\bparagraph 8\b", r"\bonus\b")
        self.assert_sentence(step, r"\bbeing reviewed\b", r"\brecord its status on the date read\b")
        self.assert_pending(PENALTIES, PS_LA_2011_12, PS_LA_2006_8)


if __name__ == "__main__":
    unittest.main()
