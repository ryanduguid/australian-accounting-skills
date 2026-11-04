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

    def test_bas_payg_prefill_is_compared_but_payroll_stays_the_source(self) -> None:
        base = "https://www.ato.gov.au/businesses-and-organisations/hiring-and-paying-your-workers/single-touch-payroll/"
        step = workflow_step("bas-preparation", 2)
        self.assert_carries(step, "Human review pending", "4 November 2026", "23 October 2026", "Table 2")
        # Each pre-filled W1 and W2 amount is compared with payroll and every difference listed.
        self.assert_sentence(
            step, r"\bW1\b", r"\bW2\b",
            affirmed=(r"\bcompare each\b[^,;:]*\bpayroll-derived\b", r"\blist every difference\b"),
        )
        # Payroll stays the source: the pre-fill never replaces an amount or clears a difference.
        self.assert_sentence(
            step,
            NOT + r"replace\b[^,;:]*\bpayroll-derived\b",
            NOT + r"treat\b[^,;:]*\bclearing\b",
            affirmed=(r"\bpayroll records\W+(stay|remain)\W+the\W+source\b",),
        )
        self.assert_sentence(
            step,
            r"\bsmall and medium withholders\b",
            affirmed=(
                r"\bemployer-level correction reported through STP is included\b",
                r"\bmust still be included in the activity statement\b",
            ),
        )
        # Differences are classified by the causes the current pages support, each in its clause.
        self.assert_sentence(step, affirmed=(r"\bclassify each difference\b[^,;:]*\bcause\b",))
        self.assert_sentence(
            step,
            r"\bvoluntary to report through STP\b[^;]*" + NOT + r"reported through STP\b",
            r"\bemployer-level correction made in payroll or the ledger\b[^;]*" + NOT + r"reported through STP\b",
            r"\bclosely held payees\b[^;]*\breasonable estimate\b",
        )
        # The unreadable cause list is disclosed; until a person verifies one, any other
        # difference stays unclassified and goes to the reviewer.
        self.assert_sentence(
            step, r"\bpre-fill page\b", r"\b(could not|cannot) be read on 4 November 2026\b", r"\bno replacement\b"
        )
        self.assert_sentence(
            step,
            r"\buntil a person verifies\b",
            affirmed=(r"\bleave any other difference unclassified\b", r"\bcarry it to the reviewer\b"),
        )
        self.assert_sentence(step, r"\bagrees with payroll\b", NOT + r"show\b")
        self.assert_carries(section("bas-preparation", "Inputs"), "pre-filled W1 and W2")
        self.assert_carries(section("bas-preparation", "Checks"), "unclassified")
        self.assert_cited_and_recorded(
            "bas-preparation",
            f"{base}correcting-information-reported-through-stp",
            f"{base}stp-reporting-issues-and-errors",
            f"{base}payments-you-must-report-through-stp",
            f"{base}concessional-reporting",
        )

    def test_estate_dwelling_is_tested_under_s_118_195_with_the_draft_marked(self) -> None:
        step = workflow_step("au-deceased-estates", 4)
        self.assert_carries(
            step, "s 118-195", "s 118-200", "TD 2026/D1", "28 January 2026", "Human review pending", "4 November 2026"
        )
        # The gain or loss is disregarded only on all 3 conditions.
        self.assert_sentence(
            step, r"\bdisregards\b", r"\bonly if\b", NOT + r"(an\W+)?excluded foreign resident\b",
            r"\bs 118-195\(1\)\(c\)", r"\bcolumn 2\b", r"\bcolumn 3\b",
        )
        self.assert_sentence(
            step,
            r"\bbefore 20 September 1985\b",
            r"\bon or after that day\b[^;]*\bmain residence just before death\b",
            NOT + r"(then\W+)?used to produce assessable income\b",
        )
        self.assert_sentence(
            step,
            r"\bwithin 2 years of the death\b",
            r"\blonger period the Commissioner allows\b",
            r"\bspouse \(except a spouse living permanently separately and apart\b",
            r"\bright to occupy it under the deceased's will\b",
            r"\bbeneficiary whose disposal\b",
        )
        self.assert_sentence(
            step, r"\bs 118-195\b[^,;:]*" + NOT + r"apply\b", r"\bs 118-200\b[^,;:]*\bpartial exemption\b"
        )
        # TD 2026/D1 is a draft; each kind of right counts or not in its own sentence.
        self.assert_sentence(step, r"\bTD 2026/D1\b", r"\bdraft\b", NOT + r"(a\W+)?final\b")
        self.assert_sentence(
            step, r"\bonly if\b[^;:]*\bexpressly\b", r"\bnames\b", r"\bparagraphs 15 and 16\b",
            affirmed=(r"\bcounts\b",),
        )
        self.assert_sentence(step, r"\bdiscretion\b[^,;:]*" + NOT + r"count\b", r"\bparagraph 17\b")
        self.assert_sentence(
            step,
            r"\bnor\b[^,;:]*\bdeed of arrangement\b|\bdeed of arrangement\b[^,;:]*" + NOT + r"count\b",
            r"\bparagraph 18\b",
        )
        self.assert_sentence(step, r"\btestamentary trust deed\b[^,;:]*" + NOT + r"count\b", r"\bparagraphs 31 to 34\b")
        self.assert_sentence(
            step, r"\bfamily provision order\b", r"\bcodicil\b", r"\bparagraph 28\b",
            affirmed=(r"\bgrants counts\b",),
        )
        self.assert_sentence(
            step, r"\blimited period expires\b", r"\bs 118-195\b[^,;:]*" + NOT + r"apply\b",
            r"\bonly the s 118-200 partial exemption\b", r"\bparagraphs 24 and 25\b",
        )
        self.assert_sentence(
            step, r"\bbefore and after\b", r"\bparagraph 37\b", r"\bin November 2026\b",
            affirmed=(r"\bcheck whether it has issued\b",),
        )
        self.assert_sentence(
            step, NOT + r"conclude\b", affirmed=(r"\broute\b[^;:]*\breviewer\b",)
        )
        self.assert_carries(
            section("au-deceased-estates", "Inputs"),
            "deed of arrangement", "family provision order", "testamentary trust deed", "ownership interest ended",
        )
        self.assert_cited_and_recorded(
            "au-deceased-estates",
            "https://www.legislation.gov.au/C2004A05138/latest/text",
            "https://www.ato.gov.au/law/view/document?DocID=DXT/TD2026D1/NAT/ATO/00001",
            "https://www.ato.gov.au/about-ato/ato-advice-and-guidance/advice-under-development-program/"
            "advice-under-development-capital-gains-tax-and-trust-specific-issues",
        )

    def test_fbt_car_parking_tests_each_s_39a_condition(self) -> None:
        step = workflow_step("fbt-annual-workflow", 1)
        self.assert_carries(
            step,
            "s 39A(1)", "s 136(1)", "TR 2021/2", "[2026] FCAFC 50", "27 April 2026", "[2026] HCADisp 242",
            "Table 9", "20 May 2026", "6 March 2025", "Human review pending", "4 November 2026",
        )
        # The parking conditions, each on its own.
        self.assert_sentence(
            step,
            r"\bbusiness or associated premises\b", r"\bmore than 4 hours\b", r"\bbetween 7 am and 7 pm\b",
            r"\bwithin a 1 km radius\b", r"\bordinary course of business\b", r"\bmembers of the public\b",
            r"\ball-day parking on the first business day of the FBT year\b",
            r"\bis more than the car parking threshold\b",
        )
        self.assert_sentence(
            step,
            r"\bs 39A\(1\)\(c\)", r"\bin respect of the employment\b", r"\bprimary place of employment\b",
            r"\bin the vicinity\b", r"\btravel between the employee's residence\b",
        )
        # TR 2021/2 on distance, operators, hallmarks and fees, with the 1 April 2022 cutoff
        # bound to the changed view.
        self.assert_sentence(step, r"\bclosest car entrances\b", r"\bshortest practicable route\b", r"\bparagraph 17\b")
        self.assert_sentence(
            step, r"\bshopping centre\b", r"\bparagraph 20\b",
            affirmed=(r"\btreats a facility operated by a car parking operator\b",),
        )
        self.assert_sentence(
            step,
            r"\bwithout an operator\b", r"\b2 or more hallmarks\b", r"\bsignage\b", r"\bcontrols on entry\b",
            r"\bmore than nominal\b", r"\bparagraphs 21 and 22\b",
            affirmed=(r"\bcan still be one\b",),
        )
        self.assert_sentence(
            step,
            r"\bexpensive all-day rate\b[^,;:]*" + NOT + r"(on its own\W+)?put\b[^,;:]*\boutside the ordinary course\b",
            r"\bparagraphs 35 and 36\b",
        )
        self.assert_sentence(
            step, r"\bparagraph 81 of TR 96/26\b", r"\bparagraph 56\b",
            affirmed=(r"\bchanged view applies\b[^,;:]*\bon or after 1 April 2022\b",),
        )
        self.assert_sentence(
            step, r"\bFull Court\b", r"\bshopping centre\b", NOT + r"require\b[^,;:]*\bprofit-making purpose\b",
            r"\bin the nature of commerce\b", r"\bparagraph 8\b",
        )
        self.assert_sentence(step, r"\bHigh Court refused special leave\b", r"\b8 October 2026\b")
        self.assert_sentence(
            step, NOT + r"from memory\b", affirmed=(r"\btake the car parking threshold\b[^,;:]*\bTable 9\b",)
        )
        self.assert_sentence(
            step, r"\bdistance\b", r"\broute\b", r"\bfee evidence\b", r"\bhallmarks\b",
            affirmed=(r"\brecord each station's name\b",),
        )
        # No station is dropped for its setting, its fee mix or the absence of a profit aim.
        self.assert_sentence(
            step, NOT + r"exclude a station\b", r"\bshopping centre\b", r"\bshort-term\b",
            NOT + r"aim at profit\b",
        )
        self.assert_sentence(step, r"\bdisability\b", r"\bsmall business\b", r"\bexempt employer\b", r"\b5 valuation methods\b")
        self.assert_sentence(
            step, r"\bexemption\b", r"\bmethod\b", r"\bwithout concluding\b",
            affirmed=(r"\bare reviewer decisions\b",),
        )
        self.assertIn(
            "](https://www.judgments.fedcourt.gov.au/judgments/Judgments/fca/full/2026/2026fcafc0050)", step
        )
        self.assert_carries(
            section("fbt-annual-workflow", "Inputs"), "7 am", "first business day of the FBT year", "exempt employer"
        )
        self.assert_carries(section("fbt-annual-workflow", "Checks"), "s 39A(1)")
        self.assertFalse((SKILLS / "fbt-annual-workflow" / "sources.exempt.json").exists())
        self.assert_cited_and_recorded(
            "fbt-annual-workflow",
            "https://www.legislation.gov.au/C2004A03280/latest/text",
            "https://www.ato.gov.au/law/view/document?DocID=TXR/TR20212/NAT/ATO/00001",
            "https://www.hcourt.gov.au/cases-and-judgments/judgments/special-leave-dispositions/"
            "toowoomba-regional-council-v-commissioner-taxation",
            "https://www.ato.gov.au/tax-rates-and-codes/fringe-benefits-tax-rates-and-thresholds",
            "https://www.ato.gov.au/businesses-and-organisations/hiring-and-paying-your-workers/fringe-benefits-tax/"
            "types-of-fringe-benefits/fbt-on-cars-other-vehicles-parking-and-tolls/car-parking-and-fbt",
        )

    def test_crypto_wrapping_and_airdrops_follow_the_drafts_as_drafts(self) -> None:
        step = workflow_step("au-crypto-tax", 3)
        self.assert_carries(
            step, "wrapping and unwrapping", "TD 2026/D2", "TR 2026/D1", "19 August 2026", "'To be advised'",
            "Human review pending", "4 November 2026",
        )
        self.assert_sentence(
            step, r"\bdraft for public comment\b", r"\bpreliminary view\b", NOT + r"(a\W+)?final ruling\b",
            affirmed=(r"\bproposed to apply both before and after\b",),
        )
        self.assert_sentence(
            step, r"\bTo be advised\b", r"\bbefore relying\b", affirmed=(r"\bcheck whether a final has issued\b",)
        )
        # TD 2026/D2: its scope and exclusions, each in its own clause.
        self.assert_sentence(step, r"\bonly wrapping through a smart contract\b", r"\blocks\b", r"\bmints\b", r"\bparagraph 2\b")
        self.assert_sentence(
            step,
            NOT + r"apply\b[^,;:]*\bcustodian counterparty\b", r"\bparagraph 3\b",
            NOT + r"consider\b[^,;:]*\bordinary course of a business\b",
            NOT + r"consider\b[^,;:]*\bprofit-making purpose\b", r"\bparagraph 5\b",
        )
        self.assert_sentence(
            step,
            r"\bsending A to the wrapping contract is CGT event C2\b", r"\bparagraph 9\b",
            r"\bcapital proceeds are the market value of B\b", r"\bparagraph 11\b",
            r"\bfirst element of B's cost base is A's market value\b", r"\bparagraph 12\b",
        )
        self.assert_sentence(
            step,
            r"\bunwrapping is CGT event C2 when B is burnt\b",
            r"\bcapital proceeds are the market value of A\b",
            r"\bfirst element of the new A's cost base is B's market value\b",
            r"\bparagraphs 17 to 19\b",
        )
        self.assert_sentence(
            step, r"\bAppendix 2\b", NOT + r"form part\b", r"\bparagraph 59\b", r"\bsection 106-60\b",
            affirmed=(r"\brejects a Subdivision 124-B roll-over\b",),
        )
        self.assert_sentence(
            step, r"\bcustodial crypto bridges\b", r"\bDecember 2026\b", affirmed=(r"\bcarry\b[^,;:]*\breviewer\b",)
        )
        # TR 2026/D1: exclusions, the separate asset, when the value is income and when it is not.
        self.assert_sentence(
            step, NOT + r"apply to\b", r"\bfiat currency\b", r"\bliquidity\b", r"\bnon-arm's length\b",
            r"\brebasing\b", r"\bparagraph 9\b",
        )
        self.assert_sentence(step, r"\bparagraph 16\b", affirmed=(r"\bis a separate CGT asset\b",))
        self.assert_sentence(
            step,
            r"\bis ordinary income for a recipient carrying on a business of crypto asset trading\b",
            r"\bparagraph 13\b",
            r"\bis ordinary income when it is received for goods or services\b",
            r"\bparagraph 14\b",
        )
        self.assert_sentence(
            step, r"\botherwise\b[^,;:]*" + NOT + r"ordinary income\b", r"\bparagraph 16\b",
            r"\bnor\b[^,;:]*\bhobby\b", r"\bparagraph 21\b",
        )
        self.assert_sentence(step, r"\blater disposal is CGT event A1\b", r"\bparagraph 17\b")
        self.assert_sentence(
            step, r"\binitial allocation airdrop\b", r"\bonly to airdrops after its date of issue\b", r"\bparagraph 66\b"
        )
        self.assert_sentence(
            step, r"\bcustody\b", r"\bAUD market value\b", r"\bhobby character\b",
            affirmed=(r"\brecord the contract or issuer\b",),
        )
        self.assert_sentence(
            step, NOT + r"treat either draft as final law\b", affirmed=(r"\bcarry each such classification to the reviewer\b",)
        )
        self.assert_carries(section("au-crypto-tax", "Inputs"), "contract address", "airdrop")
        self.assert_cited_and_recorded(
            "au-crypto-tax",
            "https://www.ato.gov.au/law/view/document?DocID=DXT/TD2026D2/NAT/ATO/00001",
            "https://www.ato.gov.au/law/view/document?DocID=DTR/TR2026D1/NAT/ATO/00001",
            "https://www.ato.gov.au/about-ato/ato-advice-and-guidance/advice-under-development-program/"
            "advice-under-development-capital-gains-tax-and-trust-specific-issues",
        )

    def test_individual_return_compares_the_standard_deduction_from_2026_27(self) -> None:
        step = workflow_step("au-individual-return", 3)
        self.assert_carries(
            step,
            "Schedule 4", "s 25-130(2)(a)", "LCR 2026/D5", "26 August 2026", "Human review pending",
            "4 November 2026", "au-wfh-deductions", "au-car-expenses", "au-travel-expenses",
        )
        self.assert_sentence(
            step, affirmed=(r"\bitem 17\b[^,;:]*\bappl(y|ies)\b[^,;:]*\b2026-27 income year and later\b",)
        )
        self.assert_sentence(step, r"\b2 November 2026\b", NOT + r"available for 2025-26\b")
        self.assert_sentence(
            step,
            r"\bqualifies only if\b", r"\bAustralian resident at any time during the income year\b",
            r"\bderive assessable labour income\b", r"\bs 25-130\(1\)",
        )
        self.assert_sentence(
            step,
            r"\bs 25-130\(4\)", r"\bemployees\b", r"\bcompany directors\b", r"\boffice holders\b",
            r"\breligious practitioners\b", r"\breturn to work\b", r"\bretirement\b", r"\btermination\b",
            r"\bparental leave pay\b",
        )
        self.assert_sentence(
            step,
            r"\blesser of\b[^,;:]*\bs 25-130\(2\)\(a\)[^,;:]*\bassessable labour income\b",
            NOT + r"below zero\b", r"\bs 25-130\(2\)\(c\) to \(g\)",
            r"\bgeneral deductions\b", r"\bcar expenses\b", r"\btravel between workplaces\b", r"\brepairs\b",
            r"\bdecline in value\b", r"\bbalancing adjustments\b", r"\bCOVID-19 tests\b",
        )
        self.assert_sentence(
            step,
            r"\bs 25-130\(3\)", r"\bincome protection\b", r"\bpersonal sickness\b", r"\baccident insurance\b",
            r"\btrade, business or professional association membership\b", NOT + r"reduce it\b",
            affirmed=(r"\bclaim them separately\b",),
        )
        self.assert_sentence(
            step,
            r"\bitemised claims plus any remaining standard deduction\b",
            r"\bmaximum standard deduction with those expenses\W+" + NOT + r"claimed\b",
            affirmed=(r"\bprepare both positions\b",),
        )
        self.assert_sentence(step, r"\bLCR 2026/D5\b", r"\bdraft for public comment\b", NOT + r"(a\W+)?final ruling\b")
        self.assert_sentence(
            step, r"\bparagraph 31\b", NOT + r"just the amount above\b",
            affirmed=(r"\bmust have incurred\b", r"\bmust substantiate the full amount claimed\b"),
        )
        self.assert_sentence(step, r"\bin December 2026\b", affirmed=(r"\bcheck whether it has issued\b",))
        self.assert_sentence(
            step, r"\bresidency\b", r"\bassessable labour income\b", r"\bis unknown\b",
            affirmed=(r"\bleave the comparison `UNVERIFIED`",),
        )
        self.assert_sentence(
            step, r"\bclient and reviewer choose\b",
            NOT + r"apply the standard deduction to a 2025-26 or earlier return\b",
        )
        self.assert_carries(
            section("au-individual-return", "Inputs"), "standard deduction", "residency at any time", "assessable labour income"
        )
        self.assert_carries(section("au-individual-return", "Hand-off"), "standard deduction comparison")
        self.assert_cited_and_recorded(
            "au-individual-return",
            "https://www.legislation.gov.au/C2004A05138/latest/text",
            "https://www.legislation.gov.au/C2026A00049/asmade/text",
            "https://www.ato.gov.au/individuals-and-families/income-deductions-offsets-and-records/"
            "deductions-you-can-claim/work-related-deductions/standard-deduction-for-work-related-expenses",
            "https://www.ato.gov.au/law/view/document?DocID=COD/LCR2026D5/NAT/ATO/00001&PiT=99991231235958",
            "https://www.ato.gov.au/about-ato/ato-advice-and-guidance/advice-under-development-program/"
            "advice-under-development-2026-budget-related-issues",
        )

    def test_agent_sanctions_and_section_45_client_notices(self) -> None:
        step = workflow_step("au-tax-agent-obligations", 2)
        self.assert_carries(
            step,
            "Act No. 86 of 2026", "15 September 2026", "Subdivision 40-C", "section 40-45(3)", "section 40-50",
            "section 40-55", "section 60-140(c) to (e)", "Human review pending", "4 November 2026",
        )
        self.assert_sentence(
            step, r"\bcommenced on 1 October 2026\b",
            affirmed=(r"\bitem 70 applies it to conduct engaged in on or after that day\b",),
        )
        self.assert_sentence(
            step, r"\bas well as terminate\b", r"\bSubdivision 40-A\b", r"\bsections 40-5 to 40-15\b",
            affirmed=(r"\blets the Board suspend\b",),
        )
        # Interim suspension needs both limbs: the conduct and a significant risk.
        self.assert_sentence(
            step,
            r"\bSubdivision 40-D\b", r"\binterim basis\b", r"\bsatisfied on reasonable grounds\b",
            r"\boffence against a taxation law\b", r"\bcivil penalty provision\b",
            r"\band that there is or may be a significant risk\b", r"\bmaterial loss to clients\b",
            r"\bpublic interest\b", r"\bsection 40-45\(1\)",
        )
        self.assert_sentence(
            step,
            r"\b90 days or less\b",
            NOT + r"required to observe the natural justice hearing rule\b",
            r"\bmust\W+" + NOT + r"provide tax agent services whil(e|st) suspended\b",
            affirmed=(r"\bmay be extended\b", r"\bmust give notice within 7 days\b"),
        )
        self.assert_sentence(
            step,
            r"\binfringement notices \(Subdivision 52-A\)", r"\benforceable undertakings \(Subdivision 52-B\)",
            r"\blift a Subdivision 40-A suspension\b", r"\bnotifiable instrument\b",
            affirmed=(r"\bmust publish each suspension decision\b",),
        )
        # The section 45 changes, each in its own clause, apply to events from 1 October 2026.
        self.assert_sentence(
            step, r"\bF2026L01196 amended section 45\b", r"\bon or after 1 October 2026\b", r"\bsection 101\b"
        )
        self.assert_sentence(
            step,
            r"\binterim suspension is excluded\b[^;]*\bsection 45\(1\)\(d\)\(i\)",
            r"\benforceable undertaking\b[^;]*\badded as events\b",
            r"\bpreventing an application for registration\b[^;]*\badded as events\b",
            r"\bsection 45\(1\)\(d\)\(x\) and \(xi\)",
            r"\bcurrent suspension is added as a matter\b[^;]*\bsection 45\(1\)\(e\)\(ii\)",
        )
        self.assert_sentence(step, affirmed=(r"\bmust be given in writing\b",))
        not_advised = r"\bexisting client\W+" + NOT + r"previously advised\W+"
        self.assert_sentence(
            step,
            r"\bsection 45\(1\)\(d\) event\b", r"\bprospective client at the time of the inquiry\b",
            not_advised + r"within 30 days of the event\b", r"\bsection 45\(2\)\(b\)",
        )
        self.assert_sentence(
            step,
            r"\bsection 45\(1\)\(e\) matter\b", r"\bprospective client at the time of the inquiry\b",
            not_advised + r"as soon as reasonably practicable after the event\b", r"\bsection 45\(2\)\(d\)",
        )
        self.assert_sentence(
            step, r"\bTPB\(GS\) 54/2024\b", r"\b22 July 2026\b", r"\bpredates the amendment\b", NOT + r"describe it\b"
        )
        self.assert_sentence(
            step,
            r"\binterim suspension\b", r"\binfringement notice\b", r"\benforceable undertaking\b",
            r"\bon or after 1 October 2026\b", r"\bsection 60-140 notice\b", r"\bprospective clients were told\b",
            affirmed=(r"\brecord any suspension\b",),
        )
        self.assert_sentence(
            step, NOT + r"conclude\b", affirmed=(r"\bduty applies and was met is for the responsible practitioner\b",)
        )
        self.assert_carries(section("au-tax-agent-obligations", "Inputs"), "interim suspension", "enforceable undertaking")
        self.assert_cited_and_recorded(
            "au-tax-agent-obligations", "https://www.legislation.gov.au/C2026A00086/asmade/text"
        )

    def test_agent_code_sections_name_their_guidance_statements(self) -> None:
        step = workflow_step("au-tax-agent-obligations", 2)
        guidance = {
            49: ("upholding-and-promoting-ethical-standards-tax-profession", r"\(section 10\)"),
            50: ("false-or-misleading-statements", r"\(section 15\)"),
            51: (
                "managing-conflicts-interest-when-undertaking-activities-government-and-maintaining-"
                "confidentiality-dealings-government",
                r"\(sections 20 and 25\)",
            ),
            52: ("obligation-keep-proper-client-records-tax-agent-services-provided", r"\(section 30\)"),
            53: ("supervision-competency-and-quality-management-under-tax-agent-services-act-2009", r"\(sections 35 and 40\)"),
            54: ("keeping-your-clients-informed", r"\(section 45\)"),
        }
        # Each statement names its own section: nothing past the next link may supply it.
        for number, (_, sections) in guidance.items():
            self.assert_sentence(step, rf"\bTPB\(GS\) {number}/2024\b[^\[]*?{sections}")
        self.assert_sentence(
            step, r"\b23 December 2024\b", r"\bTPB\(I\) 44/2024 to 49/2024\b", r"\b30 April 2026\b",
            affirmed=(r"\barchived the TPB\(I\) versions\b", r"\bcite the guidance statement in force\b"),
        )
        sources = section("au-tax-agent-obligations", "Primary-source starting point")
        self.assert_carries(sources, *(f"(formerly TPB(I) {number - 5}/2024)" for number in guidance))
        self.assert_cited_and_recorded(
            "au-tax-agent-obligations",
            *(f"https://www.tpb.gov.au/tpb-gs-{number}-2024-{slug}" for number, (slug, _) in guidance.items()),
        )


if __name__ == "__main__":
    unittest.main()
