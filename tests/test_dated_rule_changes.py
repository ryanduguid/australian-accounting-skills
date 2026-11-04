# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""Skills that meet a 2026 rule change keep its start date, its scope and its source.

Each test reads one numbered workflow step and checks the dates, authorities,
exceptions and escalations it must carry, not its wording. A prohibition,
exception, negative predicate or date scope is checked within one sentence with
its negator before its verb or its side of the date. An affirmative instruction
is matched from its verb, predicate or subject and fails only when a negator
sits directly before that, so 'do not use X but apply Y' still applies Y. Each
term of a list the step must carry in full is required on its own.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[1] / ".claude" / "skills"
PENDING = "source-discovery-only-human-review-pending"
PENDING_FACT = "Primary-source discovery only; no human-reviewed current-law fact is recorded."
ISO_DATE = r"^\d{4}-\d{2}-\d{2}$"
# A negator directly before the matched verb, allowing only auxiliaries, 'to', articles
# and a set-off 'however' between ('do not apply', 'not to escalate', 'not be apportioned',
# 'does not, however, apply'). 'No. 86' is a number and 'no longer' a change.
NEGATED = r"(?:\b(?:not|never|cannot|no(?!\.))|n't)(?:\W+(?:be|been|to|a|an|the|however|also))*\W+$"
# A required negative predicate keeps its negator before its verb.
NOT = r"(?:\bnot|\bnever|n't)\W+"


def skill_text(skill: str) -> str:
    return (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")


def raw_section(skill: str, heading: str) -> str:
    """The Markdown under the first `## <heading>...` until the next `## ` heading."""
    text = skill_text(skill)
    start = re.search(rf"^## {re.escape(heading)}.*$", text, re.MULTILINE)
    assert start, f"{skill} has no '## {heading}' section"
    end = re.compile(r"^## ", re.MULTILINE).search(text, start.end())
    return text[start.end() : end.start() if end else len(text)]


def section(skill: str, heading: str) -> str:
    return " ".join(raw_section(skill, heading).split())


def workflow_step(skill: str, number: int) -> str:
    """Workflow step `number` with its indented continuation paragraphs, up to the next step."""
    workflow = raw_section(skill, "Workflow")
    start = re.search(rf"^{number}\. ", workflow, re.MULTILINE)
    assert start, f"{skill} has no workflow step {number}"
    end = re.compile(r"^\d+[a-z]?\. ", re.MULTILINE).search(workflow, start.end())
    return " ".join(workflow[start.start() : end.start() if end else len(workflow)].split())


def sentences(text: str) -> list[str]:
    """Sentences of normalised text; 'No. 86' and section numbers do not end one."""
    return re.split(r"(?<=\.)\s+(?=[A-Z*\[(])", text)


def affirms(sentence: str, pattern: str) -> bool:
    """`pattern` matches somewhere in `sentence` with no negator directly before it."""
    return any(
        not re.search(NEGATED, sentence[: match.start()], re.IGNORECASE)
        for match in re.finditer(rf"(?=(?:{pattern}))", sentence, re.IGNORECASE)
    )


def records(skill: str) -> dict[str, dict[str, object]]:
    payload = json.loads((SKILLS / skill / "sources.json").read_text(encoding="utf-8"))
    return {str(source["url"]): source for source in payload["sources"]}


class DatedRuleChangeTests(unittest.TestCase):
    def assert_carries(self, text: str, *terms: str) -> None:
        folded = text.casefold()
        for term in terms:
            with self.subTest(term=term):
                self.assertIn(term.casefold(), folded)

    def assert_sentence(self, text: str, *patterns: str, affirmed: tuple[str, ...] = ()) -> None:
        """One sentence of `text` matches every pattern, case-insensitively, and each
        `affirmed` pattern with no negator directly before it."""
        with self.subTest(patterns=patterns, affirmed=affirmed):
            self.assertTrue(
                any(all(re.search(pattern, sentence, re.IGNORECASE) for pattern in patterns)
                    and all(affirms(sentence, pattern) for pattern in affirmed)
                    for sentence in sentences(text)),
                f"no sentence matches all of {patterns} with {affirmed} affirmed",
            )

    def assert_cited_and_recorded(self, skill: str, *urls: str) -> None:
        text = skill_text(skill)
        indexed = records(skill)
        for url in urls:
            with self.subTest(skill=skill, url=url):
                self.assertIn(f"]({url})", text)
                record = indexed[url]
                # Either explicitly pending or human-dated, so a person can accept the
                # record; test_coverage_matrix checks an accepted record's digest binding.
                if record.get("verification_status") == PENDING:
                    self.assertEqual(record["checked_at"], "")
                    self.assertRegex(str(record["review_required_since"]), ISO_DATE)
                    self.assertEqual(record["fact"], PENDING_FACT)
                else:
                    self.assertRegex(str(record["checked_at"]), ISO_DATE)

    def test_smsf_lrba_real_property_must_be_business_real_property(self) -> None:
        step = workflow_step("au-smsf-year-end", 4)
        self.assert_carries(step, "10 August 2026", "Schedule 5", "s 67A(2)(c)", "s 66")
        # The rule reaches arrangements entered into from 10 August 2026,
        self.assert_sentence(
            step,
            affirmed=(r"\b(appl(y|ies)|reach(es)?|cover(s)?)\b[^,;:]*\bentered into (on or after|from) (that day|10 August 2026)\b",),
        )
        # but not maintaining or refinancing an earlier borrowing, or an asset acquired
        # under an earlier arrangement and settling later.
        excluded = r"\b(not|except|exclud\w*|other than)\b.*"
        self.assert_sentence(
            step, excluded + r"\bmaintain", excluded + r"\brefinanc", r"\bbefore (that day|10 August 2026)\b"
        )
        # Each exclusion carries its own cutoff: the acquisition's 'before' is in its clause.
        self.assert_sentence(
            step, excluded + r"\bacquired under\b", r"\bacquired under\b[^,;:]*\bbefore (that day|10 August 2026)\b", r"\bsettle"
        )
        # The evidence test applies where no exclusion does.
        self.assert_sentence(
            step, r"\bbusiness real property\b", r"\b(neither|no|none of the)\W+(exclusions?|exceptions?)\W+appl(y|ies)\b"
        )
        self.assert_sentence(
            step,
            affirmed=(r"\b(must|has to|needs? to)\W+(remain|be|stay)\W+business real property\b[^,;:]*\blife of the LRBA\b",),
        )
        # Real property that is not business real property is escalated to the trustee and
        # auditor as a possible contravention, which the agent does not decide.
        self.assert_sentence(
            step, r"\bs 67\(1\)", NOT + r"business real property\b", r"\b(do not|never|not to)\W+conclud",
            affirmed=(r"\bescalate\w*\b[^;:]*\btrustee\b", r"\bescalate\w*\b[^;:]*\bauditor\b"),
        )
        self.assert_carries(section("au-smsf-year-end", "Inputs"), "LRBA")
        self.assert_cited_and_recorded(
            "au-smsf-year-end",
            "https://www.legislation.gov.au/C2026A00049/asmade/text",
            "https://www.legislation.gov.au/C2004A04633/latest/text",
            "https://www.ato.gov.au/individuals-and-families/super-for-individuals-and-families/"
            "self-managed-super-funds-smsf/smsf-investing/restrictions-on-smsf-investments/"
            "smsf-borrowing-restrictions/limited-recourse-borrowing-arrangements/"
            "changes-to-limited-recourse-borrowing-arrangements",
        )

    def test_rental_holiday_home_costs_are_denied_before_apportionment(self) -> None:
        step = workflow_step("au-rental-property", 4)
        self.assert_carries(step, "s 26-50(3)(b)(ii)", "TR 2026/1", "Appendix 2", "PCG 2026/3")
        # Where family or friends use the home for no rent, s 26-50 denies ownership and use
        # costs unless it was mainly for rent at all times, and a denied cost is not apportioned.
        self.assert_sentence(
            step, r"\bs 26-50\b", r"\b(for no|without|free of)\W+rent\b|\brent[- ]free\b",
            r"\b(unless|except)\b.*\bat all times\b.*\bmainly\b",
            affirmed=(r"\bden(y|ies)\b[^,;:]*\bownership\b",),
        )
        self.assert_sentence(step, r"\b(not|never|rather than)\W+(\w+\W+){0,2}apportion")
        # Costs that do not relate to ownership or use, such as advertising, stay under
        # s 8-1; a change of use is tested under s 26-50(4), and a seasonal pattern is not one.
        self.assert_sentence(
            step,
            r"\badvertising\b",
            NOT + r"relate\w*\b[^,;:]*\bownership\b|\bunrelated to\b[^,;:]*\bownership\b",
            affirmed=(r"\b(stay|remain|are|is)\w*\W+(deductible\W+)?under s 8-1\b",),
        )
        self.assert_sentence(
            step, r"\bseasonal\b[^,;:]*" + NOT + r"(a\W+|such\W+)*change\b",
            affirmed=(r"\btest\w*\b[^,;:]*\bs 26-50\(4\)",),
        )
        # Appendix 2 spends no compliance resources on earlier expenses, except for
        # avoidance, fraud or evasion; an amended assessment or private ruling still
        # follows the ruling; and both documents cover individuals not in business.
        unless = r"\b(unless|except|other than)\b.*"
        self.assert_sentence(
            step,
            r"\bbefore 1 July 2026\b",
            NOT + r"devote\w*\b[^,;:]*\bcompliance resources\b|\bno compliance resources\b",
            unless + r"\bavoidance\b", unless + r"\bfraud\b", unless + r"\bevasion\b",
        )
        self.assert_sentence(
            step,
            r"\b(not|no)\W+(an\W+)?exemption\b",
            affirmed=(r"\bamended assessment\b[^,;:]*\bfollows?\b", r"\bprivate ruling\b", r"\bfollows?\b[^,;:]*\bruling\b"),
        )
        self.assert_sentence(step, r"\bindividuals\b", NOT + r"in business\b")
        # Denied amounts are kept for the cost base.
        self.assert_sentence(step, r"\bcost base\b", affirmed=(r"\bkeep\w*\b[^,;:]*\bdenied amounts\b",))
        self.assert_cited_and_recorded(
            "au-rental-property",
            "https://www.ato.gov.au/law/view/document?DocID=TXR/TR20261/NAT/ATO/00001",
            "https://www.ato.gov.au/law/view/document?DocID=COG/PCG20263/NAT/ATO/00001",
            "https://www.legislation.gov.au/C2004A05138/latest/text",
        )

    def test_agent_consent_record_covers_ai_tools(self) -> None:
        step = workflow_step("au-tax-agent-obligations", 3)
        self.assert_carries(
            step,
            "Code item 6", "TPB(GS) 55/2026", "22 July 2026", "paragraph 23",
            "https://github.com/ryanduguid/llm-tax-guardrails/blob/main/src/data/gs55-concordance.yaml",
        )
        # The consent record extends to each AI tool, and each client's permission comes
        # before its information goes into one.
        self.assert_sentence(step, r"\brecord\b", affirmed=(r"\b(extend|cover)\w*\b[^,;:]*\bAI tools?\b",))
        self.assert_sentence(
            step,
            r"\bAI tool\b",
            affirmed=(
                r"\bpermission\W+(is\W+)?(needed|required)\W+(first|before)\b"
                r"|\b(obtain|get|hold|have)\b.*\bpermission\b.*\b(first|before)\b",
            ),
        )
        # The record includes the practice's due diligence, and whether a use is a
        # disclosure is for the responsible practitioner.
        self.assert_sentence(
            step, r"\bparagraph 25\b", affirmed=(r"\b(the|its|their)\W+(\w+'s\W+)?due diligence\b",)
        )
        self.assert_sentence(
            step,
            r"\bdisclosure\b",
            affirmed=(r"\b(for|to|with)\W+the\W+responsible practitioner\b|\bresponsible practitioner\W+(decides|determines)\b",),
        )
        self.assert_carries(section("au-tax-agent-obligations", "Inputs"), "AI tools")
        self.assert_cited_and_recorded(
            "au-tax-agent-obligations",
            "https://www.tpb.gov.au/tpbgs-552026-use-artificial-intelligence-and-code-professional-conduct",
        )

    def test_trust_beneficiary_tfns_move_to_the_statement_of_distribution(self) -> None:
        step = workflow_step("au-trust-distributions", 3)
        self.assert_carries(step, "closely held trust")
        # Record whether and when each beneficiary quoted a TFN and whether TFN
        # withholding applied, never the TFN itself.
        self.assert_sentence(
            step,
            r"\b(not|never)\W+(\w+\W+){0,3}TFN itself\b", r"\bquot\w*\b[^,;:]*\b(when|date)\b", r"\bwithh(olding|eld)\b",
            affirmed=(r"\brecord\b[^,;:]*\bquot",),
        )
        # The quarterly report ceased from 1 July 2026, the last falling due on 31 July 2026;
        # the return carries TFNs from the 2027 lodgment; withholding where no TFN was quoted stays.
        self.assert_sentence(step, r"\b(from|on|after) 1 July 2026\b", affirmed=(r"\b(ceased|ended|stopped|no longer)\b",))
        self.assert_sentence(step, r"\b(last|final)\b", r"\b30 June 2026\b", r"\b31 July 2026\b")
        self.assert_sentence(
            step,
            r"\b(starting|from|beginning)\b.*\b2027\b",
            affirmed=(r"\b(report\w*|go|goes|appear\w*)\b[^,;:]*\bstatement of distribution\b",),
        )
        self.assert_sentence(step, r"\bTFN withholding\b.*\b(unchanged|still applies|continues)\b", NOT + r"quoted\b")
        self.assert_carries(section("au-trust-distributions", "Inputs"), "TFN")
        self.assert_cited_and_recorded(
            "au-trust-distributions",
            "https://www.ato.gov.au/businesses-and-organisations/trusts/trusts-registration-and-reporting-obligations/"
            "closely-held-trusts/tfn-withholding-for-closely-held-trusts/what-trustees-need-to-do",
            "https://www.ato.gov.au/businesses-and-organisations/business-bulletins-newsroom/"
            "changes-to-beneficiary-tfn-reporting-for-closely-held-trusts",
        )

    def test_nonresident_cgt_events_from_1_october_2026_use_the_amended_tests(self) -> None:
        step = workflow_step("au-nonresident-cgt", 2)
        self.assert_carries(step, "Act No. 86 of 2026", "item 39(2)", "s 855-25(1)(b)")
        # The amended Division 855 applies to CGT events from 1 October 2026 and an
        # earlier event keeps the law as it stood.
        self.assert_sentence(
            step,
            r"\bCGT events?\W+(occurring\W+)?(on or after|from) 1 October 2026\b",
            affirmed=(r"\bappl(y|ies)\b[^,;:]*\bDivision 855\b[^,;:]*\bas amended\b",),
        )
        self.assert_sentence(
            step,
            r"\b(earlier|prior)\b.*\bCGT event\b|\bCGT event\b.*\b(before|prior to) 1 October 2026\b",
            affirmed=(
                r"\b(appl(y|ies)|use|uses|take|takes)\b[^,;:]*(\bas it stood\b|\bunamended\b"
                r"|\bbefore (the |its )?(amendments?|changes?)\b|\b(earlier|former|previous|old) (law|version|rules)\b)",
            ),
        )
        # The new real property definition; water entitlements and options; the principal
        # asset test at the event or at any time in the 365 days before it, unless a
        # determination sets another time; and the record of what was applied.
        self.assert_sentence(step, affirmed=(r"\b(takes?|uses?|appl(y|ies))\b[^,;:]*\bs 995-1\(1\)",))
        self.assert_sentence(
            step,
            r"\bs 855-20\b",
            affirmed=(r"\b(covers?|includes?)\b[^,;:]*\bwater entitlements?\b", r"\b(covers?|includes?)\b[^,;:]*\boptions?\b"),
        )
        self.assert_sentence(
            step,
            r"\b(unless|except)\b.*s 855-25\(1A\)",
            r"\btime of the (CGT )?event\b",
            r"\b(any|some) time (in|during|within) the 365 days (before|preceding|prior)\b",
        )
        self.assert_sentence(
            step,
            r"\bversion of Division 855\b", r"\bmarket[- ]value evidence\b",
            affirmed=(r"\brecord\b[^,;:]*\bevent date\b",),
        )
        self.assert_cited_and_recorded(
            "au-nonresident-cgt",
            "https://www.legislation.gov.au/C2026A00086/asmade/text",
            "https://www.legislation.gov.au/C2004A05138/latest/text",
        )

    def test_stp_finalisation_asks_about_changed_reporting_identifiers(self) -> None:
        """The step dates the agent read inline, and both pages are indexed so preflight sees them."""
        base = "https://www.ato.gov.au/businesses-and-organisations/hiring-and-paying-your-workers/single-touch-payroll/"
        step = workflow_step("stp-finalisation", 2)
        self.assert_carries(step, "income statement", "Human review pending")
        # Ask whether each identifier changed and record the date of each change.
        self.assert_sentence(
            step, r"\bABN\b", r"\bbranch\b", r"\bBMS ID\b", r"\bPayroll ID\b",
            affirmed=(r"\b(ask|confirm|establish|find out)\b", r"\brecord\b[^,;:]*\bdate\b"),
        )
        # Moved YTD amounts need the replacement method or zeroing out, or duplicates follow.
        must = r"\b(must|needs? to|has to|is required to)\W+(tell|notify|report to|use)\b[^,;:]*"
        self.assert_sentence(
            step, r"\bduplicate", affirmed=(must + r"\breplacement method\b", must + r"\bzeroing out\b")
        )
        # A changed ABN or branch is finalised under the old one and restarts from zero;
        # where YTD amounts were not transferred, each combination is finalised separately,
        # impossible once cancelled.
        self.assert_sentence(
            step,
            r"\bABN\b",
            affirmed=(r"\bfinalis\w*\b[^,;:]*\b(original|old|previous|former)\b", r"\b(starts?|restarts?|begins?)\b[^,;:]*\bzero\b"),
        )
        self.assert_sentence(
            step,
            NOT + r"transferred\b",
            r"\b(cannot|can ?not|can't|unable|not possible)\b.*\bcancelled\b",
            affirmed=(r"\bfinalis\w*\b[^,;:]*\bseparately\b",),
        )
        # The agent lists exceptions; the authorised person corrects them.
        self.assert_sentence(
            step,
            r"\bcorrect",
            affirmed=(
                r"\b(an?|the)\W+(action|matter|task|step)\W+for\W+the\W+authorised person\b"
                r"|\bauthorised person\W+(makes|corrects|does)\b",
            ),
        )
        self.assert_carries(section("stp-finalisation", "Inputs"), "Payroll ID")
        self.assert_cited_and_recorded(
            "stp-finalisation",
            f"{base}changing-your-payroll-solution-or-employees-payroll-ids",
            f"{base}correcting-information-reported-through-stp",
        )


if __name__ == "__main__":
    unittest.main()
