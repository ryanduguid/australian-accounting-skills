# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""Two review registers keep every item visible until a person decides it.

The FBT sweep keeps a line register whose account totals tie to the ledger,
and the registered agent self-review adds optional professional-body and
AML/CTF rows that record evidence and gaps without concluding, and an ATO
client list reconciliation that leaves each difference as a question. The FBT car comparison
keeps each car's method evidence and leaves the method to the reviewer. Each test reads one
numbered workflow step, or one section, and checks the columns, statuses,
authorities, dates and prohibitions it must carry, not its wording, in the
style of test_practice_workflows.py. A prohibition or negative predicate is
checked within one sentence with its negator before its verb, and each term
of a list the step must carry in full is required on its own. The helpers
are in skill_prose.py.
"""

from __future__ import annotations

import re
import unittest

from skill_prose import (
    DO_NOT,
    IN_PROHIBITED_LIST,
    ISO_DATE,
    NOT,
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

FBT = "fbt-annual-workflow"
AGENT = "au-tax-agent-obligations"


class ReviewRegisterTests(unittest.TestCase):
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

    # fbt-annual-workflow

    def test_fbt_sweep_lists_every_line_with_one_status(self) -> None:
        step = workflow_step(FBT, 1)
        # Each column is required on its own, inside the column list.
        columns = [rf"\bwith its\b[^.;:]*\b{column}\b"
                   for column in ("account", "date", "reference", "description", "amount")]
        self.assert_sentence(step, r"\bin each swept account for the FBT year\b", *columns,
                             affirmed=(r"\blist every GL line\b",))
        # The 3 statuses, each with what it records, and one status a line.
        self.assert_sentence(
            step, r"\b(exactly one|a single|only one)\b[^.;:]*\bstatus\b[^.;:]*\breason\b",
            r"\bbenefit, with its category\b[^.;]*\bemployee or associate\b",
            r"\bnot a fringe benefit, with the evidence\b", r"\bunresolved, with the evidence needed\b",
        )
        self.assert_sentence(step, r"\bnets? to nil\b", r"\bboth entries\b",
                             affirmed=(r"\b(stays?|remains?) on the register\b",))

    def test_fbt_line_register_ties_each_account_to_the_ledger(self) -> None:
        step = workflow_step(FBT, 1)
        self.assert_sentence(step, r"\btie each account total to\b[^.;]*\bGL movement for the FBT year\b",
                             affirmed=(r"\btotal the register by account\b",))
        # A difference goes to the reviewer; it is not plugged and no line is dropped to clear it.
        self.assert_sentence(step, r"\bto the reviewer as an open item\b", affirmed=(r"\bcarry any difference\b",))
        self.assert_prohibited(step, r"\bplug the difference\b", r"\bdrop a line\b")
        self.assert_sentence(step, r"\bbenefit register\b", affirmed=(r"\btrace each benefit line by its reference\b",))
        self.assert_sentence(step, affirmed=(r"\bcarry each unresolved line to the reviewer\b",))
        self.assert_sentence(step, r"\bproposal\b", r"\bwhether a line is a fringe benefit\b",
                             affirmed=(r"\bis a reviewer decision\b",))

    def test_fbt_checks_and_workpaper_carry_the_line_register(self) -> None:
        bullets = [line for line in raw_section(FBT, "Checks").splitlines()
                   if "line register" in line.casefold()]
        self.assertEqual(len(bullets), 1)
        self.assert_sentence(
            bullets[0], r"\bevery line in each swept account\b", r"\bone status and its reason\b",
            r"\bties to its GL movement for the FBT year\b", r"\bany difference is an open item\b",
        )
        self.assert_carries(workflow_step(FBT, 9), "line register", "account tie-out")

    def test_fbt_car_methods_are_compared_per_car_only_on_records(self) -> None:
        # The fbt-car-method-records-pair card relies on each of these.
        self.assert_carries(section(FBT, "Inputs needed"), "odometer/logbooks where operating cost method is in play")
        self.assert_sentence(workflow_step(FBT, 1), r"\bcars\b",
                             affirmed=(r"\bstatutory formula versus operating cost\b",
                                       r"\bcomparing both where logbooks exist\b"))
        step = workflow_step(FBT, 3)
        self.assert_sentence(step, affirmed=(r"\bproduce the related missing logbook/odometer list\b",))
        self.assert_sentence(step, r"\bmissing support\b", r"\breduction\b[^.;:]*\bis " + NOT + r"assumed\b")
        self.assert_sentence(section(FBT, "Checks before handing over"),
                             affirmed=(r"\bmethod choice documented per vehicle\b", r"\bdays-available count\b"))
        self.assert_sentence(section(FBT, "Boundaries"), r"\bmethod elections\b",
                             affirmed=(r"\bgo to the reviewer as flagged decisions\b",))

    # au-tax-agent-obligations

    def test_agent_professional_body_rows_are_optional_separate_and_inconclusive(self) -> None:
        step = workflow_step(AGENT, 8)
        self.assert_carries(step, "Human review pending", "4 November 2026")
        self.assert_sentence(step, r"\bCA ANZ\b", r"\bCPA Australia\b", r"\bIPA\b",
                             affirmed=(r"\bonly for a membership\b",))
        self.assert_sentence(
            step, r"\bmembership obligations\b", NOT + r"obligations under the \*?Tax Agent Services Act 2009\b",
            affirmed=(r"\bkeep them apart from the rows in steps 1 to 7\b",),
        )
        self.assert_sentence(step, DO_NOT + r"treat evidence for one kind of row as meeting the other\b")
        # Each column is required on its own.
        self.assert_sentence(step, r"\beach row carries\b", *[
            rf"\b{column}\b" for column in ("standard or by-law", "version in force for the review period",
                                            "firm or member", "evidence held", "gap", "owner", "status",
                                            "next action")])
        self.assert_sentence(step, r"\bevidence held and gaps\b", r"\breach no conclusion about compliance\b")
        self.assert_sentence(step, r"\bwhether a firm or member meets\b", r"\bresponsible practitioner\b",
                             DO_NOT + r"conclude\b")

    def test_agent_professional_body_rows_test_risk_and_quality_management(self) -> None:
        step = workflow_step(AGENT, 8)
        self.assert_sentence(
            step, r"\bAPES 325\b", r"\bMembers in Public Practice conducting the operations of a firm in Australia\b",
            r"\bparagraph 1\.5\b", r"\bhas adopted it\b", r"\bProfessional Bodies\b", r"\bCA ANZ\b",
            r"\bCPA Australia\b", r"\bIPA\b",
        )
        self.assert_sentence(step, r"\bby 1 April 2023\b", r"\bparagraph 1\.2\b",
                             affirmed=(r"\bincorporate its amendments\b",))
        self.assert_carries(step, "paragraph 6.1", "paragraph 4.1", "paragraphs 5.1 and 5.3", "paragraph 6.3",
                            "paragraph 4.4")
        self.assert_sentence(step, r"\bbefore 1 April 2023\b", r"\b2023 amendments\b", affirmed=(r"\bis a gap\b",))
        # APES 320 covers the non-assurance practice; ASQM 1 covers the assurance practice.
        self.assert_sentence(step, r"\bAPES 320\b", r"\bnon-assurance practice\b", r"\bparagraphs 1\.4 and 1\.10\b",
                             r"\bby 1 January 2023\b")
        self.assert_carries(step, "paragraph 3.5", "paragraph 3.6", "paragraph 3.17")
        self.assert_sentence(step, r"\bat least one completed engagement for each engagement partner\b",
                             r"\bnot involved in performing it\b", r"\bparagraph 4\.65\b")
        self.assert_sentence(
            step, r"\baudit, review, other assurance or related services engagement\b", r"\bASQM 1\b",
            r"\bAuditing and Assurance Standards Board\b", r"\bAppendix 1\b", r"\bAus 0\.1\b",
            affirmed=(r"\bassurance practice applies\b",),
        )
        self.assert_sentence(step, r"\bat least annually\b", r"\bparagraph 53\b")
        self.assert_sentence(step, r"\bboth practices\b", affirmed=(r"\bhas both rows\b",))

    def test_agent_professional_body_rows_record_insurance_by_body(self) -> None:
        step = workflow_step(AGENT, 8)
        self.assert_sentence(
            step, r"\bCR 2A\b", r"\bissued 23 May 2025\b", r"\bCertificate of Public Practice\b",
            r"\bAffiliate members\b", r"\bPractice Entity members\b", r"\bCR 2A\.1\b",
            NOT + r"to Chartered Accountants resident in New Zealand\b", r"\bCR 2A\.5 \(CR 2A\.4\)",
            r"\bwithin 7 days of becoming aware\b", r"\bexpired\b", r"\bcancelled\b", r"\bavoided\b",
            r"\bineffective\b", r"\bunless it is renewed or replaced within that period\b",
        )
        self.assert_sentence(
            step, r"\beffective 1 October 2026\b",
            r"\bproviding Public Accounting Services or holding a current Public Practice Certificate\b",
            r"\bBy-Law 9\.8\(a\)", r"\bcancellation, lapse or failure to renew within 10 Business Days\b",
            r"\bBy-Law 9\.8\(e\)\(ii\)", r"\beach annual renewal\b", r"\bBy-Law 9\.8\(h\)",
        )
        # Each set of by-laws keeps its own class of certificate holder.
        self.assert_sentence(step, r"\bBy-Laws 9\.1\.10 and 9\.1\.11 to Professional Practice Certificate holders\b",
                             r"\bBy-Laws 9\.1\.7 and 9\.1\.8 to Limited-PPC holders\b")
        self.assert_sentence(step, r"\bpolicy\b", r"\beach notice given to the body with its date\b",
                             r"\brenewal confirmation\b", affirmed=(r"\brecord the policy\b",))
        self.assert_sentence(step, NOT + r"from memory\b", affirmed=(r"\btake cover levels and policy terms\b",))
        self.assert_sentence(step, r"\bTPB insurance row in step 4\b", affirmed=(r"\bkeep these rows apart\b",))

    def test_agent_professional_body_rows_record_cpd_by_body(self) -> None:
        step = workflow_step(AGENT, 8)
        self.assert_sentence(step, r"\bCPD period\b", r"\bhours evidenced\b", r"\bexemption\b", r"\brecords held\b",
                             affirmed=(r"\btaking the required hours from the body's text at use time\b",))
        self.assert_sentence(step, r"\bCR 7\b", r"\bannual and triennium minimums in CR 7\.3\b",
                             r"\bexemptions in CR 7\.5\b", r"\b(6|six) years in CR 7\.6\(a\)")
        self.assert_sentence(step, r"\bBy-Law 4\.1\b", r"\beach triennium and each year of it\b")
        self.assert_sentence(step, r"\bBy-Law 4\.2\b", r"\bdates, time and topics\b",
                             r"\bat least 12 months after the end of each triennium\b")
        # Pronouncement 7 v5.0 changes the IPA's period from 1 July 2026.
        self.assert_sentence(
            step, r"\bPronouncement 7\b", r"\bv5\.0\b", r"\b17 February 2026\b",
            r"\b1 July 2024 to 30 June 2027 CPD period\b", r"\bPart-1, from 1 July 2024 to 30 June 2026\b",
            r"\bPart-2, from 1 July 2026 to 30 June 2027\b", r"\beach CPD period is one financial year\b",
            r"\bparagraph 1\.3\b", r"\bat least (5|five) years after the end of each period\b", r"\bparagraph 7\.1\b",
        )
        self.assert_sentence(step, r"\bTPB CPE row in step 5\b", affirmed=(r"\bkeep these rows apart\b",))

    def test_agent_register_lists_professional_body_rows_and_sends_nothing(self) -> None:
        self.assert_prohibited(workflow_step(AGENT, 9), r"\bcontact the TPB\b", r"\ban insurer\b",
                               r"\ba professional association\b")
        self.assert_sentence(
            section(AGENT, "Hand-off"), r"\bProfessional-body rows\b", r"\bonly for a membership held\b",
            r"\bapart from the Tax Agent Services Act rows\b", r"\bwithout a conclusion about compliance\b",
        )
        self.assert_carries(section(AGENT, "Inputs"), "CA ANZ, CPA Australia or IPA membership",
                            "risk management framework", "quality management documents", "CPD records")

    def test_agent_professional_body_sources_are_pending_or_marked_unindexed(self) -> None:
        self.assert_cited_and_recorded(
            AGENT,
            "https://apesb.org.au/standards-guidance/risk-management-for-firms-apes-325/",
            "https://apesb.org.au/standards-guidance/quality-management-for-firms-that-provide-non-assurance-services/",
            "https://www.legislation.gov.au/F2021L00415/latest/text",
        )
        # The member bodies' hosts are outside the retrieval policy, so the step says so.
        self.assert_sentence(workflow_step(AGENT, 8), NOT + r"indexed in `sources\.json`",
                             r"\bretrieval policy\b", affirmed=(r"\bopen the version in force at use time\b",))
        sources = section(AGENT, "Primary-source starting point")
        for host in ("www.charteredaccountantsanz.com", "www.cpaaustralia.com.au", "www.publicaccountants.org.au"):
            with self.subTest(host=host):
                self.assertIn(f"](https://{host}/", sources)

    def test_agent_aml_ctf_rows_are_separate_inconclusive_and_route_client_checks(self) -> None:
        step = workflow_step(AGENT, "8a")
        self.assert_carries(step, "Human review pending", "12 November 2026")
        self.assert_sentence(step, r"\breporting entity that provides designated services\b",
                             affirmed=(r"\badd these rows only where\b",))
        # Whether a service is designated is never answered here.
        self.assert_sentence(step, r"\bwhether a service is a designated service\b", r"\bAML/CTF compliance officer\b",
                             DO_NOT + r"decide it\b", affirmed=(r"\badd no rows\b",))
        self.assert_sentence(
            step, NOT + r"obligations under the \*?Tax Agent Services Act 2009\b", r"\bprofessional body\b",
            affirmed=(r"\bkeep them apart from the rows in steps 1 to 8\b",),
        )
        self.assert_sentence(step, DO_NOT + r"treat evidence for one kind of row as meeting another\b")
        self.assert_sentence(step, r"\beach row carries\b", *[
            rf"\b{column}\b" for column in ("provision", "compilation in force for the review period", "evidence held",
                                            "gap", "owner", "status", "next action")])
        self.assert_sentence(step, r"\bevidence held and gaps\b", r"\breach no conclusion about compliance\b")
        # Client-level customer due diligence belongs to the coverage skill.
        self.assert_sentence(step, r"\bclient-level checks\b", r"`au-aml-ctf-client-coverage`",
                             DO_NOT + r"repeat them here\b")
        # A possible suspicious matter stops the work, and no report's content enters the register.
        self.assert_sentence(step, r"\bsuspicious matter report\b", r"\bAML/CTF compliance officer\b",
                             r"\bdisclose it to no one else\b", r"\bs 123 of the AML/CTF Act\b")
        self.assert_sentence(step, r"\bpolicy and process evidence only\b",
                             NOT + r"the content of a report or a suspicion\b")
        self.assert_sentence(step, r"\bwhether an obligation is met\b", r"\bAML/CTF compliance officer\b",
                             DO_NOT + r"conclude\b")

    def test_agent_aml_ctf_rows_cite_each_obligation_in_the_act_and_rules(self) -> None:
        step = workflow_step(AGENT, "8a")
        self.assert_sentence(step, r"\bcompilation 63 of the AML/CTF Act\b", r"\b1 October 2026\b",
                             r"\bcompilation 1 of the AML/CTF Rules\b", r"\b31 March 2026\b")
        # One sentence per obligation, each provision with its instrument.
        for provisions in (
            (r"\bReporting Entities Roll\b", r"\bs 51B of the AML/CTF Act\b", r"\bs 51F of the AML/CTF Act\b",
             r"\bs 3-9 of the AML/CTF Rules\b"),
            (r"\bML/TF risk assessment\b", r"\bs 26C of the AML/CTF Act\b", r"\bs 26D of the AML/CTF Act\b",
             r"\bs 5-1 of the AML/CTF Rules\b", r"\bs 26E of the AML/CTF Act\b"),
            (r"\bAML/CTF policies\b", r"\bs 26F\(3\) and \(4\) of the AML/CTF Act\b", r"\bs 26F\(8\) of the AML/CTF Act\b",
             r"\bs 26G of the AML/CTF Act\b"),
            (r"\bgoverning body\b", r"\bs 26H of the AML/CTF Act\b", r"\bss 5-6 and 5-7 of the AML/CTF Rules\b"),
            (r"\bmanagement level\b", r"\bs 26J of the AML/CTF Act\b", r"\bs 26K of the AML/CTF Act\b",
             r"\bs 5-14 of the AML/CTF Rules\b", r"\bs 26M of the AML/CTF Act\b",
             r"\bauthority, independence and access to resources and information\b",
             r"\bs 26J\(2\)\(b\) of the AML/CTF Act\b", r"\bresident of Australia\b",
             r"\bs 26J\(3\)\(a\) of the AML/CTF Act\b"),
            (r"\bs 26N of the AML/CTF Act\b", r"\bs 5-15 of the AML/CTF Rules\b", r"\bsenior manager\b",
             r"\bs 26P of the AML/CTF Act\b"),
            (r"\bpersonnel due diligence and training\b", r"\bs 26F\(4\)\(d\) and \(e\) of the AML/CTF Act\b",
             r"\bss 5-8 and 5-9 of the AML/CTF Rules\b"),
            (r"\bindependent evaluation\b", r"\bs 26F\(4\)\(f\) of the AML/CTF Act\b", r"\bs 5-10 of the AML/CTF Rules\b"),
            (r"\bss 5-11 to 5-13 of the AML/CTF Rules\b", r"\bs 41 of the AML/CTF Act\b", r"\bs 43 of the AML/CTF Act\b"),
            (r"\breporting period\b", r"\bs 9-9 of the AML/CTF Rules\b", r"\bs 47 of the AML/CTF Act\b"),
            (r"\bPart 1A of the AML/CTF Act\b", r"\bs 116 of the AML/CTF Act\b", r"\breconstruct\b",
             r"\bs 107 of the AML/CTF Act\b", r"\bdocument a customer gives\b", r"\bs 108 of the AML/CTF Act\b"),
            (r"\breview and update\b", r"\bs 26F\(3\)\(c\) and \(d\) of the AML/CTF Act\b",
             r"\badverse findings\b", r"\bs 5-4 of the AML/CTF Rules\b", r"\btargeted financial sanctions\b",
             r"\bs 5-3 of the AML/CTF Rules\b", r"\bsenior manager's approval\b",
             r"\bforeign politically exposed person\b", r"\bs 5-5\(1\) of the AML/CTF Rules\b",
             r"\bs 5-5\(1A\) of the AML/CTF Rules\b"),
            (r"\bs 26F\(3\)\(b\) of the AML/CTF Act\b", r"\bsource of wealth and source of funds\b",
             r"\bs 5-2 of the AML/CTF Rules\b"),
        ):
            self.assert_sentence(step, *provisions)
        # AUSTRAC's summary and the Rules differ on the compliance report period; both go to the officer.
        self.assert_sentence(step, r"\bcalendar year\b", r"\bfinancial year\b", r"\bs 9-9 of the AML/CTF Rules\b",
                             r"\bthat instrument sets the period\b",
                             affirmed=(r"\brecord that description as a discrepancy\b",))
        # A row whose period has not ended is a question, never a gap.
        self.assert_sentence(step, r"\bperiod has not ended\b", r"\bquestion for the AML/CTF compliance officer\b",
                             r"\bdate the period runs from\b", NOT + r"(as )?a gap\b")
        self.assert_sentence(step, r"\bs 46 of the AML/CTF Act\b",
                             r"\bonly where the AML/CTF compliance officer's assessment records that service\b")
        self.assert_sentence(step, r"\bfrom the provision at use time\b", r"\btimeliness\b",
                             r"\bAML/CTF compliance officer\b")

    def test_agent_client_list_reconciliation_matches_on_a_shared_identifier(self) -> None:
        step = workflow_step(AGENT, "8b")
        self.assert_carries(step, "Human review pending", "12 November 2026")
        self.assert_sentence(step, r"\bclient list page\b", r"\b14 October 2026\b", r"\bregistered agent number\b",
                             r"\bAccess Manager\b", r"\bCSV\b")
        self.assert_sentence(step, r"\bmore than 3,500 clients\b", r"\brelationship\b", r"\bentity type\b",
                             r"\btax product\b")
        # The ATO does not publish the columns, so the practitioner supplies them.
        self.assert_sentence(step, NOT + r"list the export's columns\b",
                             affirmed=(r"\bask the practitioner for the column headings\b",))
        self.assert_sentence(step, r"\bincomplete\b", r"\bpractice list and not the ATO list\b", r"`UNVERIFIED`")
        self.assert_sentence(step, r"\bABN or another identifier both lists carry\b",
                             affirmed=(r"\bmatch the lists\b", r"\brecord which\b"))
        self.assert_sentence(step, r"\bname only\b", r"`UNVERIFIED`", NOT + r"treat it as a match\b",
                             r"\blist each such pair in both lists of clients on one list only\b",
                             r"\bpossible pairing\b")
        self.assert_sentence(step, r"\bpractice list and not the ATO list\b", r"\bATO list and not the practice list\b",
                             r"\bidentifier conflicts\b", r"\bquestion for the responsible practitioner\b",
                             r"\ban identifier held by 2 or more clients in either list\b",
                             r"\ba client whose identifiers match different clients on the other list\b")
        self.assert_sentence(step, r"\bsecurity-assessed\b", r"\brestricted in Access Manager\b", r"\bend-dated\b",
                             NOT + r"findings\b")
        self.assert_sentence(step, r"\bTFN\b", r"\bkeep it in the matching workpaper in the firm's approved environment\b",
                             r"\bidentify each client in the output by the practice's client code\b",
                             r"\bby its row number in the ATO file\b")

    def test_agent_client_list_reconciliation_routes_and_changes_nothing_at_the_ato(self) -> None:
        step = workflow_step(AGENT, "8b")
        self.assert_sentence(step, r"\bpractice list and not the ATO list\b", r"`au-client-acceptance` step 5\b",
                             r"\bATO list\b", r"\bno longer acts for\b", r"`au-client-departure` step 7\b")
        self.assert_prohibited(step, r"\badd, remove or change a client at the ATO\b",
                               r"\bdecide whether the practice may act\b")
        self.assert_carries(section(AGENT, "Inputs"), "Online services for agents", "registered agent number",
                            "column headings", "AUSTRAC enrolment", "independent evaluation reports",
                            "assessment of which of its services are designated services")
        self.assert_prohibited(workflow_step(AGENT, 9), r"\bAUSTRAC\b")
        hand_off = section(AGENT, "Hand-off")
        self.assert_sentence(hand_off, r"\bAML/CTF rows\b", r"\bapart from the Tax Agent Services Act\b",
                             r"\bwithout a conclusion about compliance or about whether a service is designated\b")
        self.assert_sentence(hand_off, r"\bpractice list and not the ATO list\b", r"\bATO list and not the practice list\b",
                             r"\bidentifier conflicts\b")

    def test_agent_aml_ctf_and_client_list_sources_are_pending(self) -> None:
        self.assert_cited_and_recorded(
            AGENT,
            "https://www.legislation.gov.au/C2006A00169/latest",
            "https://www.legislation.gov.au/F2025L01026/latest",
            "https://www.austrac.gov.au/industry-and-business/obligations-and-guidance/your-obligations",
            "https://www.ato.gov.au/tax-and-super-professionals/digital-services/online-services-for-agents/client-list",
        )


if __name__ == "__main__":
    unittest.main()
