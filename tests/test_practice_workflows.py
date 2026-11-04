# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""The 4 practice workflows added on 4 November 2026 keep their key rules.

Each test reads one numbered workflow step and checks the authorities,
conditions, cut-offs and prohibitions it must carry, not its wording, in the
style of test_dated_rule_changes.py. A prohibition or negative predicate is
checked within one sentence with its negator before its verb, and each action
of a prohibited list is checked on its own as an item of that list; an
exception or cut-off is matched inside its own clause; each term of a list the
step must carry in full is required on its own. The helpers repeat that module's so each
file stands alone under unittest discovery.
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
# A negator directly before the matched verb, allowing only auxiliaries, 'to',
# articles and a set-off 'however' between, as in test_dated_rule_changes.py.
NEGATED = r"(?:\b(?:not|never|cannot|no(?!\.))|n't)(?:\W+(?:be|been|to|a|an|the|however|also))*\W+$"
# A required prohibition keeps its negator directly before its verb.
DO_NOT = r"\b(?:do not|don't|never|must not)\W+"
# The text before an item of a prohibited list: the negator, then only earlier items of
# that list, each closed by a comma, 'or' or ', or'.
IN_PROHIBITED_LIST = DO_NOT + r"(?:[^,.;:]+?(?:,(?:\s+or)?|\s+or)\s+)*$"
ATO_AGENTS = "https://www.ato.gov.au/tax-and-super-professionals/digital-services/online-services-for-agents"
TRUST_LOSS = (
    "https://www.ato.gov.au/businesses-and-organisations/trusts/"
    "trust-income-losses-and-capital-gains/trust-loss-provisions"
)


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
    """Sentences of normalised text; paragraph numbers such as 'R320.7' do not end one."""
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


class PracticeWorkflowTests(unittest.TestCase):
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

    def assert_prohibited(self, text: str, *actions: str) -> None:
        """Each action is named in `text`, and every mention of it is an item of a list
        that a prohibition governs, so 'do not post, pay or lodge' forbids all 3, whilst
        'do not post or lodge; pay' or a later 'pay the debt' permits paying."""
        for action in actions:
            with self.subTest(prohibited=action):
                mentions = [sentence[: match.start()] for sentence in sentences(text)
                            for match in re.finditer(action, sentence, re.IGNORECASE)]
                self.assertTrue(mentions, f"{action!r} is not named")
                for before in mentions:
                    self.assertTrue(re.search(IN_PROHIBITED_LIST, before, re.IGNORECASE),
                                    f"{action!r} is not inside a prohibited list after {before!r}")

    def assert_routes(self, text: str, count: int) -> None:
        """`text` routes to at least `count` distinct skills, each of which exists. The
        names are not quoted here, so the coverage matrix credits this file only to the
        4 skills it tests."""
        names = set(re.findall(r"`([a-z0-9]+(?:-[a-z0-9]+)+)`", text))
        self.assertGreaterEqual(len(names), count)
        for name in sorted(names):
            with self.subTest(route=name):
                self.assertTrue((SKILLS / name / "SKILL.md").is_file())

    def assert_cited_and_recorded(self, skill: str, *urls: str) -> None:
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

    # au-client-departure

    def test_client_departure_classifies_records_by_owner_without_deciding(self) -> None:
        step = workflow_step("au-client-departure", 2)
        self.assert_carries(step, "source documents", "working papers", "final accounts", "tax returns",
                            "advice letters", "ATO correspondence", "cloud ledger file", "TPB(GS) 07/2011")
        self.assert_sentence(step, r"\bterms are silent\b", r"\bagent\b", r"\bprincipal\b",
                             affirmed=(r"\brecord the engagement type\b",))
        # Each general rule keeps its own owner.
        self.assert_sentence(
            step, r"\bN1\b",
            r"\bcreated on the client's instructions belong to the client\b",
            r"\bsolely for the member's own purposes belong to the member\b",
            r"\bmember guidance\b[^.;]*\bnot law\b",
        )
        self.assert_sentence(step, r"\bUNVERIFIED\b", affirmed=(r"\bproposed classification for review\b",))

    def test_client_departure_records_cloud_files_and_leaves_access_unchanged(self) -> None:
        step = workflow_step("au-client-departure", 3)
        self.assert_carries(step, "cloud account owner", "subscriber", "every user", "subscription")
        self.assert_sentence(
            step, r"\bmust be returned when the engagement ceases\b", r"\bno obligation to prepare reports\b",
            r"\bmay export\b",
        )
        self.assert_prohibited(step, r"\bremove a user\b", r"\bchange a subscription\b",
                               r"\btransfer the account\b")

    def test_client_departure_reply_discloses_only_what_is_permitted(self) -> None:
        step = workflow_step("au-client-departure", 4)
        self.assert_carries(step, "R320.7", "320.7 A1", "AUST 320.2.1", "R320.8(b)", "Code item 6",
                            "s 30-10(6)", "R114.4", "AUST 114.3 A1.1")
        # R320.7 has 2 limbs; both are required ('and', not 'or').
        self.assert_sentence(
            step, r"\bR320\.7\b",
            r"\bcomply with\b[^;]*\bgoverning the request\b,? and (to )?(give|provide)\b[^;]*\bhonestly and unambiguously\b",
        )
        # The exception belongs to the bar on disclosure.
        self.assert_sentence(
            step, r"\bCode item 6\b",
            r"\bbars disclos\w*\b[^;]*\bwithout the client's permission unless there is a legal duty\b",
            r"\bformer clients\b",
        )
        self.assert_sentence(step, r"\bincluding only what the client has permitted\b",
                             r"\bwhere no permission is held\b[^.;]*\bdiscloses no client information\b",
                             affirmed=(r"\bdraft the reply\b",))
        self.assert_sentence(step, DO_NOT + r"send the reply\b")

    def test_client_departure_lists_lien_questions_with_their_limits(self) -> None:
        step = workflow_step("au-client-departure", 5)
        self.assert_sentence(step, r"\bunpaid\b", affirmed=(r"\blist each proposal as a lien question\b",))
        self.assert_sentence(step, r"\bnot entitled to a general lien\b",
                             affirmed=(r"\bparticular lien needs every circumstance\b",))
        # Each limit keeps its negator in its own clause.
        self.assert_sentence(
            step, r"\blien cannot be exercised over\b[^.;]*\bsection 286\b",
            r"\b(should not|must not|never|do not)\W+deny a client access\b[^.;]*\bledger\b",
        )
        self.assert_sentence(step, r"\bexpended no labour\b", r"\bgenerally cannot be the subject of a lien\b",
                             affirmed=(r"\bencourages legal advice\b",))
        self.assert_sentence(
            step, r"\bparagraph 3\.9\b", r"\bsubject to any legal right of lien\b",
            affirmed=(r"\brequires records belonging to the client to be made available for collection promptly\b",),
        )
        self.assert_sentence(step, r"\bwhether a lien applies\b",
                             affirmed=(r"\bdecisions for the authorised practitioner\b",))

    def test_client_departure_keeps_section_30_records_and_deletes_nothing(self) -> None:
        step = workflow_step("au-client-departure", 6)
        self.assert_carries(step, "Section 30", "including former clients", "Human review pending",
                            "4 November 2026", "F2026C00953", "at least 5 years", "AML/CTF records")
        self.assert_routes(step, 1)
        self.assert_sentence(step, r"\bfor the period it states\b", affirmed=(r"\bkept and retained\b",))
        self.assert_sentence(step, DO_NOT + r"delete any record\b")

    def test_client_departure_lists_ato_client_list_steps_without_making_them(self) -> None:
        step = workflow_step("au-client-departure", 7)
        # The ordering condition stays with its own action.
        self.assert_sentence(
            step, r"\bmust remove your contact details from the client's record before removing the client\b",
            r"\bAustralian Business Register\b", r"\bfinal return does not remove a client\b",
        )
        self.assert_sentence(step, r"\bPractice preference\b", r"\baddress for service\b",
                             r"\bexpress written authority\b")
        self.assert_sentence(step, DO_NOT + r"change ATO or Australian Business Register records\b")

    def test_client_departure_sources_are_pending(self) -> None:
        self.assertIn("](https://www.charteredaccountantsanz.com/", skill_text("au-client-departure"))
        self.assert_cited_and_recorded(
            "au-client-departure",
            "https://apesb.org.au/standards-guidance/apes-110-code-of-ethics/",
            "https://www.legislation.gov.au/C2009A00013/latest/text",
            "https://www.legislation.gov.au/F2024L00849/latest/text",
            "https://www.tpb.gov.au/confidentiality-client-information",
            "https://www.tpb.gov.au/tpb-gs-07-2011-claiming-lien-over-client-property",
            "https://www.tpb.gov.au/tpb-gs-52-2024-obligation-keep-proper-client-records-tax-agent-services-provided",
            f"{ATO_AGENTS}/client-list",
            f"{ATO_AGENTS}/client-communication",
        )

    # au-trust-losses

    def test_trust_losses_keep_capital_losses_out(self) -> None:
        step = workflow_step("au-trust-losses", 1)
        self.assert_sentence(step, r"(?:\bnot|n't)\W+apply to capital losses\b",
                             affirmed=(r"\bkeep capital losses out\b",))

    def test_trust_losses_classify_the_trust_for_the_test_period(self) -> None:
        step = workflow_step("au-trust-losses", 2)
        self.assert_carries(step, "s 267-20(1)", "s 272-70", "s 272-100", "s 272-75", "Division 266")
        self.assert_sentence(
            step, r"\btest period\b[^.]*\bbeginning of the loss year\b[^.]*\b(until|to) the end of the income year\b"
        )
        # 'any time' belongs to the non-fixed test and 'all times' to the exception.
        self.assert_sentence(step, r"\bnon-fixed trust\b[^.;,]{0,20}\bat any time\b",
                             r"\bexcepted trust\b[^.;,]{0,20}\bat all times\b")
        self.assert_sentence(step, r"\bfamily trust is an excepted trust only (whilst|while) its election is in force\b")
        self.assert_sentence(step, r"\bafter the beginning of the loss year\b",
                             r"\bdoes not cover the whole test period\b")

    def test_trust_losses_evidence_each_non_fixed_trust_test(self) -> None:
        step = workflow_step("au-trust-losses", 3)
        self.assert_carries(step, "s 267-20(2)", "s 267-30", "Subdivision 269-D", "s 269-65", "s 269-70",
                            "s 269-60", "s 269-75", "s 269-80", "s 269-85", "s 267-35", "s 267-40",
                            "Subdivision 269-C", "s 267-40(3)", "s 267-45", "Subdivision 269-E", "s 269-95",
                            "Subdivision 267-C", "s 267-50", "pattern of distributions test", "50% stake test",
                            "control test")
        self.assert_sentence(step, r"\bcannot deduct the loss unless it meets each condition\b")
        # Both distribution windows are needed before the test applies ('and', not 'or').
        self.assert_sentence(
            step, r"\bapplies only if\b",
            r"\bin the income year or within 2 months after its end and in at least one of the 6 earlier income years\b",
        )
        self.assert_sentence(step, r"\bwithin 2 months after the end of the income year\b", r"\bsame individuals\b",
                             r"\bfor their own benefit\b", r"\bgreater than 50% share of each\b")
        self.assert_sentence(step, r"\bincome and for capital may differ\b")
        self.assert_sentence(step, r"\bat any time in the test period\b", r"\bmore than a 50% stake\b")
        self.assert_sentence(step, r"\bsame individuals kept more than that stake until the end of the test period\b")
        self.assert_sentence(step, r"\bs 267-40\(3\)", DO_NOT + r"assume it is exercised\b",
                             affirmed=(r"\bis for the reviewer\b",))
        self.assert_carries(step, "trustees", "appointor or guardian",
                            "shareholders or directors of a corporate trustee", "new beneficiaries",
                            "deed amendments", "unit holdings", "other unusual changes")
        self.assert_sentence(step, r"\bbegan to control\b", r"\bquestion of fact for the reviewer\b")
        self.assert_sentence(step, r"\bpattern of distributions test does not apply for current year loss purposes\b")
        self.assert_sentence(step, r"\bfails only the 50% stake test or the control test\b", r"\bs 267-50\b",
                             affirmed=(r"\bleave the amount for review\b",))

    def test_trust_losses_screen_for_income_injection_unless_excluded(self) -> None:
        step = workflow_step("au-trust-losses", 4)
        # Division 270 reaches fixed and non-fixed trusts with a deduction; s 270-10(1)(d)
        # excludes only the excepted trusts in s 272-100(b), (c) and (d), each named.
        self.assert_sentence(
            step, r"\bfixed or non-fixed\b", r"\bdeduction is allowable for the income year \(s 270-10\(1\)\(a\)\)",
            r"\bexcept an excepted trust under s 272-100\(b\), \(c\) or \(d\) \(s 270-10\(1\)\(d\)\)",
            affirmed=(r"\bDivision 270 applies to any trust\b",),
        )
        self.assert_carries(step, "complying superannuation fund", "complying approved deposit fund",
                            "pooled superannuation trust", "5th anniversary of the death",
                            "exempt entities have fixed entitlements")
        # The other excepted trusts stay inside it.
        self.assert_sentence(
            step, r"\bfamily trust \(s 272-100\(a\)\)",
            r"\bdesignated infrastructure project entity \(s 272-100\(f\)\)",
            affirmed=(r"\bstill applies to the other 2 kinds of excepted trust\b",),
        )
        # The 3 limbs of the scheme are cumulative.
        self.assert_sentence(
            step,
            r"\bderived assessable income\b[^.]*\boutsider\b[^.]*\bprovided a benefit\b[^.]*,? and the trustee, a beneficiary or an associate provided a benefit to the outsider\b",
        )
        self.assert_sentence(step, r"\bs 270-25\(1\)", affirmed=(r"\bnarrows who is an outsider\b",))
        self.assert_sentence(step, r"\bwholly or partly, but not merely incidentally\b",
                             affirmed=(r"\bis for the reviewer\b",))

    def test_trust_losses_record_election_evidence_without_recommending(self) -> None:
        step = workflow_step("au-trust-losses", 5)
        self.assert_carries(step, "specified individual", "specified income year", "s 272-80(4)",
                            "s 272-80(4A)", "interposed entity election", "only one individual can be specified",
                            "family trust distribution tax", "Human review pending", "C2026C00454",
                            "4 November 2026")
        self.assert_routes(step, 2)
        # The later start is an exception to the general start, in its own clause.
        self.assert_sentence(
            step, r"\bgenerally in force from the beginning of the specified income year\b",
            r"\bor from a later time if the family control test is not passed for the whole year\b",
        )
        self.assert_prohibited(step, r"\bmake, vary or revoke an election\b", r"\brecommend doing so\b")
        self.assert_sentence(step, affirmed=(r"\btrustee decides\b",))

    def test_trust_losses_end_at_the_reviewers_decision(self) -> None:
        step = workflow_step("au-trust-losses", 6)
        self.assert_sentence(step, affirmed=(r"\bleave the deduction amount blank\b",))
        self.assert_sentence(step, r"\bin full or in part\b", affirmed=(r"\bis the reviewer's decision\b",))

    def test_trust_losses_sources_are_pending(self) -> None:
        self.assert_cited_and_recorded(
            "au-trust-losses",
            "https://www.legislation.gov.au/C1936A00027/latest/text",
            f"{TRUST_LOSS}/about-trust-loss-provisions",
            f"{TRUST_LOSS}/which-tests-to-apply",
            f"{TRUST_LOSS}/how-to-apply-the-trust-loss-tests",
            "https://www.ato.gov.au/businesses-and-organisations/trusts/family-trusts",
        )

    # au-ato-correspondence-triage

    def test_triage_screens_for_scams_without_treating_absence_as_one(self) -> None:
        step = workflow_step("au-ato-correspondence-triage", 2)
        self.assert_sentence(
            step, r"\bnever sends unsolicited messages containing hyperlinks or QR codes\b",
            r"\bnever asks for a TFN, bank details or a myGov login by email or SMS\b",
            r"\bending in 'ato\.gov\.au'",
        )
        self.assert_sentence(step, r"UNVERIFIED: possible scam", DO_NOT + r"open its links\b",
                             affirmed=(r"\broute it to the practitioner\b",))
        self.assert_prohibited(step, r"\bopen its links\b", r"\bcall a number it gives\b")
        self.assert_sentence(step, r"\bAbsence from Communication history alone is not a scam sign\b",
                             r"\bsent only by post\b", r"\bnot viewable there\b")
        self.assert_sentence(step, r"\bunmatched paper letter `?UNVERIFIED")

    def test_triage_keeps_unknown_notice_types_unverified(self) -> None:
        step = workflow_step("au-ato-correspondence-triage", 3)
        self.assert_sentence(step, r"\bexactly as printed\b", affirmed=(r"\bmap it to a communication\b",))
        self.assert_sentence(step, r"\bmatches no listed communication\b", r"\bmark the type `?UNVERIFIED",
                             DO_NOT + r"infer a type from the layout\b")

    def test_triage_matches_clients_on_identifier_and_name(self) -> None:
        step = workflow_step("au-ato-correspondence-triage", 4)
        self.assert_sentence(step, r"\bidentifier and name together\b")
        self.assert_sentence(step, r"\bmatch on both as matched\b", r"\bmatch on only one as `?UNVERIFIED",
                             r"\bno match as unmatched\b", DO_NOT + r"assign an item to the nearest name\b")
        self.assert_sentence(step, r"\bPractice\b", r"\baddress for service\b",
                             r"\bresponsible for informing the client\b")

    def test_triage_records_only_stated_dates(self) -> None:
        step = workflow_step("au-ato-correspondence-triage", 5)
        self.assert_sentence(step, r"\bexactly as printed\b", affirmed=(r"\brecord each date the item states\b",))
        self.assert_sentence(step, r"\bstates no date\b[^.;]*\bleave the due date blank\b", r"\bUNVERIFIED\b",
                             DO_NOT + r"calculate a due date\b")
        self.assert_prohibited(step, r"\bcalculate a due date\b", r"\bsupply one from memory\b")
        self.assert_carries(step, "objection time limits", "penalty or interest questions")
        self.assert_routes(step, 2)

    def test_triage_assigns_owners_and_sends_nothing(self) -> None:
        step = workflow_step("au-ato-correspondence-triage", 6)
        self.assert_sentence(step, r"\bregister names nobody\b", affirmed=(r"\bunassigned\b",))
        # Each action is forbidden in its own right, not merely named beside one that is.
        self.assert_prohibited(step, r"\breply to the ATO\b", r"\bcontact the client\b", r"\bpay\b",
                               r"\blodge\b", r"\bobject\b", r"\bchange a communication preference\b")
        self.assert_sentence(step, r"\bdraft a reply only when the practitioner asks\b",
                             r"\bonly for their review\b")

    def test_triage_checks_completeness(self) -> None:
        step = workflow_step("au-ato-correspondence-triage", 7)
        self.assert_carries(step, "35 days", "60 days", "Communication history", "paper letters",
                            "Human review pending", "4 November 2026")

    def test_triage_sources_are_pending(self) -> None:
        self.assert_cited_and_recorded(
            "au-ato-correspondence-triage",
            f"{ATO_AGENTS}/client-communication",
            f"{ATO_AGENTS}/client-communication/communication-types",
            f"{ATO_AGENTS}/online-services-for-agents-user-guide/communication/communication-history",
            "https://www.ato.gov.au/online-services/scams-cyber-safety-and-identity-protection/verify-or-report-an-ato-scam",
        )

    # au-ato-account-reconciliation

    def test_reconciliation_checks_dates_in_each_download(self) -> None:
        self.assert_carries(section("au-ato-account-reconciliation", "Inputs"), "activity statement account",
                            "income tax account", "processed and effective dates")
        step = workflow_step("au-ato-account-reconciliation", 1)
        self.assert_carries(step, "integrated client account (ICA)", "sequence number",
                            "'the date we have finalised processing and update the account'",
                            "'the date a refund is sent or for a debt, when the payment is due'")
        self.assert_sentence(step, r"\bUNVERIFIED\b", DO_NOT + r"infer a missing date\b")

    def test_reconciliation_recomputes_balances_from_transactions(self) -> None:
        step = workflow_step("au-ato-account-reconciliation", 2)
        self.assert_sentence(step, r"\b4 November 2026\b",
                             r"\brunning balance is not calculated in the order of the sort\b",
                             r"'double counted'")
        self.assert_sentence(
            step, DO_NOT + r"rely on the portal's running balance or a download's totals\b",
            affirmed=(r"\bremove duplicated breakdown lines\b", r"\blisting each one removed\b",
                      r"\brecompute every balance from the transaction amounts\b"),
        )

    def test_reconciliation_fixes_the_balance_by_processed_date(self) -> None:
        step = workflow_step("au-ato-account-reconciliation", 3)
        self.assert_sentence(step, r"\bprocessed on or before that date\b", r"\bbalance by effective date\b")

    def test_reconciliation_lists_items_processed_after_balance_date(self) -> None:
        step = workflow_step("au-ato-account-reconciliation", 4)
        # The cut-off pairs a later processed date with an earlier period, in one clause.
        listed = (r"\bprocessed after balance date for a period ending on or before "
                  r"(balance date|it|that date)\b")
        # Each column is required on its own, in any order, inside the column list.
        columns = [rf"\bwith its\b[^.]*\b{column}\b[^.]*\bas a reconciling item\b"
                   for column in ("processed date", "effective date", "period", "amount")]
        self.assert_sentence(
            step, listed, *columns,
            r"\breconciling item between the ATO balance at balance date and the ledger control account\b",
            affirmed=(r"\blist every transaction\b",),
        )
        self.assert_sentence(step, r"\bnever net such an item into either balance silently\b",
                             affirmed=(r"\breviewer decides\b",))
        self.assert_sentence(step, r"\bpayment made on or before balance date that the ATO processed after it\b",
                             r"\b4 business days\b")

    def test_reconciliation_pairs_offsets_and_routes_breaks(self) -> None:
        step = workflow_step("au-ato-account-reconciliation", 5)
        self.assert_sentence(step, r"\boffset\w*\b", affirmed=(r"\bpair each offset across both accounts\b",))
        self.assert_carries(step, "break tracing", "BAS figure corrections", "general interest charge",
                            "disputed assessment")
        self.assert_routes(step, 4)

    def test_reconciliation_posts_nothing(self) -> None:
        step = workflow_step("au-ato-account-reconciliation", 6)
        self.assert_prohibited(step, r"\bpost a journal\b", r"\bpay\b", r"\blodge an amendment\b",
                               r"\bcontact the ATO\b")
        self.assert_sentence(step, r"\bHuman review pending\b", r"\b4 November 2026\b")
        self.assert_sentence(step, r"\bcolumn headings were not seen\b")

    def test_reconciliation_sources_are_pending(self) -> None:
        guide = f"{ATO_AGENTS}/online-services-for-agents-user-guide/accounts-and-payments"
        self.assert_cited_and_recorded(
            "au-ato-account-reconciliation",
            guide,
            f"{guide}/tax-accounts",
            "https://www.ato.gov.au/online-services/businesses-and-organisations-online-services/"
            "account-and-payments-in-online-services-for-business",
            "https://www.ato.gov.au/online-services/technical-support/troubleshooting-for-businesses-and-tax-practitioners",
            "https://www.ato.gov.au/individuals-and-families/paying-the-ato/interest-and-penalties/"
            "interest-we-charge/calculate-and-report-ato-interest",
            "https://www.ato.gov.au/businesses-and-organisations/preparing-lodging-and-paying/"
            "business-activity-statements-bas/bas-and-gst-tips/bas-refund/offsetting",
        )


if __name__ == "__main__":
    unittest.main()
