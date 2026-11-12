# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""Skills that meet a 2026 rule change keep its start date, its scope and its source.

Each test reads one numbered workflow step, or one table row cell by cell, and
checks the dates, authorities, exceptions and escalations it must carry, not its
wording. A prohibition,
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

from skill_prose import (
    DO_NOT,
    ISO_DATE,
    NOT,
    PENDING,
    PENDING_FACT,
    SKILLS,
    affirms,
    raw_section,
    records,
    section,
    sentences,
    skill_text,
    table_row,
    workflow_step,
)

# Links from a skill to the author's other repositories, and what each names.
AUTHOR_LINK = re.compile(r"github\.com/ryanduguid/(?!australian-accounting-skills\b)[\w.-]+(?:/[^\s)\"'`>]*)?")
LINKED_PROGRAMS = {
    "/packages/review-ready-gate": "review-ready",
    "/packages/monthly-close-control-plane": "close-control",
    "/packages/xero-trial-balance-export": "xero-trial-balance-export",
    "/tools/xero_aged_receivables.py": "xero_aged_receivables.py",
    "/packages/the-wip-tally": "wip-tally",
    "/packages/the-exchequer-tally": "the-exchequer-tally",
    "/packages/solomons-sword": "solomons-sword",
    "/packages/payday-super-checker": "payday-super-check",
    "ryanduguid/PaulGoodman": "fadden",
}
NOT_PROGRAM_LINKS = (
    r"/powerquery/",  # an adapter the skill describes; it does not tell the agent to run it
    r"/samples/",  # fabricated sample data
    r"ryanduguid/DrDebits/",  # a data file
    r"ryanduguid/xero-mcp-server/",  # the ledger connector, which has its own Privacy bullet
    r"ryanduguid/australian-accounting$",  # the repository in wip-tally's cargo install command
)
# Named without a link to its source.
UNLINKED_PROGRAMS = ("aasb-corpus",)

# 'Dutiable' and its faithful rewordings.
DUTIABLE = r"(?:dutiable|subject to duty|liable to duty)\b"


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
            "https://github.com/ryanduguid/DrDebits/blob/main/src/data/gs55-concordance.yaml",
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

    def test_trust_resolution_content_schedule_carries_content_never_wording(self) -> None:
        step = workflow_step("au-trust-distributions", "1a")
        self.assert_sentence(step, r"\btrustee and their lawyer\b", r"\bdeed abstract\b",
                             r"\bresolution-readiness checklist\b", r"\bproposed distribution plan\b",
                             affirmed=(r"\bprepare a schedule\b",))
        # Each entry is required on its own.
        self.assert_sentence(
            step, r"\bfor each beneficiary\b", r"\bmeasure of income the deed uses\b", r"\bamount or share\b",
            r"\bstreamed class\b", r"\bclause relied on\b", r"\bdeadline as the deed abstract records it\b",
            r"\bnot ready\b", r"\bquestion for the lawyer\b",
        )
        self.assert_sentence(step, r"\btrust-law income\b", r"\bstep 2\b", NOT + r"spread\b",
                             affirmed=(r"\blist (any|the) difference\b",))
        self.assert_sentence(step, r"\bblank\b", r"`UNVERIFIED`", NOT + r"fill it from\b")
        self.assert_sentence(step, r"\bschedule of content\b", NOT + r"resolution wording\b",
                             DO_NOT + r"draft, date or sign a resolution\b")
        self.assert_sentence(step, r"\bthe trustee and their lawyer settle the wording\b", r"\btrustee decides\b")
        # The schedule carries the proposal as given and derives nothing from it.
        self.assert_sentence(step, r"\bproposal as given\b", NOT + r"(convert|compute)\b",
                             r"\bnothing the proposal does not state\b")
        self.assert_sentence(step, r"\bshares apply before or after the streamed amounts\b",
                             r"\bquestion for the trustee and their lawyer\b")
        # Step 2's schedule exists before the comparison.
        self.assert_sentence(step, r"\btrust-law income\b", r"\bprepared before this schedule\b")
        self.assert_carries(section("au-trust-distributions", "Inputs"), "proposed distribution plan")
        self.assert_sentence(section("au-trust-distributions", "Hand-off"), r"\bresolution content schedule\b",
                             NOT + r"resolution wording\b")

    def test_trust_family_trust_screen_reads_the_fte_and_iee_report(self) -> None:
        step = workflow_step("au-trust-distributions", "4a")
        self.assert_carries(step, "Online services for agents", "Human review pending", "12 November 2026", "19 October 2026")
        # The report is checked for the trust and for each entity interposed into its family group.
        self.assert_sentence(
            step, r"\bFTE\b", r"\bIEE\b", r"\bfor the trust\b", r"\beach entity with an IEE\b",
            affirmed=(r"\bcheck\b[^,;:]*\breport\b[^,;:]*\bOnline services for agents\b",),
        )
        # The page that listed the report's fields is gone (HTTP 404 on 12 November 2026), so the
        # skill states only what the ATO's live bulletin says: the report was enhanced from
        # 18 April 2026 and shows the date each election was lodged.
        self.assert_sentence(step, r"\bdisplays details about elections\b", r"\b18 April 2026\b", r"\bdate lodged\b")
        # The ATO gives no view on validity, and the record keeps no TFN or date of birth.
        self.assert_sentence(step, r"\bno opinion\b", r"\bvalidity\b")
        self.assert_sentence(
            step, r"\bform type\b", r"\bincome year\b", r"\bcommencement date\b", r"\bdate lodged\b",
            r"\b(not|never)\W+(any\W+)?TFN\b", r"\b(not|never)\W+(any\W+)?(TFN\W+or\W+)?date of birth\b", r"\bown copies\b",
            affirmed=(r"\brecord each election, variation and revocation\b", r"\bcompare\b"),
        )
        # Each mismatch goes to the specialist, in its own clause.
        self.assert_sentence(
            step,
            r"\belection the report shows that the trust's records (do\W+not|don't|lack)\b",
            r"\bcopy that does\W+" + NOT + r"match\b",
            r"\bspecified individual other than the one\b",
            affirmed=(r"\blist\b[^,;:]*\bspecialist review\b",),
        )
        self.assert_sentence(
            step, r"\bfamily trusts page\b", r"\b10 November 2026\b", r"\bindividual other than its own specified individual\b",
            r"\bnarrows\b", r"\bcommon to both\b", r"\bdifferent specified individuals\b",
        )
        self.assert_sentence(step, r"\bcannot be accessed\b", affirmed=(r"\brecord\b[^,;:]*\bnot performed\b",))
        self.assert_sentence(
            step, r"\bwhat was lodged\b", NOT + r"(that\W+)?an election is valid\b", r"\bfamily group\b"
        )
        self.assert_carries(section("au-trust-distributions", "Inputs"), "interposed entity election report")
        self.assert_cited_and_recorded(
            "au-trust-distributions",
            "https://www.ato.gov.au/businesses-and-organisations/business-bulletins-newsroom/"
            "extension-of-gic-remission-offer-for-ftdt-liabilities",
            "https://www.ato.gov.au/businesses-and-organisations/trusts/family-trusts",
        )

    def test_sole_trader_screens_business_or_hobby_under_the_draft_as_a_draft(self) -> None:
        step = workflow_step("au-sole-trader", 0)
        self.assert_carries(
            step, "TR 2026/D2", "16 October 2026", "Human review pending", "4 November 2026", "item 4205",
            "2 November 2026",
        )
        # A draft for public comment, not a final ruling; the final is proposed to apply both ways.
        self.assert_sentence(
            step, r"\bTR 2026/D2\b", r"\bdraft for public comment\b", r"\bpreliminary view\b", NOT + r"(a\W+)?final ruling\b"
        )
        self.assert_sentence(step, r"\bcomments\b.*\b27 November 2026\b")
        self.assert_sentence(step, r"\bparagraph 108\b", affirmed=(r"\bproposed to apply both before and after\b",))
        self.assert_sentence(
            step, r"\bTo be advised\b", r"\bbefore relying\b",
            affirmed=(r"\bcheck\w*\b[^,;:]*\bfinal\b[^,;:]*\b(has|have)\W+(been\W+)?(issued|published)\b",),
        )
        # Every indicator in paragraph 14, each on its own.
        self.assert_sentence(
            step,
            r"\bparagraph 14\b", r"\bsignificant commercial purpose or character\b", r"\bintention to carry on a business\b",
            r"\bpurpose and prospect of profit\b", r"\bnot a hobby or recreation\b",
            r"\borganised and carried on in a business-like and systematic manner\b", r"\bsize and scale\b",
            r"\brepetition and regularity\b",
            affirmed=(r"\brecord\b[^,;:]*\bevidence\b[^,;:]*\beach indicator\b",),
        )
        self.assert_sentence(
            step, r"\bparagraph 15\b", r"\bin combination\b|\bas a whole\b|\btogether\b",
            r"\bno (one|single) indicator is (decisive|determinative)\b",
        )
        self.assert_sentence(
            step, r"\bparagraph 23\b", r"\bintend\w*\b[^,;:]*\bnot enough\b", r"\buntil\b[^,;:]*\b(started|commenced|begun)\b"
        )
        # The hobby signs in paragraph 50, each on its own.
        self.assert_sentence(
            step,
            r"\bparagraph 50\b", r"\bmore likely\b[^,;:]*\bhobby\b", r"\bpersonal enjoyment\b",
            r"\bno\W+contract or other obligation\b", r"\battendance\b", r"\bperformance\b", r"\btimeframes\b", r"\boutput\b",
            r"\b(no|without)\W+(\w+\W+)?steps\b[^,;]*\bprofitable\b", r"\bsmall in scale\b", r"\bnon-commercial\b",
            r"\bincidental\b",
        )
        # Neither a hobby nor a business can still be assessable, so its receipts stay.
        self.assert_sentence(
            step,
            r"\bparagraph 49\b", r"\bneither a hobby nor a business\b", r"\bpassive investment\b",
            r"\bisolated profit-making undertaking\b",
            affirmed=(
                r"\b(can|may)\W+still\W+(produce|be|give rise to|generate)\b[^,;:]*\bassessable\b",
                r"\bkeep\w*\b[^,;:]*\breceipts\b",
            ),
        )
        self.assert_sentence(
            step, r"\bprimary production\b", NOT + r"replace\b[^,;:]*\bTR 97/11\b", r"\bparagraph 3\b",
            affirmed=(r"\broute\b[^,;:]*`au-primary-production`",),
        )
        # Doubtful activities, each on its own, go to the reviewer, and later steps stay conditional.
        self.assert_sentence(
            step,
            r"\bmissing\b", r"\bpoints? both ways\b", r"\bcontent creation\b", r"\bparagraphs 194 to 205\b",
            r"\bside activity beside employment\b", r"\b(began|started) as a hobby\b", r"\brepeated losses\b",
            affirmed=(r"\broute\b[^,;:]*\breviewer\b", r"\bonly as conditional work\b"),
        )
        self.assert_sentence(
            step, r"\b(do not|never|not to)\W+conclude\b[^,;:]*\bbusiness\b", r"\breviewer's\b|\bfor the reviewer\b"
        )
        self.assert_carries(section("au-sole-trader", "Inputs"), "steps taken to make a profit", "regularity")
        self.assert_carries(section("au-sole-trader", "Hand-off"), "step 0 indicator record")
        self.assert_cited_and_recorded(
            "au-sole-trader",
            "https://www.ato.gov.au/law/view/document?DocID=DTR/TR2026D2/NAT/ATO/00001",
            "https://www.ato.gov.au/about-ato/ato-advice-and-guidance/advice-under-development-program/"
            "advice-under-development-income-tax-issues",
        )

    def test_psi_screens_each_psb_outcome_for_part_iva_under_pcg_2025_5(self) -> None:
        step = workflow_step("au-psi-review", 5)
        self.assert_carries(step, "PCG 2025/5", "28 November 2025", "Human review pending", "4 November 2026", "Part IVA")
        self.assert_sentence(
            step, r"\bparagraphs 1 and 15\b", r"\bcompany or trust conducting a PSB\b", r"\bindividual's PSI\b",
            affirmed=(r"\bmore likely to apply compliance resources\b",),
        )
        self.assert_sentence(step, r"\bparagraph 14\b", affirmed=(r"\bappl(y|ies)\b[^,;:]*\bboth before and after\b",))
        # The guideline's exclusions, each in its own clause, and the PSI rules for a wrong self-assessment.
        self.assert_sentence(
            step,
            r"\bparagraph 18\b", NOT + r"apply where\b",
            r"\bincome is\W+" + NOT + r"(PSI|personal services income)\b",
            r"\bentity\W+(does\W+|did\W+)?" + NOT + r"derive\b|\bentity\W+doesn't\W+derive\b",
            r"\b(wrongly|incorrectly)\W+self-assessed\b[^.]*\bPSI rules apply\b",
        )
        self.assert_sentence(
            step, r"\bbusiness structure\b", r"\bPCG 2021/4\b", r"\bparagraph 21\b",
            affirmed=(r"\broute\b[^,;:]*`au-professional-firm-profits`",),
        )
        self.assert_sentence(
            step, r"\bparagraph 25\b", NOT + r"(entitle|allow|permit)\w*\b[^,;:]*\bdivert or retain\b", r"\btax benefit\b"
        )
        # The facts recorded per individual and year, each on its own.
        self.assert_sentence(
            step,
            r"\beach individual and income year\b", r"\bnet PSI the entity derived\b", r"\bassessable income\b",
            r"\bsalary\b", r"\bdirector's fees\b", r"\bdividends\b", r"\btrust distributions\b", r"\bassociate\b",
            r"\bservice entity\b", r"\bservices it was for\b", r"\bnet PSI retained\b", r"\brecorded purpose\b",
            r"\bwhether that purpose was carried out\b",
            affirmed=(r"\brecord\b",),
        )
        self.assert_sentence(
            step, r"\blow-risk indicators in Table 1\b", r"\bhigher-risk indicators in Table 2\b", r"\bparagraph 40\b",
            affirmed=(r"\bcompare\b", r"\brecord\b[^,;:]*\bevidence shows\b", r"\bfacts are missing\b"),
        )
        self.assert_sentence(
            step, r"\b(sets|establishes|gives) no 'safe' level\b", r"\bparagraph 41\b", r"\bno safe harbour\b",
            r"\bparagraph 13\b",
        )
        self.assert_sentence(
            step,
            r"\bparagraph 11\b", NOT + r"apply compliance resources\b", r"\bgenuine attempt\b",
            r"\blow-risk arrangement by 30 June 2027\b",
            affirmed=(r"\brecord\b[^,;:]*\bstep\b[^,;:]*\bdate\b",),
        )
        self.assert_sentence(
            step, r"\bhigher-risk indicator\b", r"\bmissing facts\b", affirmed=(r"\broute\b[^,;:]*\bqualified review\b",)
        )
        self.assert_sentence(
            step, r"\b(do not|never|not to)\W+conclude\b[^,;:]*\blow risk\b", r"\bPart IVA does or does not apply\b"
        )
        self.assert_carries(section("au-psi-review", "Inputs"), "retained", "restructure step")
        self.assert_carries(section("au-psi-review", "Hand-off"), "Part IVA indicator record")
        self.assert_cited_and_recorded(
            "au-psi-review", "https://www.ato.gov.au/law/view/document?DocID=COG/PCG20255/NAT/ATO/00001"
        )

    def test_small_business_cgt_15_year_gain_of_a_trust_does_not_reach_beneficiaries_as_a_capital_gain(self) -> None:
        step = workflow_step("au-small-business-cgt", 3)
        self.assert_carries(step, "Human review pending", "4 November 2026", "compilation 268")
        self.assert_sentence(
            step, r"\b(s|section) 152-110\(1\)", r"\bs 102-5\(1\), step 1, note 2\b",
            affirmed=(
                r"\bdisregards\b[^,;:]*\bgain\b",
                r"\b(left out|excluded|not counted)\b[^,;:]*\bnet capital gain\b",
            ),
        )
        # A beneficiary's extra gain is measured from what remains of each trust gain after steps 1 to 6.
        self.assert_sentence(
            step,
            r"\bSubdivision 115-C\b", r"\beach capital gain of the trust estate\b", r"\bs 115-215\(3\)\)",
            r"\bremaining after steps 1 to 6\b", r"\bs 102-5\(1\)", r"\bs 115-225\(1\)\(a\)",
        )
        self.assert_sentence(
            step,
            r"\bdisregarded under s 152-110\(1\)", r"\bleaves no\b[^,;:]*\bamount\b",
            NOT + r"(flow|pass|reach)\w*\W+(\w+\W+){0,2}beneficiar\w*\W+as\W+a\W+capital gain\b",
            r"\bunlike\b[^,;:]*\bSubdivision 152-C\b", r"\bs 115-215\(3\)\(b\) and \(c\)",
        )
        # The conclusion is a reading of the provisions, and says so.
        self.assert_sentence(
            step,
            r"\bAct\b", NOT + r"say\w*\W+(this|so)\W+in terms\b", r"\breviewer\b[^.]*\bconfirm\b",
        )
        self.assert_sentence(
            step,
            r"\b(do not|never|not)\W+(show|report|include)\w*\b[^,;:]*\bbeneficiary statement\b",
            r"\bcapital gain\b", r"\bdiscount\b", r"\bindexation\b",
        )
        self.assert_sentence(
            step,
            r"\bneither assessable income nor exempt income\b", r"\bs 152-110\(2\)",
            r"\bexcept\b[^;]*\bbalancing adjustment event\b", r"\bDivision 40\b", r"\bDivision 328\b", r"\bs 152-110\(3\)",
        )
        # Each payment, and each fact s 152-125 turns on, on its own.
        self.assert_sentence(
            step,
            r"\bown line\b", r"\bdate\b", r"\bamount\b", r"\brecipient's position \(not name\)",
            r"\binterposed entity\b", r"\bCGT concession stakeholder just before the CGT event\b",
            r"\bparticipation percentage\b",
            affirmed=(r"\brecord each payment\b",),
        )
        self.assert_sentence(
            step,
            r"\bonly if\b", r"\bindividual who was a CGT concession stakeholder just before the CGT event\b",
            r"\bs 152-125\(1\)\(c\)\)\W+and\W+(it is made\W+)?before the later of 2 years after the event\b",
            r"\b6 months after the latest time\b", r"\blook-through earnout right\b", r"\bs 152-125\(1\)\(b\)",
            r"\bunless the Commissioner extends\b", r"\bs 152-125\(4\)",
            r"\bcompany or trust\b", r"\bthe recipient\b", r"\binterposed entity\b",
        )
        self.assert_sentence(step, r"\bonly up to the limit in s 152-125\(2\)", r"\bparticipation percentage\b")
        self.assert_sentence(
            step, r"\bcompany\b", r"\bwithin that limit\b", NOT + r"(a\W+)?dividend or a frankable distribution\b",
            r"\bs 152-125\(3\)",
        )
        self.assert_sentence(step, r"\bwages\b", NOT + r"(a\W+)?payment relating to the exempt amount\b")
        self.assert_sentence(
            step,
            r"\bafter that time\b", r"\bwho was\W+" + NOT + r"(a\W+)?stakeholder\b", r"\babove the limit\b",
            NOT + r"conclude\b",
            affirmed=(r"\blist\b[^,;:]*\bexception\b",),
        )
        self.assert_carries(section("au-small-business-cgt", "Inputs"), "exempt amount", "participation percentage")
        self.assert_carries(section("au-small-business-cgt", "Hand-off"), "payment schedule")
        self.assert_cited_and_recorded("au-small-business-cgt", "https://www.legislation.gov.au/C2004A05138/latest/text")

    def test_aml_ended_relationships_carry_a_retain_until_date_never_a_deletion_list(self) -> None:
        step = workflow_step("au-aml-ctf-client-coverage", 1)
        self.assert_carries(step, "Human review pending", "4 November 2026", "compilation 63", "2 November 2026")
        self.assert_sentence(
            step, r"\bno longer engaged\b", r"\bdate the business relationship ended\b", r"\bretain until\b",
            affirmed=(r"\brecord\b", r"\blabel\b[^,;:]*`retain`"),
        )
        # The 7 years run from the end of the relationship, or of an occasional transaction.
        self.assert_sentence(
            step,
            r"\bSection 111\(2\)", r"\bcustomer due diligence\b", r"\buntil the end of the 7[- ]year period\b",
            r"\bbegins when the business relationship ends\b", r"\bor when it completes an occasional transaction\b",
            affirmed=(r"\brequires\b[^,;:]*\bretain\b",),
        )
        # The date covers only those records; ss 107 and 108 start their own clocks.
        self.assert_sentence(
            step,
            r"\bcovers only\b[^,;:]*\bcustomer due diligence records\b",
            r"\btransaction records\b[^,;]*\bfrom the day each record is made\b", r"\bs 107\(3\)",
            r"\bdocuments a customer gives\b[^,;]*\bfrom when they are given\b", r"\bs 108\(2\)",
            NOT + r"apply the date to them\b",
        )
        self.assert_sentence(
            step, r"\bending on 5 April 2029\b", r"\buntil 4 April 2036\b", affirmed=(r"\b(use|apply|follow) that convention\b",)
        )
        self.assert_sentence(
            step,
            r"\bengagement end date\b", r"\bonly where\b[^;]*\bdesignated services ended\b",
            r"\botherwise\b[^.]*`UNVERIFIED`", r"\bcompliance officer\b",
        )
        # A retention list, never a deletion list; destruction is the officer's decision.
        self.assert_sentence(
            step, r"\bnever a deletion list\b", NOT + r"delete\b", r"\barchive\b", r"\bmark for removal\b"
        )
        self.assert_sentence(
            step,
            r"\balready past\b", r"\bwhether and how a record is destroyed\b", r"\bfirm's policies\b",
            affirmed=(
                r"\blist\b[^,;:]*\bcompliance officer\b",
                r"\bleave\b[^,;:]*\bdestroyed\b[^,;:]*\b(that officer|compliance officer|authorised person)\b",
            ),
        )
        self.assert_sentence(step, r"\bPrivacy Act 1988\b", r"\bs 119\b", NOT + r"limit any other obligation\b")
        self.assert_carries(workflow_step("au-aml-ctf-client-coverage", 5), "'retain until' date")
        self.assert_cited_and_recorded(
            "au-aml-ctf-client-coverage",
            "https://www.austrac.gov.au/industry-and-business/obligations-and-guidance/your-amlctf-program/"
            "develop-your-amlctf-programs/record-keeping/record-keeping-overview",
            "https://www.legislation.gov.au/C2006A00169/latest",
        )

    def test_pre_lodgement_compares_work_related_claims_with_taxation_statistics_as_a_question(self) -> None:
        step = workflow_step("au-pre-lodgement-review", 4)
        self.assert_carries(step, "Human review pending", "4 November 2026", "17 June 2026", "2023-24 income year")
        self.assert_sentence(
            step, r"\bwork-related expense claims\b", r"\btaxation statistics\b",
            affirmed=(r"\b(as a|only as a) reviewer question only\b|\bas a reviewer question\b",),
        )
        # What each table holds, each dimension on its own.
        self.assert_sentence(
            step,
            r"\bTable 14A\b", r"\boccupation unit group\b", r"\bsex\b", r"\btaxable income range\b",
            r"\bnumber of individuals claiming\b", r"\btotal amount claimed\b", r"\beach work-related expense type\b",
            r"\btotal work-related expenses\b",
        )
        self.assert_sentence(
            step, r"\bTable 18B\b", r"\boccupation sub-major group\b", r"\bsex\b", r"\bdeduction claimed range\b"
        )
        # The return's 6-digit code reaches a table row only through a recorded, verified mapping.
        self.assert_sentence(
            step, r"\b6-digit code\b", r"\bTable 14A\b[^.]*\b4-digit unit group\b",
            r"\bTable 18B\b[^.]*\b2-digit sub-major group\b", r"\bmay apply to more than one occupation\b",
        )
        self.assert_sentence(
            step, r"\bthe client's code\b", r"\bcode list's year\b", r"\btable row\b[^,;:]*\bevidence\b",
            r"\bexpense type column or deduction label\b",
            affirmed=(r"\brecord a verified mapping\b",),
        )
        self.assert_sentence(
            step, r"\b(do not|never)\W+take the row from the code's leading digits alone\b", r"\b91 to 99\b"
        )
        # No published average: derive one and record its inputs.
        self.assert_sentence(
            step,
            r"\b(neither|no)\W+table\W+publishes\W+an\W+average\b",
            r"\bthe table\b", r"\bthe income year\b", r"\bthe occupation code\b", r"\brows summed\b", r"\bderived figure\b",
            affirmed=(r"\bderive\b", r"\bdivid\w*\b"),
        )
        self.assert_sentence(
            step, r"\bprivacy\b", r"\boccupation is\W+" + NOT + r"recorded\b", r"\bhas no row\b",
            r"\blacks a verified mapping\b",
            affirmed=(r"\btreat\b[^,;:]*\bapproximate\b", r"\brecord\b[^,;:]*\bnot performed\b"),
        )
        self.assert_sentence(
            step, r"\bstatistics year can differ\b", affirmed=(r"\bcheck\b[^,;:]*\blater release\b",)
        )
        # A question for the reviewer, never a level to claim up to.
        self.assert_sentence(
            step, r"\babove the derived figure\b", r"\bsteps 2 and 3\b", affirmed=(r"\blist\b[^,;:]*\bquestion for the reviewer\b",)
        )
        self.assert_sentence(
            step,
            r"\bnever\W+present\b[^.]*\bclaim up to\b", r"\btarget\b", r"\bevidence that a claim is or is not allowable\b",
            r"\b(do not|never)\W+raise, lower or set a claim\b",
        )
        self.assert_carries(section("au-pre-lodgement-review", "Inputs"), "occupation code")
        self.assert_cited_and_recorded(
            "au-pre-lodgement-review",
            "https://www.ato.gov.au/about-ato/research-and-statistics/in-detail/taxation-statistics/taxation-statistics-2023-24/"
            "statistics-in-taxation-statistics-2023-24/individuals-statistics-for-taxation-statistics-2023-24",
            "https://www.ato.gov.au/forms-and-instructions/salary-and-wage-occupation-codes",
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
            r"\bs 118-195\(1\)\(c\)", r"\bcolumn 2\b[^,;:]*\band\b[^,;:]*\bcolumn 3\b",
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
            r"\blonger period the Commissioner allows\W+or from the death until\b",
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
            step, r"\bspecified period\b", r"\bafter it expires\b", r"\bcannot be disregarded under s 118-195\(1\)",
            r"\bpart of it may be disregarded under s 118-200\b", r"\bparagraphs 24 and 25\b",
        )
        # The expiry defeats only item 2(b), so the other column 3 routes are tested before s 118-200.
        self.assert_sentence(
            step, r"\bonly item 2\(b\)", r"\bparagraph 6\b", r"\bdefeats only the right-to-occupy route\b",
            r"\bwithin 2 years of the death or a longer period the Commissioner allows\b",
            r"\bspouse\b", r"\bdisposing beneficiary\b", r"\bbefore falling back to s 118-200\b",
            affirmed=(r"\bstill test\b",),
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
        self.assert_sentence(step, r"\bonly wrapping through a smart contract\b", r"\blocks\b",
            r"\bmints\b[^,;:]*,?\s*\b(one for one|on a 1:1 basis)\b", r"\bparagraph 2\b",
            affirmed=(r"\b(one for one|on a 1:1 basis)\b",),
        )
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
            # Backticked, because a quoted skill name gives that skill behavioural gate credit.
            "4 November 2026", "`au-wfh-deductions`", "`au-car-expenses`", "`au-travel-expenses`",
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
            affirmed=(r"\b(lets the Board|allows the Board to) suspend\b",),
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

    def test_transfer_duty_lists_dutiable_asset_classes_by_jurisdiction(self) -> None:
        """Each jurisdiction's row is read cell by cell, so a rule stays with its state and column."""
        skill = "au-transfer-duty"
        step = workflow_step(skill, 1)
        self.assert_sentence(step, r"\bHuman review pending\b", r"\bon 4 November 2026\b", r"\bnot a human review\b")
        # Every asset class is listed with its location and allocation, each class on its own.
        self.assert_sentence(
            step, r"\bassociated agreements?\b", r"\blocation\b", r"\bconsideration or value\b", r"\bland\b",
            r"\bfixtures\b", r"\bleases\b", r"\bplant and equipment\b", r"\bstock-in-trade\b", r"\blivestock\b",
            r"\bregistered vehicles\b", r"\bgoodwill\b", r"\bintellectual property\b", r"\bbusiness licences\b",
            r"\bdebts\b",
            affirmed=(r"\blist every asset class\b",),
        )
        # Each class is tested at the revenue office where the asset is, with its page and read date;
        # a class the guidance does not settle stays UNVERIFIED and is never taken as non-dutiable.
        self.assert_sentence(
            step, r"\brevenue office of the jurisdiction where the asset is located\b", r"\bpage\b", r"\bdate\b",
            affirmed=(r"\brecord whether\b",),
        )
        self.assert_sentence(step, NOT + r"settle\b", NOT + r"non-dutiable\b", affirmed=(r"`UNVERIFIED`",))
        # Goods that are not dutiable alone can be with land, so the classes are tested together.
        self.assert_sentence(
            step, NOT + DUTIABLE + r"\W+on their own\b", r"\bwith land or other dutiable property\b",
            affirmed=(r"\btest the classes together\b", r"\baggregate\b"),
        )
        self.assert_sentence(step, r"\bnt\.gov\.au\b", NOT + r"indexed\b", r"\boutside the reviewed fetch list\b")
        self.assert_sentence(step, affirmed=(r"\bconfirm each row\b[^.]*\bAct for the transaction date\b",))
        self.assert_sentence(step, r"\bdecides no liability, value, exemption or concession\b")

        goods, excluded, other = table_row(skill, "Workflow", "New South Wales")
        self.assert_carries(goods, "Revenue NSW", "4 November 2026")
        self.assert_sentence(goods, affirmed=(DUTIABLE + r"\W+when\b[^.]*\bincludes other dutiable property\b",))
        self.assert_sentence(goods, r"\bfixtures\b", r"\binterest in land\b", r"\balways\W+" + DUTIABLE)
        self.assert_carries(
            excluded, "stock-in-trade", "materials held for use in manufacture", "goods under manufacture",
            "primary production land", "livestock", "registered vehicles", "ships or vessels",
        )
        self.assert_sentence(
            other, r"\bgoodwill\b", r"\bintellectual property\b", r"\bstatutory licences\b", r"\bdebtor receivables\b",
            r"\bare\W+" + NOT + DUTIABLE,
        )

        goods, excluded, other = table_row(skill, "Workflow", "Victoria")
        self.assert_carries(goods, "SRO Victoria", "24 August 2026")
        self.assert_sentence(
            goods, r"\bdutiable transaction over an estate or interest in land\b",
            r"\bincluding goods used in connection with a business\b", r"\bs 10\(1\) Duties Act 2000\b",
            affirmed=(r"\bgoods in Victoria are\W+" + DUTIABLE + r"\W+where\b",),
        )
        self.assert_sentence(
            goods, r"\bDA-054\b", r"\b1 March 2011\b", r"\bunder review\b",
            r"\bpredates the fixtures provisions of 19 June 2019\b",
        )
        self.assert_sentence(goods, affirmed=(r"\bfixtures are always\W+" + DUTIABLE,))
        self.assert_carries(
            excluded, "stock-in-trade", "materials held for use in manufacture", "goods under manufacture",
            "primary production", "livestock", "s 10(1)(d)",
        )
        self.assert_sentence(
            other, r"\bDA-029\b", r"\bDuties Act 2000\b", NOT + r"charge duty separately on the sale of a business\b"
        )
        self.assert_sentence(
            other, r"\bintangible items\b", r"\blicences\b", r"\bunbundled water entitlements\b",
            r"\bare\W+" + NOT + DUTIABLE + r"\W+as goods\b",
        )

        goods, excluded, other = table_row(skill, "Workflow", "Queensland")
        self.assert_carries(goods, "Queensland Revenue Office", "8 January 2025")
        self.assert_sentence(
            goods, r"\bonly if\b[^.]*\bincludes another type of dutiable property or is aggregated with\b",
            affirmed=(r"\bchattel in Queensland is\W+" + DUTIABLE,),
        )
        self.assert_carries(excluded, "None listed on the pages read")
        self.assert_sentence(
            excluded, r"\bpersonal property in Queensland\b", r"\btrading stock\b", r"\bplant and equipment\b",
            affirmed=(r"\bitself a business asset\b",),
        )
        self.assert_sentence(
            other, r"\bgoodwill\b", r"\bstatutory business licence\b", r"\bright to use one\b", r"\bbusiness name\b",
            r"\bfranchise arrangement\b", r"\bdebtor lives in Queensland\b", r"\bsupply right\b",
            r"\bintellectual property\b", r"\bpersonal property in Queensland\b",
            affirmed=(r"\bbusiness assets are\W+" + DUTIABLE,),
        )
        self.assert_sentence(
            other, r"\bsolely for a debt, a supply right or intellectual or personal property\b",
            r"\bwith no other property\b", r"\bmay\W+" + NOT + r"be\W+" + DUTIABLE, r"\bs 37\b", r"\b27 September 2024\b",
        )

        goods, excluded, other = table_row(skill, "Workflow", "Western Australia")
        self.assert_carries(goods, "RevenueWA", "2 June 2026")
        self.assert_sentence(
            goods,
            affirmed=(
                r"\bchattels such as plant and equipment are\W+" + DUTIABLE
                + r"\W+when transferred with other dutiable property, including business assets\b",
            ),
        )
        self.assert_carries(
            excluded, "stock-in-trade", "held for use in or under manufacture", "primary production business",
            "livestock", "vehicle licence duty", "ships or vessels",
        )
        self.assert_sentence(excluded, r"\bfixed to land is land, with listed exceptions\b")
        self.assert_sentence(
            other, r"\bgoodwill\b", r"\brestraint of trade\b", r"\bbusiness identity\b", r"\bbusiness licence\b",
            r"\buncompleted supply contract\b", r"\bintellectual property\b", r"\brent rolls\b", r"\bclient lists\b",
            r"\bbut not a trade debt\b",
            affirmed=(r"\bWA business assets are\W+" + DUTIABLE,),
        )
        self.assert_sentence(
            other, r"\bintellectual property alone is\W+" + NOT + DUTIABLE,
            r"\bunless aggregated with another WA business asset or chattel\b",
        )

        goods, excluded, other = table_row(skill, "Workflow", "South Australia")
        self.assert_carries(goods, "RevenueSA Information Circular 99", "10 May 2017", "status current")
        self.assert_sentence(goods, r"^" + NOT + DUTIABLE + r"\W*$")
        self.assert_sentence(
            goods, r"\binterests in land such as a lease, fixtures and items fixed to land\b",
            affirmed=(r"\bonly a conveyance of land is\W+" + DUTIABLE,),
        )
        self.assert_sentence(
            goods, r"\bgoods with a significant connection to transferred land\b",
            r"\bonly to transactions from 18 June 2015 to 30 June 2016\b",
        )
        self.assert_sentence(
            other, r"\bplant and equipment that is\W+" + NOT + r"fixed\b", r"\bgoodwill\b", r"\bintellectual property\b",
            r"\breceivables\b", r"\bstatutory leases and licences\b", r"\bare\W+" + NOT + DUTIABLE,
        )

        goods, excluded, other = table_row(skill, "Workflow", "Tasmania")
        self.assert_carries(goods, "SRO Tasmania")
        self.assert_sentence(
            goods, r"^" + NOT + DUTIABLE + r"\W+by themselves\b",
            r"\bbut\W+" + DUTIABLE + r"\W+when transferred in an arrangement that includes other dutiable property\b",
            r"\bfreehold interest in land, a mineral tenement or a lease of the business premises\b",
            r"\bnew lease the sale is conditional on\b",
        )
        self.assert_carries(
            excluded, "stock in trade", "materials held for use in manufacture", "goods under manufacture",
            "livestock", "registered motor vehicles", "business assets guideline",
        )
        self.assert_sentence(
            other, r"\bbusiness goodwill \(but not site goodwill\)", r"\bintellectual property\b",
            r"\bare\W+" + NOT + DUTIABLE,
        )

        goods, excluded, other = table_row(skill, "Workflow", "Australian Capital Territory")
        self.assert_carries(goods, "DAA011.3", "18 September 2017", "status current")
        self.assert_sentence(
            goods, r"\bincludes a dutiable transaction over other dutiable property, other than intellectual property\b",
            r"\bCrown lease\b", r"\bcommercial lease with a premium\b",
            affirmed=(DUTIABLE + r"\W+only if\b",),
        )
        self.assert_sentence(goods, r"\bfixtures are\W+" + NOT + r"goods\b", affirmed=(DUTIABLE + r"\W+as land\b",))
        self.assert_carries(
            excluded, "stock-in-trade", "materials held for use in manufacture", "goods under manufacture",
            "primary production land", "livestock", "registered motor vehicle", "ship or vessel",
        )
        self.assert_sentence(other, r"^" + NOT + r"addressed\b", r"`UNVERIFIED`")

        goods, excluded, other = table_row(skill, "Workflow", "Northern Territory")
        self.assert_carries(goods, "Territory Revenue Office")
        self.assert_sentence(
            goods,
            affirmed=(
                r"\bplant and equipment is\W+" + DUTIABLE + r"\W+only if acquired with other dutiable property\b",
                r"\bchattels acquired with land or a lease of land are\W+" + DUTIABLE
                + r"\W+except where that lease has nil or nominal value\b",
            ),
        )
        # The earlier law still governs a conveyance first executed before 9 May 2023, one replacing
        # such a conveyance, one whose property was agreed or optioned before then and one under a put
        # option granted before then (s 116(1)(a) to (d)).
        self.assert_sentence(
            goods, r"\bs 116 of the Stamp Duty Act 1978\b", r"\b1 July 2025\b", r"\bimmediately before 9 May 2023\b",
            r"\bfirst executed before that date\b",
            r"\breplacing an earlier conveyance\b[^;]*\bfirst executed before that date\b",
            r"\bagreement or option to purchase entered into or granted before that date\b",
            r"\boption granted before that date to require another person to purchase it\b",
            r"\(s 116\(1\)\(a\) to \(d\)\)",
            affirmed=(r"\bstill apply\b",),
        )
        self.assert_carries(
            excluded, "stock-in-trade", "materials held for manufacture", "goods under manufacture", "livestock",
            "motor vehicles to be registered or transferred",
        )
        # Intangibles are not dutiable only for a conveyance from 9 May 2023 outside s 116; for one
        # it covers, the earlier s 4 definition made them dutiable property.
        self.assert_sentence(
            other, r"\bfirst executed on or after 9 May 2023\b", r"\bs 116 does\W+" + NOT + r"cover\b",
            r"\bgoodwill\b", r"\bbusiness names\b", r"\btrademarks\b", r"\bregistered designs\b",
            r"\bcopyright\b", r"\bpatents\b", r"\bis\W+" + NOT + DUTIABLE,
            r"\bcertain statutory licences relating to mining are\W*$",
        )
        self.assert_sentence(
            other, r"\bs 116 covers\b", r"\bs 4 immediately before 9 May 2023\b", r"\bparagraphs \(b\) to \(ga\)",
            r"\bgoodwill of a business undertaking\b", r"\bbusiness name, trading name or trade mark\b",
            r"\ba patent, a registered design or a copyright\b",
            r"\bstatutory licence or permission used in connection with a business undertaking\b",
            affirmed=(r"\balso (included|covered)\b",),
        )

        self.assert_carries(section(skill, "Inputs"), "associated agreements", "location")
        self.assert_carries(
            section(skill, "Primary-source starting point"),
            "New South Wales:", "Victoria:", "Queensland:", "Western Australia:", "South Australia:", "Tasmania:",
            "Australian Capital Territory:", "Northern Territory:",
        )
        self.assert_cited_and_recorded(
            skill,
            "https://www.revenue.nsw.gov.au/taxes-duties-levies-royalties/transfer-duty/understanding-transfer-duty/"
            "business-purchases",
            "https://www.sro.vic.gov.au/buying-property/land-transfer-stamp-duty/managing-duty-transactions/"
            "evidentiary-requirements-manual/transfer-land-and-business-andor-goods",
            "https://www.sro.vic.gov.au/about-us/laws-legal-cases-and-rulings/public-rulings/transfers-land-and-business",
            "https://www.sro.vic.gov.au/about-us/laws-legal-cases-and-rulings/public-rulings/"
            "goods-held-or-used-connection-with-land",
            "https://qro.qld.gov.au/definition/dutiable-property/",
            "https://qro.qld.gov.au/duties/investors/business/assessing/",
            "https://www.wa.gov.au/government/publications/duties-fact-sheet-business-assets",
            "https://revenuesa.sa.gov.au/tools-and-resources/resources/publications/information-circulars/"
            "information-circulars/ic_099",
            "https://www.sro.tas.gov.au/property-transfer-duties/dutiable-transactions/sales-of-business",
            "https://www.sro.tas.gov.au/Documents/duty-payable-purchase-business-assets-guideline.pdf",
            "https://www.revenue.act.gov.au/__data/assets/pdf_file/0005/2945597/DAA011.3-dutiable-goods.pdf",
            "https://treasury.nt.gov.au/dtf/territory-revenue-office/stamp-duty",
        )

    def test_land_tax_routes_each_jurisdiction_to_its_office_act_owner_and_notice(self) -> None:
        """Each row is read cell by cell, so an office, Act or ownership rule stays with its jurisdiction."""
        skill = "au-land-tax"
        step = workflow_step(skill, 1)
        self.assert_sentence(step, r"\bHuman review pending\b", r"\bon 4 November 2026\b", r"\bnot a human review\b")
        self.assert_sentence(step, affirmed=(r"\broute the work to the revenue office and Act\b",))
        self.assert_sentence(
            step, r"\btitle\b", r"\bcontract\b", r"\bsettlement evidence\b",
            affirmed=(r"\brecord who owned each parcel\b",),
        )
        # The table carries no figure; each comes from the office's current page.
        self.assert_sentence(
            step, r"\bno rate\b", r"\bthreshold\b", r"\btaxing date\b", r"\bdue date\b", r"\bfee\b",
            affirmed=(r"\bread each from the revenue office's current page\b",),
        )
        self.assert_sentence(step, r"\blegislation register links\b", NOT + r"indexed\b", r"\byet\b")
        self.assert_sentence(step, affirmed=(r"\bconfirm each row\b[^.]*\bAct for the assessment year\b",))
        self.assert_sentence(step, r"\bdecides no liability, exemption or surcharge\b")

        def acts(cell: str, *links: tuple[str, str]) -> None:
            for name, url in links:
                with self.subTest(act=name):
                    self.assertRegex(cell, rf"\[{re.escape(name)}\b[^\]]*\]\({re.escape(url)}\)")

        office, act, owner, notice, surcharge = table_row(skill, "Workflow", "New South Wales")
        self.assert_carries(office, "Revenue NSW")
        acts(
            act,
            ("Land Tax Act 1956", "https://legislation.nsw.gov.au/view/html/inforce/current/act-1956-027"),
            ("Land Tax Management Act 1956", "https://legislation.nsw.gov.au/view/html/inforce/current/act-1956-026"),
        )
        self.assert_sentence(
            owner, r"\bnon-exempt land\b", r"\bmidnight on the taxing date\b", r"\bfull year\b",
            affirmed=(r"\bassesses\b",),
        )
        self.assert_sentence(notice, r"\bpost\b", r"\bemail\b", r"\bopted in\b")
        self.assert_sentence(notice, r"\bdownload\w*\b[^.]*\bLand Tax Online\b")
        self.assert_sentence(surcharge, r"\bsurcharge land tax\b", r"\bforeign\b", r"\bresidential land\b")

        office, act, owner, notice, surcharge = table_row(skill, "Workflow", "Victoria")
        self.assert_carries(office, "State Revenue Office Victoria")
        acts(act, ("Land Tax Act 2005", "https://www.legislation.vic.gov.au/in-force/acts/land-tax-act-2005"))
        self.assert_sentence(owner, r"\bmidnight on the taxing date in the previous year\b")
        self.assert_sentence(
            owner, r"\bsells during the year\b", r"\bfull year's land tax\b",
            affirmed=(r"\bremains (?:responsible|liable)\b",),
        )
        self.assert_sentence(notice, r"\bMy Land Tax\b", r"\b(?:view|download)\b")
        self.assert_carries(notice, "myGov")
        self.assert_sentence(surcharge, r"\babsentee owner surcharge\b", r"\b(?:appears|included) in the land tax assessment\b")
        self.assert_sentence(surcharge, r"\bvacant residential land tax\b", r"\bseparate tax\b", r"\bown assessment\b")
        self.assert_sentence(surcharge, r"\bwindfall gains tax\b[^.]*\bstep 5\b")

        office, act, owner, notice, surcharge = table_row(skill, "Workflow", "Queensland")
        self.assert_carries(office, "Queensland Revenue Office")
        acts(act, ("Land Tax Act 2010", "https://www.legislation.qld.gov.au/view/html/inforce/current/act-2010-015"))
        self.assert_sentence(
            owner, r"\bfreehold land\b", r"\bmidnight on the taxing date\b",
            NOT + r"(?:divide|split|apportion) the liability between buyer and seller\b",
        )
        self.assert_sentence(notice, r"\bpost\b", r"\bemail\b", r"\bQRO Online\b")
        self.assert_sentence(surcharge, r"\babsentee surcharge\b", r"\bforeign surcharge\b", r"\bassessment notice\b")

        office, act, owner, notice, surcharge = table_row(skill, "Workflow", "Western Australia")
        self.assert_carries(office, "RevenueWA")
        acts(
            act,
            ("Land Tax Assessment Act 2002", "https://www.legislation.wa.gov.au/legislation/statutes.nsf/law_a6341.html"),
            ("Land Tax Act 2002", "https://www.legislation.wa.gov.au/legislation/statutes.nsf/law_a6340.html"),
        )
        self.assert_sentence(owner, r"\bmidnight on the taxing date of the previous assessment year\b")
        self.assert_sentence(owner, r"\bsells during the year\b", affirmed=(r"\bstill liable\b",))
        self.assert_sentence(notice, r"\bNotice of Assessment\b", r"\bemail\b")
        self.assert_carries(notice, "online services portal")
        self.assert_sentence(surcharge, r"^(?:none|no surcharge\w*) (?:is |are )?named\b")
        self.assert_sentence(
            surcharge, r"\bmetropolitan region improvement tax\b", r"\bwith land tax\b", r"\bPerth metropolitan region\b",
            affirmed=(r"\bmay be payable\b",),
        )

        office, act, owner, notice, surcharge = table_row(skill, "Workflow", "South Australia")
        self.assert_carries(office, "RevenueSA")
        acts(act, ("Land Tax Act 1936", "https://www.legislation.sa.gov.au/lz?path=%2FC%2FA%2FLAND%20TAX%20ACT%201936"))
        self.assert_sentence(
            owner, r"\bmidnight on the taxing date\b", r"\bvendor who sells after it\b", r"\bfull land tax\b",
            affirmed=(r"\bremains liable\b",),
        )
        self.assert_sentence(notice, r"\bLand Tax Assessment\b", r"\bemail billing\b")
        self.assert_sentence(
            notice, r"\bseparate assessments\b", r"\bownership structures\b", r"\bon trust\b", r"\bcorporate groups\b"
        )
        self.assert_sentence(surcharge, r"^(?:none|no surcharge\w*) (?:is |are )?named\b")

        office, act, owner, notice, surcharge = table_row(skill, "Workflow", "Tasmania")
        self.assert_carries(office, "State Revenue Office Tasmania")
        acts(
            act,
            ("Land Tax Act 2000", "https://www.legislation.tas.gov.au/view/html/inforce/current/act-2000-074"),
            ("Land Tax Rating Act 2000", "https://www.legislation.tas.gov.au/view/html/inforce/current/act-2000-073"),
        )
        self.assert_sentence(owner, r"\bGeneral Land\b", r"\btaxing date\b", affirmed=(r"\bpays\b",))
        self.assert_sentence(
            owner, r"\bPrincipal Residence Land\b", NOT + r"(?:be\W+)?(?:subject to land tax|apply)\b"
        )
        self.assert_sentence(notice, r"\bemail\b")
        self.assert_sentence(surcharge, r"\bforeign investor land tax surcharge\b", r"\bGeneral Land\b")

        office, act, owner, notice, surcharge = table_row(skill, "Workflow", "Australian Capital Territory")
        self.assert_carries(office, "ACT Revenue Office")
        acts(act, ("Land Tax Act 2004", "https://www.legislation.act.gov.au/a/2004-4/"))
        self.assert_sentence(owner, r"\bquarterly\b", r"\bfirst day of each quarter\b", r"\bwhole quarters\b", r"\bno pro-rating\b")
        # Land tax reaches only residential property that is not the owner's home, never commercial property.
        self.assert_sentence(
            owner, r"\bresidential property\b", r"\b(?:is|are)\W+" + NOT + r"the owner's principal place of residence\b",
            NOT + r"(?:apply\W+)?to commercial property\b",
            affirmed=(r"\bland tax applies to residential property\b",),
        )
        self.assert_sentence(owner, r"\bmust\b[^.]*\b(?:tell|notify)\b[^.]*\boffice\b", r"\bbecomes liable\b")
        self.assert_sentence(notice, r"\bemail or post\b", r"\bnotice delivery preferences\b")
        self.assert_sentence(surcharge, r"\bforeign ownership surcharge\b")

        office, act, owner, notice, surcharge = table_row(skill, "Workflow", "Northern Territory")
        self.assert_carries(office, "Territory Revenue Office")
        self.assert_sentence(act, r"^None listed\b", r"\bmain revenue Acts\b", r"\bno land tax Act\b")
        for cell in (owner, notice):
            self.assert_sentence(cell, r"^" + NOT + r"stated\b")
        self.assert_sentence(surcharge, r"^None named\b")
        # The office's list names no land tax Act, but it does not say none is levied.
        self.assert_sentence(
            step, r"\bTerritory Revenue Office page\b",
            r"\bdoes\W+" + NOT + r"(?:say|state) in terms that the Territory levies no land tax\b",
        )
        self.assert_sentence(
            step, r"\bno land tax authority was found\b", r"`UNVERIFIED`",
            affirmed=(r"\bprepare an enquiry item for the responsible practitioner\b",),
        )
        self.assert_sentence(step, r"\bDo not contact the office\b", r"\ban authorised human handles the enquiry\b")

        # Victorian windfall gains tax keeps its own step.
        self.assert_sentence(
            workflow_step(skill, 5), r"\bwindfall gains tax separate from land tax\b", affirmed=(r"\bkeep\b",)
        )
        self.assert_carries(workflow_step(skill, 5), "deferral", "`au-transfer-duty`")

        self.assert_carries(
            section(skill, "Primary-source starting point"),
            "New South Wales:", "Victoria:", "Queensland:", "Western Australia:", "South Australia:", "Tasmania:",
            "Australian Capital Territory:", "Northern Territory:",
        )
        self.assert_cited_and_recorded(
            skill,
            "https://www.revenue.nsw.gov.au/taxes-duties-levies-royalties/land-tax/your-assessment-notice/"
            "understand-your-assessment-notice",
            "https://www.sro.vic.gov.au/owning-property/land-tax/understanding-land-tax",
            "https://www.sro.vic.gov.au/owning-property/vacant-residential-land-tax/"
            "understanding-vacant-residential-land-tax",
            "https://qro.qld.gov.au/land-tax/pay/assessment/",
            "https://www.wa.gov.au/organisation/department-of-treasury-and-finance/land-tax-assessment",
            "https://revenuesa.sa.gov.au/landtax",
            "https://www.sro.tas.gov.au/land-tax",
            "https://www.revenue.act.gov.au/rates-and-property-charges/land-tax/about-land-tax",
            "https://www.revenue.act.gov.au/rates-and-property-charges/land-tax/how-land-tax-is-calculated",
            "https://treasury.nt.gov.au/dtf/territory-revenue-office/legislation",
        )

        # One card per jurisdiction that levies land tax routes to that office and its Acts.
        cards = {
            "nsw-sole-and-joint-notices": ("Revenue NSW", "Land Tax Act 1956", "Land Tax Management Act 1956"),
            "vic-absentee-vacant-home": ("State Revenue Office Victoria", "Land Tax Act 2005"),
            "qld-sale-after-taxing-date": ("Queensland Revenue Office", "Land Tax Act 2010"),
            "wa-metropolitan-notice": ("RevenueWA", "Land Tax Assessment Act 2002", "Land Tax Act 2002"),
            "sa-trust-assessment": ("RevenueSA", "Land Tax Act 1936"),
            "tas-shack-and-home": ("State Revenue Office Tasmania", "Land Tax Act 2000", "Land Tax Rating Act 2000"),
            "act-rented-former-home": ("ACT Revenue Office", "Land Tax Act 2004"),
        }
        cases = SKILLS.parents[1] / "validation" / "cases"
        for card, (office, *named) in cards.items():
            text = (cases / f"au-land-tax-{card}.md").read_text(encoding="utf-8")
            checks = text.split("## Required checks", 1)[1].split("\n## ", 1)[0]
            bullets = [" ".join(item.split()) for item in checks.split("\n- ")[1:]]
            patterns = [rf"\broute\b[^.;]*?\bto (?:the )?{re.escape(office)}\b",
                        *(rf"\b{re.escape(name)}\b" for name in named)]
            with self.subTest(card=card):
                self.assertTrue(
                    any(all(re.search(pattern, bullet, re.IGNORECASE) for pattern in patterns) for bullet in bullets),
                    f"no required check routes to {office} and {named}",
                )

    def test_xero_exports_names_the_gst_pack_the_tax_schedules_and_the_older_bas_trail(self) -> None:
        skill, heading = "xero-exports", "The core exports"
        _, gotchas = table_row(skill, heading, "Activity Statement / GST Reconciliation")
        # The menu caveat stays. On the older BAS the trail is the GST Audit report, generated only
        # with the activity statement; the legacy .xls note is scoped to the older report.
        self.assert_sentence(gotchas, r"\b(there is no|no) report (is )?named 'GST Audit Report'[^.;]*\bAU menu\b")
        self.assert_sentence(
            gotchas, r"\bolder BAS\b", r"\bGST Audit report\b", r"\bonly when the activity statement is run\b",
            r"\b(cannot|can ?not|can't)\W+be run by itself\b",
        )
        self.assert_sentence(gotchas, r"\bby tax rate\b", r"\bBAS Excluded section\b", r"\bleft off the statement\b")
        self.assert_sentence(
            gotchas, affirmed=(r"\bagree each tax rate subtotal\b", r"\brecord\b[^.]*\bwhich BAS the organisation uses\b")
        )
        self.assert_sentence(gotchas, r"\bnew Activity Statement\b", r"\bequivalent Transactions tab\b")
        self.assert_sentence(gotchas, r"`GST Reconciliation`, the older report, exports as legacy `\.xls`")

        satisfies, gotchas = table_row(skill, heading, "GST Reconciliation (New report pack)")
        self.assert_carries(satisfies, "new BAS", "GST lodged", "last filed amounts")
        self.assert_sentence(gotchas, r"\bbeta\b", r"\bnew BAS only\b")
        self.assert_sentence(
            gotchas, r"`GST collected and GST paid`", r"`GST amount`", r"`GST on imports`", r"`Adjusted by`",
            r"\b1A or 1B\b", r"`Lodged`", r"`Variance`", affirmed=(r"\bcompares\b",),
        )
        self.assert_sentence(
            gotchas, r"`GST account summary`", r"\bGST account balance\b", r"\blast filed GST amounts\b",
            r"`Closing balance variance`", affirmed=(r"\bcompares\b",),
        )
        self.assert_sentence(gotchas, affirmed=(r"\binvestigate every non-zero variance\b",))
        self.assert_sentence(
            gotchas, r"\bwhere the GST account balance is cleared out as part of lodgement\b",
            r"\bprevious-period variance (can|may) be ignored\b|\b(lets|allows) the previous-period variance (to )?be ignored\b",
            affirmed=(r"\brecord evidence of that clearing before setting one aside\b",),
        )
        self.assert_sentence(
            gotchas, r"\bdates\b", r"\bbasis\b", r"\bdecimals\b", affirmed=(r"\brecord them per report\b",)
        )
        self.assert_sentence(gotchas, r"\bexport format\b", NOT + r"observed\b")

        _, gotchas = table_row(skill, heading, "Fixed Asset Reconciliation / Depreciation Schedule / Disposal Schedule")
        self.assert_sentence(
            gotchas, r"`Depreciation Schedule` shows book depreciation only\b",
            affirmed=(r"\bfor tax values take the `Tax Depreciation Schedule`",),
        )

        satisfies, gotchas = table_row(skill, heading, "Tax Depreciation Schedule / Tax Disposal Schedule")
        self.assert_carries(satisfies, "`au-depreciation-schedule`")
        self.assert_sentence(
            gotchas, r"\bregistered assets only, excluding pooled assets\b",
            r"\bpooled assets' tax depreciation is in the `Pool Summary` report\b",
            r"\btheir tax disposals are in the `Fixed Asset Reconciliation`",
        )
        self.assert_sentence(
            gotchas, r"\bonly fixed assets and changes from the tax reporting start date\b",
            r"\ban earlier start can give wrong figures\b",
            affirmed=(r"\brun them from that date or later\b",),
        )
        self.assert_sentence(gotchas, r"`Tax Depreciation Schedule`", NOT + r"show pool depreciation\b")
        self.assert_sentence(gotchas, r"\bexport format\b", NOT + r"observed\b")

        notice = section(skill, heading)
        self.assert_sentence(
            notice, r"\bHuman review pending\b", r"\b4 November 2026\b", r"\bnot a human review\b", r"\bno update date\b"
        )
        self.assert_sentence(notice, NOT + r"from an inspected export or menu\b")
        self.assert_sentence(notice, affirmed=(r"\bconfirm each report name, menu label and setting\b",))
        # The API and parsing sections cover the new reports and scope the .xls note to the older one.
        api = section(skill, "What the API can and cannot fetch")
        self.assert_sentence(
            api, r"\bboth GST reconciliation reports\b", r"\bthe 2 tax schedules\b", r"\bhas no report endpoint\b"
        )
        self.assert_sentence(
            api, r"\b4 November 2026\b", r"\bno endpoint for the GST reconciliation pack or either tax schedule\b"
        )
        self.assert_carries(section(skill, "Parsing conventions"), "GST Reconciliation (the older report)")
        self.assert_carries(section(skill, "Boundaries"), "sources.json", "discovery-only", "plain HTTP")
        self.assert_cited_and_recorded(
            skill,
            "https://central.xero.com/0/article/GST-Reconciliation-new",
            "https://central.xero.com/0/article/The-GST-Audit-Report-AU",
            "https://central.xero.com/0/article/Depreciation-Schedule-new-AU",
            "https://central.xero.com/0/article/Tax-Depreciation-Schedule",
            "https://central.xero.com/0/article/Tax-Disposal-Schedule",
        )
        self.assertFalse((SKILLS / skill / "sources.exempt.json").exists())

    def test_business_formation_keeps_cp_391_a_dated_proposal(self) -> None:
        skill = "au-business-formation"
        step = workflow_step(skill, 3)
        self.assert_sentence(step, r"\bProposal, not law\b", r"\b5 November 2026\b", r"\bproposes\b")
        self.assert_sentence(step, r"\b1 July 2027\b", r"\b1 August 2028\b", r"\bonly if no service address\b")
        self.assert_sentence(step, r"\bMarch 2027\b", r"\bnot necessarily its final position\b")
        self.assert_sentence(step, affirmed=(r"\bRead the current status at ASIC\b",))
        self.assert_sentence(step, r"`sources\.json`", r"\bawaits human review\b")
        self.assert_sentence(step, r"\bkeep it out of the registration requirements\b")
        self.assert_sentence(step, NOT + r"tell anyone that an address will be published\b", r"\bmust be lodged\b")
        self.assert_cited_and_recorded(
            skill,
            "https://www.asic.gov.au/regulatory-resources/find-a-document/consultations/"
            "cp-391-access-to-information-on-the-companies-register",
        )

    def test_tax_research_keeps_the_as_at_check_a_locator(self) -> None:
        step = workflow_step("au-tax-research", 2)
        self.assert_carries(step, "python -m fadden as_at", "PaulGoodman")
        for status in ("captured", "before_compilation", "superseded", "after_retrieval"):
            self.assert_carries(step, f"`{status}`")
        self.assert_sentence(step, r"`captured` is not a finding that the text was the law\b")
        self.assert_sentence(step, r"\bendnotes\b", r"\bversion history\b", affirmed=(r"\bRead the compilation\b",))
        self.assert_sentence(step, r"\bWithout the tool\b", r"\bunchanged\b")

    def test_xero_connector_route_refuses_writes_and_records_each_read(self) -> None:
        route = section("xero-exports", "Read-only connector route")
        self.assert_sentence(route, r"\bfile-export path stays the default\b")
        self.assert_sentence(route, r"\bwhether client data may reach a connector\b", r"\bask before using one\b")
        self.assert_sentence(route, r"\bconnector in Claude\b", r"\bread-only\b")
        self.assert_sentence(route, r"\bRemote MCP\b", r"\bopen source server\b", r"\bdifferent\b")
        self.assert_sentence(route, r"\btools that write\b")
        self.assert_sentence(route, r"\b5 November 2026\b", r"\bnot indexed\b")
        self.assert_sentence(route, r"\bNo authenticated request was tested\b")
        self.assert_sentence(route, r"\bcannot be completed\b", affirmed=(r"\bcall nothing\b",))
        self.assert_sentence(route, r"\bmust end in `\.read`", r"\breject a connection\b")
        self.assert_sentence(route, r"\bEvery tool the connection exposes must be on the allowlist\b")
        self.assert_sentence(route, r"\bother servers\b", r"\bout of this check\b")
        self.assert_sentence(
            route, r"\bdoes not show which tools belong to this connection\b", r"\bnot completed\b", r"\bstop\b"
        )
        self.assert_sentence(route, r"\bStop on any other name\b", r"\beven when the scopes pass\b")
        self.assert_sentence(route, r"\bvendor page\b", r"\bdoes not confirm either check\b")
        allowlist = route.partition("Allowlist, from")[2].partition("The open source server")[0]
        tools = re.findall(r"`(\w+)`", allowlist)
        self.assertEqual(18, len(set(tools)), tools)
        self.assertEqual(["get_connected_tenants"], [tool for tool in tools if not tool.startswith("list_")])
        card = (SKILLS.parents[1] / "validation" / "cases" / "xero-exports-connector-read-and-write-request.md")
        self.assert_carries(
            card.read_text(encoding="utf-8"),
            "Stop before calling any tool on this connection",
            "including `list_trial_balance`",
        )
        self.assert_carries(
            route, "organisation", "period or as-at date", "cash or accrual basis", "capture date and time"
        )
        self.assert_sentence(route, r"\bdo not merge reads\b")
        self.assert_sentence(route, r"\bcannot stand in for a UI-only report\b", r"\breconstruction\b")
        self.assert_sentence(
            route, r"\bNever call a tool outside the allowlist\b", r"`create_`", r"`update_`", r"`authorise_`", r"`void_`"
        )
        self.assert_sentence(route, r"\bunposted draft\b")
        bas = " ".join(skill_text("bas-preparation").split())
        self.assert_sentence(bas, r"\bread-only connector route\b", r"\bcapture time\b", r"\brefuses every write\b")
        self.assert_sentence(bas, r"\bActivity Statement's transaction tabs\b", r"\bstill come from exports\b")

    def test_xero_connector_route_allows_the_read_only_fork_at_its_commit(self) -> None:
        """The fork's 31 read-only tools pass the tool-list check, pinned to a commit and a setting."""
        route = section("xero-exports", "Read-only connector route")
        allowlist, _, row = route.partition("Allowlist, from")[2].partition("Fork row,")
        self.assertTrue(row, "the route has no fork row")
        row = row.partition("For every connector read")[0]
        sha = "a115f181895d82d0f9e0604546ef00671e9c47a6"
        self.assert_sentence(row, r"\bryanduguid/xero-mcp-server\b", rf"`{sha}`", r"\b10 November 2026\b")
        self.assert_carries(row, f"/tree/{sha})")
        self.assert_sentence(row, r"\bAt that commit and setting\b", r"\b31 tools\b", r"\bon that server only\b")
        self.assert_sentence(row, r"\bcalls only Xero read methods\b", r"\bno server was run\b")
        self.assert_sentence(row, r"\bonly after verifying\b", r"\bthat exact commit\b", r"`XERO_READ_ONLY=true`")
        self.assert_sentence(
            row,
            r"\bin this session\b",
            r"\bcheckout its launch command runs\b",
            r"\bno local change\b",
            r"\blaunch configuration sets the variable\b",
        )
        self.assert_sentence(row, r"\bperson's assurance verifies neither\b")
        self.assert_sentence(
            row,
            r"\bIf either is unverified\b",
            r"\bfork row does not apply\b",
            r"\bbase allowlist alone\b",
            r"\bstops on any other name\b",
            r"\bfile exports\b",
        )
        self.assert_sentence(row, r"\bOn the verified server\b", r"\btool-list check stops\b", r"\boutside these 31\b")
        self.assert_sentence(row, r"\bleaves the scopes\b[^.]*\bunchanged\b", r"\bscopes check still decides\b")
        self.assert_sentence(
            row,
            r"\bfirst organisation Xero lists\b",
            r"\blooking it up again during a session\b",
            r"`list-organisation-details`",
            r"\bbefore each export\b",
            r"\bstop if it is not the organisation the engagement names\b",
        )
        # The names the fork registers with XERO_READ_ONLY=true at a115f18:
        # src/tools/get/index.ts and src/tools/list/index.ts, 2 and 29.
        registered = {
            "get-contact", "get-timesheet", "list-accounts", "list-aged-payables-by-contact",
            "list-aged-receivables-by-contact", "list-bank-transactions", "list-bank-transfers",
            "list-contact-groups", "list-contacts", "list-credit-notes", "list-currencies", "list-invoices",
            "list-items", "list-manual-journals", "list-organisation-details", "list-overpayments",
            "list-payments", "list-payroll-employee-leave", "list-payroll-employee-leave-balances",
            "list-payroll-employee-leave-types", "list-payroll-employees", "list-payroll-leave-periods",
            "list-payroll-leave-types", "list-prepayments", "list-profit-and-loss", "list-quotes",
            "list-report-balance-sheet", "list-tax-rates", "list-timesheets", "list-tracking-categories",
            "list-trial-balance",
        }
        self.assertEqual(31, len(registered))
        hyphenated = {tool.replace("_", "-") for tool in re.findall(r"`(list_\w+)`", allowlist)}
        named = re.findall(r"`((?:get|list)-[a-z-]+)`", row.partition("these 14")[2].partition("Each of the 31")[0])
        self.assertEqual(14, len(named), named)
        self.assertEqual(14, len(set(named)), named)
        self.assertFalse(set(named) & hyphenated, "a row name repeats the allowlist")
        self.assertEqual(registered, set(named) | hyphenated)

    def assert_export_is_no_exemption(self, text: str) -> None:
        self.assert_sentence(
            text,
            r"\bfile export is not an exemption\b",
            r"\bexternal AI provider\b",
            r"\bassess that disclosure\b",
            r"\bapproved local process\b",
        )

    def test_a_ledger_connection_needs_the_read_only_route_and_client_permission(self) -> None:
        route = section("xero-exports", "Read-only connector route")
        self.assert_sentence(route, r"\bregistered tax or BAS agent\b", r"\bthis client's permission\b")
        self.assert_sentence(route, r"\bTPB\(GS\) 55/2026\b", r"\bdepending on how the tool is configured and used\b", r"\(paragraph 23\)")
        self.assert_sentence(route, r"\bfact find and consent\b", r"\bgeneral authority\b", r"\(paragraph 24\)")
        self.assert_sentence(route, r"\bno record is supplied\b", r"\bstop\b", r"\bfile-export path\b")
        self.assert_sentence(route, r"\bresponsible practitioner\b")
        self.assert_export_is_no_exemption(route)
        gs55 = "https://www.tpb.gov.au/tpbgs-552026-use-artificial-intelligence-and-code-professional-conduct"
        self.assert_cited_and_recorded("xero-exports", gs55)

        step = workflow_step("au-bookkeeping", 1)
        self.assert_sentence(step, r"\bFor Xero\b", r"\bread-only connector route in `xero-exports`", r"\brefuses every write\b")
        self.assert_sentence(step, r"\bread-only connector route\b", r"\bclient's permission\b")
        self.assert_sentence(step, r"\bany ledger connector\b", r"\brecord of this client's permission\b", r"\(paragraph 23\)")
        self.assert_sentence(step, r"\bno record is supplied\b", r"\bstop\b", r"\bidentified export\b")
        self.assert_export_is_no_exemption(step)
        self.assert_cited_and_recorded("au-bookkeeping", gs55)

        bas = " ".join(skill_text("bas-preparation").split())
        self.assert_sentence(bas, r"\bBefore any connector read\b", r"\brecord of this client's permission\b", r"\(paragraph 23\)")
        self.assert_sentence(bas, r"\bno record is supplied\b", r"\bcall nothing on that connection\b", r"\buse exports\b", affirmed=(r"\bstop\b",))
        self.assert_export_is_no_exemption(bas)
        self.assert_cited_and_recorded("bas-preparation", gs55)

        integrations = " ".join((SKILLS.parents[1] / "docs" / "integrations.md").read_text(encoding="utf-8").split())
        self.assertIn("## Xero reads", integrations)
        self.assertIn("xero-exports/SKILL.md#read-only-connector-route", integrations)
        self.assertIn("Developer Remote MCP", integrations)
        self.assertIn("It refuses every write.", integrations)
        self.assertIn("A registered tax or BAS agent also needs a record of the client's permission first", integrations)
        self.assertIn("These skills give no guidance for writing to Xero.", integrations)

        readme = " ".join((SKILLS.parents[1] / "README.md").read_text(encoding="utf-8").split())
        self.assertIn("## Privacy", readme)
        self.assertIn("[Privacy](#privacy)", readme)
        self.assertIn(f"[TPB(GS) 55/2026]({gs55})", readme)
        self.assertIn("unless there is a legal duty", readme)
        self.assertIn("depending on how the tool is configured and used", readme)
        self.assertIn("**Human review pending:**", readme.split("## Privacy")[1].split("## Alternatives")[0])

    def test_readme_keeps_the_automated_decision_duty_conditional(self) -> None:
        readme = " ".join((SKILLS.parents[1] / "README.md").read_text(encoding="utf-8").split())
        privacy = readme.split("## Privacy")[1].split("## Alternatives")[0]
        self.assert_sentence(
            privacy,
            r"^\W*From 10 December 2026\b",
            r"\bAPP\) 1\.7\b",
            r"\bbut only if\b.*\bcomputer program\b",
            r"\bsignificantly affect an individual's rights or interests\b",
            r"\bpersonal information about that individual is used\b",
            r"\]\(https://www\.legislation\.gov\.au/C2024A00128/",
        )
        self.assert_sentence(privacy, r"\bdecisions made after that date\b", r"\bwhenever the program was arranged\b")
        self.assert_sentence(privacy, r"\bhuman reviewing the output\b", r"\bnot by itself\b", r"\]\(https://www\.oaic\.gov\.au/")
        self.assert_sentence(privacy, r"\bAPP entity\b", r"\bfor the firm to decide\b")
        self.assertLess(readme.index("## Privacy"), readme.index("## Alternatives"))
        self.assertEqual(readme.count("Anthropic's `small-business` plugin"), 0)
        self.assertEqual(readme.count("The `small-business` plugin declares"), 1)

    def test_readme_documents_the_host_caveat_and_the_audited_mcp_pin(self) -> None:
        """Documentation consistency only: this does not test the server's network behaviour."""
        root = SKILLS.parents[1]
        readme = " ".join((root / "README.md").read_text(encoding="utf-8").split())
        privacy = readme.split("## Privacy")[1].split("## Alternatives")[0]
        self.assert_sentence(privacy, r"\*\*Your agent host\*\* decides where\b")
        self.assert_sentence(privacy, r"\bcloud model\b", r"\bnormally reach\b", r"\bcheck your host's configuration\b")
        audited = "f17bbb2f920e3c11dac9810060a533c64e0e3be8"  # aus-accounting-mcp v0.6.0
        plugin = json.loads((root / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
        self.assertIn(f"@{audited}#", plugin["mcpServers"]["aus-accounting"]["args"][1])
        self.assert_sentence(
            privacy,
            r"`aus-accounting-mcp` 0\.6\.0",
            rf"/commit/{audited}\)",
            r"\bimport no network library apart from `asyncio`",
            r"\b0 socket and 0 connect calls\b",
            r"\b12 calculation tools\b",
        )
        self.assert_sentence(privacy, r"\b8 corpus tools\b", r"\bnot traced\b")
        self.assert_sentence(privacy, r"\btrace's method and output\b", r"\bnot published\b")
        self.assert_sentence(privacy, r"\bMCP SDK\b", r"\bnot pinned\b", r"\bdid not cover it\b")

    def test_skill_folders_hold_no_runtime_scripts(self) -> None:
        readme = " ".join((SKILLS.parents[1] / "README.md").read_text(encoding="utf-8").split())
        self.assertIn("The skill folders hold Markdown and JSON files and no scripts", readme)
        suffixes = {path.suffix for path in SKILLS.rglob("*") if path.is_file()}
        self.assertLessEqual(suffixes, {".md", ".json"})

    def test_readme_names_every_local_program_a_skill_names(self) -> None:
        """A firm reads the Privacy section to decide what can leave the machine, so a
        program a skill points the agent to must appear there. Programs are found from
        the skills' links to the author's tool repositories; a link this test cannot
        classify fails it until the README and the maps below name it."""
        texts = [path.read_text(encoding="utf-8") for path in sorted(SKILLS.rglob("*.md"))]
        found = set()
        for link in sorted({m for text in texts for m in AUTHOR_LINK.findall(text)}):
            programs = {name for part, name in LINKED_PROGRAMS.items() if part in link}
            with self.subTest(link=link):
                self.assertTrue(
                    programs or any(re.search(pattern, link) for pattern in NOT_PROGRAM_LINKS),
                    "name this program in the README's Privacy section and in LINKED_PROGRAMS",
                )
            found |= programs
        self.assertEqual(found, set(LINKED_PROGRAMS.values()), "a mapped program is no longer linked")
        for program in UNLINKED_PROGRAMS:
            with self.subTest(program=program):
                self.assertTrue(any(f"`{program}" in text for text in texts), "no skill names it any more")
        readme = (SKILLS.parents[1] / "README.md").read_text(encoding="utf-8")
        heading = "- **A local program a skill names**"
        bullet = next((line for line in readme.splitlines() if line.startswith(heading)), "")
        for program in sorted(found | set(UNLINKED_PROGRAMS)):
            with self.subTest(program=program):
                self.assertIn(f"`{program}`", bullet)

    def test_tracker_reports_are_intake_tied_to_source_records(self) -> None:
        cgt = " ".join(raw_section("au-capital-gains", "Inputs").split())
        self.assertIn("Sharesight or Navexa", cgt)
        self.assert_sentence(cgt, r"\breport name\b", r"\bcost base and parcel-matching settings\b")
        step = workflow_step("au-capital-gains", 1)
        self.assert_sentence(step, r"\bTie its disposals, proceeds and parcels to the broker or registry records\b")
        self.assert_sentence(step, r"\bgain, discount or tax figure\b", r"\bnot evidence of the treatment\b")

        crypto = " ".join(raw_section("au-crypto-tax", "Inputs").split())
        self.assertIn("such as one from Koinly", crypto)
        self.assert_sentence(crypto, r"\bwallets and exchanges imported\b", r"\bcost-basis settings\b")
        step = workflow_step("au-crypto-tax", 1)
        self.assert_sentence(step, r"\bTie its wallets, transactions and units to the exports\b")
        self.assert_sentence(step, r"\bclassifications and gain figures\b", r"\bnot evidence of the treatment\b")

    def test_year_end_client_request_list_is_drafted_and_not_sent(self) -> None:
        text = " ".join(skill_text("year-end-workpapers").split())
        carry_forwards = text.index("6. **Carry-forwards and completeness.**")
        start = text.index("7. **Client request list.**", carry_forwards)
        step = text[start : text.index("## Checks before handing over", start)]
        self.assertIn("including any step 6 found", step)
        self.assertIn("one page the reviewer can send", step)
        self.assertIn("Leave out workpaper references, tax positions and advice", step)
        self.assertIn("An authorised human reviews and sends it", step)
        self.assertIn("appears once on the client request list, drafted and not sent", text)

    def test_transfer_duty_cards_cover_each_jurisdiction_without_a_rate(self) -> None:
        cases = SKILLS.parents[1] / "validation" / "cases"
        offices = {
            "nsw-business-with-land": "Revenue NSW",
            "vic-goods-under-separate-contract": "State Revenue Office Victoria",
            "qld-business-assets-and-debts": "Queensland Revenue Office",
            "wa-rent-roll-and-trade-debts": "RevenueWA",
            "sa-fixed-items-and-old-rule": "RevenueSA",
            "tas-new-lease-condition": "State Revenue Office Tasmania",
            "act-goods-with-crown-lease": "ACT Revenue Office",
            "nt-option-before-9-may-2023": "Territory Revenue Office",
        }
        for name, office in offices.items():
            card = (cases / f"au-transfer-duty-{name}.md").read_text(encoding="utf-8")
            with self.subTest(card=name):
                self.assertIn(office, card)
                self.assertNotRegex(card, r"\d\s?(?:%|per cent)")
                self.assertIn("Do not state a rate, threshold or concession from memory.", card)
                self.assertIn("uncalculated unless a period-specific rule is verified", card)


if __name__ == "__main__":
    unittest.main()
