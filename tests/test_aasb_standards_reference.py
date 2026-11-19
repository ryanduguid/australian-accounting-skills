# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The AASB standards reference skill: its index, its version rule and the text it must not hold."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS = REPOSITORY / ".claude" / "skills"
SKILL = SKILLS / "au-aasb-standards-reference"

# The Standards the AASB portal listed by number on 19 November 2026.
PORTAL_LIST = (
    [str(n) for n in range(1, 19)]
    + ["20", "101", "102", "107", "108", "110", "112", "116", "119", "120", "121", "123", "124", "127", "128", "129"]
    + ["132", "133", "134", "136", "137", "138", "139", "140", "141"]
    + ["1004", "1023", "1039", "1048", "1049", "1050", "1051", "1052", "1053", "1054", "1055", "1056", "1057", "1058"]
    + ["1059", "1060", "1061", "S1", "S2"]
)


def text() -> str:
    return (SKILL / "SKILL.md").read_text(encoding="utf-8")


def section(heading: str) -> str:
    body = text()
    start = body.index(f"## {heading}")
    end = body.find("\n## ", start + 1)
    return body[start : end if end != -1 else len(body)]


def index() -> dict[str, str]:
    """Each index row's AASB number and its IFRS counterpart."""
    rows = {}
    for line in section("Standards on the portal").splitlines():
        match = re.fullmatch(r"\| AASB (\w+) \| .+ \| (.+) \|", line)
        if match:
            rows[match.group(1)] = match.group(2)
    return rows


class AasbStandardsReferenceTests(unittest.TestCase):
    def test_index_lists_the_portal_standards_with_consistent_counterparts(self) -> None:
        rows = index()
        self.assertEqual(list(rows), PORTAL_LIST)
        for number, counterpart in rows.items():
            with self.subTest(number=number):
                if number.startswith("S"):
                    expected = f"IFRS {number}"
                elif int(number) < 100:
                    expected = f"IFRS {number}"
                elif int(number) < 1000:
                    expected = f"IAS {int(number) - 100}"
                else:
                    expected = "none"
                self.assertTrue(counterpart.startswith(expected), counterpart)

    def test_version_is_chosen_by_the_period_not_the_label(self) -> None:
        workflow = " ".join(section("Workflow").split())
        for phrase in (
            "use the By Reporting Period function with the period's own start and end dates",
            "the Future Periods tab and the Standard's Amended By list",
            # The portal holds every version from 1 July 2021; the archive only matters before that.
            "The portal holds the versions for periods beginning on or after 1 July 2021. For a period beginning before that date, use the archived Browse for Pronouncements search",
            "A URL, version label or download date does not select a version: the application paragraph does.",
            "Statements prepared under Tier 2 do not comply with IFRS Standards",
            # AASB 1057's insurance exceptions and elections sit outside paragraphs 5 and 6.
            "For insurance contracts, read paragraphs 5A and 6A too",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, workflow)

    def test_holds_no_standard_text_and_says_what_it_lacks(self) -> None:
        body = text()
        self.assertNotRegex(body, r"(?m)^>", "no block quotation")
        for quoted in re.findall(r"[\"“]([^\"”]+)[\"”]", body.split("---", 2)[2]):
            with self.subTest(quoted=quoted):
                self.assertLessEqual(len(quoted.split()), 6, "no quotation of a Standard")
        lacks = " ".join(section("What this skill does not hold").split())
        self.assertIn("No text of any Standard, Interpretation, Basis for Conclusions", lacks)
        self.assertIn("No version of any Standard.", lacks)
        terms = " ".join(section("Quotation and copyright").split())
        for phrase in (
            "it contains IFRS Foundation copyright material",
            "in unaltered form, with the notice kept, for personal and non-commercial use",
            "Client workpapers, fee-earning advice and anything published are not personal, non-commercial use.",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, terms)

    def test_each_listed_source_has_a_record_read_that_day(self) -> None:
        records = {r["url"]: r for r in json.loads((SKILL / "sources.json").read_text(encoding="utf-8"))["sources"]}
        listed = re.findall(r"^- \[[^\]]+\]\((https://[^)]+)\)", section("Primary-source starting point"), re.M)
        self.assertEqual(sorted(listed), sorted(records))
        self.assertIn("https://www.aasb.gov.au/about-the-aasb/copyright-notice/", records)
        for url, record in records.items():
            with self.subTest(url=url):
                self.assertEqual(record["fetched_at"], "2026-11-19")
                self.assertEqual(record["verification_status"], "source-discovery-only-human-review-pending")

    def test_routes_only_to_skills_in_the_pack(self) -> None:
        named = re.findall(r"`([a-z0-9-]+)`", section("Routing"))
        self.assertTrue(named)
        for name in named:
            with self.subTest(skill=name):
                self.assertTrue((SKILLS / name / "SKILL.md").is_file())


if __name__ == "__main__":
    unittest.main()
