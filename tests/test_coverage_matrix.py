# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The evidence matrix must describe the tree, not the author's memory of it.

`coverage.json` says what backs each skill: how many primary sources it
indexes, whether any moved since a person last reviewed them, which validation
cards exercise it, and whether a test asserts its text. A file like that is
worth nothing if it can drift, so `accounting-skills build-coverage` generates
it, and its `--check` mode, run by the native CI job and the coverage-matrix
pre-commit hook, rebuilds it and compares. These checks refuse the two ways a
matrix quietly becomes a decoration: a summary that disagrees with its own
rows, and a classification that lands every skill in the same bucket.
"""

from __future__ import annotations

import hashlib
import json
import re
import unittest
from pathlib import Path
from typing import Any

REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS_DIRECTORY = REPOSITORY / ".claude" / "skills"
COVERAGE_FILE = REPOSITORY / "coverage.json"

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


def matrix() -> dict[str, Any]:
    return json.loads(COVERAGE_FILE.read_text(encoding="utf-8"))


def rows() -> list[dict[str, Any]]:
    return matrix()["skills"]


class CoverageMatrixTests(unittest.TestCase):
    def test_every_skill_appears_exactly_once(self) -> None:
        listed = [row["skill"] for row in rows()]
        self.assertEqual(listed, sorted(listed))
        self.assertEqual(len(listed), len(set(listed)))
        self.assertEqual(
            set(listed), {path.parent.name for path in SKILLS_DIRECTORY.glob("*/SKILL.md")}
        )

    def test_totals_agree_with_the_rows_they_summarise(self) -> None:
        """A summary nobody recomputes is the first thing to go wrong."""
        listed = rows()
        totals = matrix()["totals"]
        expected = dict(
            skills=len(listed),
            sources_indexed=sum(row["sources"]["indexed"] for row in listed),
            skills_source_exempt=sum(1 for row in listed if row["sources"]["exempt"]),
            skills_with_unreachable_sources=sum(
                1 for row in listed if row["sources"]["unreachable"]
            ),
            skills_with_sources_moved_since_review=sum(
                1 for row in listed if row["sources"]["moved_since_review"]
            ),
            skills_with_behavioural_gate=sum(1 for row in listed if row["gates"]["behavioural"]),
            skills_with_only_the_seeded_case=sum(
                1 for row in listed if row["validation"]["only_seeded_case"]
            ),
            skills_with_confirmed_pass=sum(
                1 for row in listed if row["validation"]["confirmed_pass"]
            ),
            skills_with_confirmed_fail=sum(
                1 for row in listed if row["validation"]["confirmed_fail"]
            ),
            skills_with_confirmed_on_earlier_card=sum(
                1 for row in listed if row["validation"]["confirmed_on_earlier_card"]
            ),
            sources_reviewed=sum(row["sources"]["reviewed_count"] for row in listed),
        )
        self.assertEqual(totals, expected)

    def test_confirmed_verdicts_count_only_for_the_current_card(self) -> None:
        """Recount the confirmed verdicts, holding each to the card bytes it was judged on.

        A verdict counts as current only when the record's rubric digest equals
        the card as it is now; a verdict on an earlier version is listed apart,
        whether or not the current card also has one.
        Legacy records carry no status and stay out of these lists.
        """
        current: dict[str, set[str]] = {"pass": set(), "fail": set()}
        earlier: set[str] = set()
        for path in sorted((REPOSITORY / "validation" / "results").glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            if record.get("status") != "confirmed":
                continue
            for card, verdict in record["results"].items():
                card_bytes = (REPOSITORY / "validation" / "cases" / f"{card}.md").read_bytes()
                digest = hashlib.sha256(card_bytes).hexdigest()
                if record["provenance"][card]["rubric_sha256"] == digest:
                    current[verdict].add(card)
                else:
                    earlier.add(card)
        self.assertTrue(current["pass"], "no confirmed pass found, so the recount is vacuous")
        for row in rows():
            cards = row["validation"]["case_ids"]
            with self.subTest(skill=row["skill"]):
                for verdict in ("pass", "fail"):
                    self.assertEqual(
                        row["validation"][f"confirmed_{verdict}"],
                        [card for card in cards if card in current[verdict]],
                    )
                self.assertEqual(
                    row["validation"]["confirmed_on_earlier_card"],
                    [card for card in cards if card in earlier],
                )

    def test_reviewed_count_is_the_sources_with_a_review_date(self) -> None:
        for row in rows():
            index = SKILLS_DIRECTORY / row["skill"] / "sources.json"
            records = []
            if index.is_file():
                records = json.loads(index.read_text(encoding="utf-8"))["sources"]
            with self.subTest(skill=row["skill"]):
                self.assertEqual(
                    row["sources"]["reviewed_count"],
                    sum(1 for record in records if record.get("checked_at")),
                )

    def test_verification_page_states_the_matrix_totals(self) -> None:
        page = (REPOSITORY / "docs" / "skill-verification.md").read_text(encoding="utf-8")
        totals = matrix()["totals"]
        self.assertIn(
            f"Totals: {totals['skills']} skills, {totals['sources_indexed']} indexed primary "
            f"sources of which {totals['sources_reviewed']} have a recorded human review, "
            f"{totals['skills_source_exempt']} skills exempt from source indexing, "
            f"{totals['skills_with_unreachable_sources']} skills with an unreachable source, ",
            page,
        )
        listed = [line for line in page.splitlines() if line.startswith("| [`")]
        self.assertEqual(len(listed), totals["skills"])
        for row, line in zip(rows(), listed, strict=True):
            sources = row["sources"]
            if sources["indexed"]:
                with self.subTest(skill=row["skill"]):
                    self.assertIn(f"({sources['reviewed_count']} of {sources['indexed']})", line)

    def test_verification_page_names_every_legacy_record_and_its_fails(self) -> None:
        """Legacy records are left out of the columns, so the legend must say what they hold."""
        page = (REPOSITORY / "docs" / "skill-verification.md").read_text(encoding="utf-8")
        legacy = 0
        for path in sorted((REPOSITORY / "validation" / "results").glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            if "status" in record:
                continue
            legacy += 1
            self.assertIn(f"`{path.name}`", page)
            for card, verdict in record["results"].items():
                if verdict == "fail":
                    self.assertIn(f"`{card}` (`{path.name}`)", page)
        self.assertTrue(legacy, "no legacy record found, so the check is vacuous")

    def test_behavioural_gates_separate_some_skills_from_others(self) -> None:
        """Guard against a classification that has stopped discriminating.

        Every skill is named by the inventory sweep, so a bug that counted
        those as behavioural evidence would mark all 50 covered and read as a
        clean bill of health. All-or-nothing in either direction means the
        column has stopped carrying information.
        """
        gated = [row for row in rows() if row["gates"]["behavioural"]]
        self.assertTrue(gated, "no skill has a behavioural gate, so the column is vacuous")
        self.assertLess(
            len(gated),
            len(rows()),
            "every skill reports a behavioural gate, which means the inventory sweep is "
            "being counted as evidence",
        )

    def test_seeded_case_flag_names_only_the_template_card(self) -> None:
        for row in rows():
            skill = row["skill"]
            cards = row["validation"]["case_ids"]
            with self.subTest(skill=skill):
                # The seeded card; a skill with only this one has nothing
                # written for its own failure modes.
                seeded = f"{skill}-missing-evidence"
                self.assertEqual(row["validation"]["only_seeded_case"], cards == [seeded])
                self.assertEqual(row["validation"]["cases"], len(cards))
                self.assertTrue(cards, "every skill needs at least one validation card")


class SourceProvenanceTests(unittest.TestCase):
    """Shape checks on the fields `scripts/source_refresh.py` writes."""

    def source_records(self) -> list[tuple[str, dict[str, Any]]]:
        found: list[tuple[str, dict[str, Any]]] = []
        for path in sorted(SKILLS_DIRECTORY.glob("*/sources.json")):
            payload = json.loads(path.read_text(encoding="utf-8"))
            for record in payload["sources"]:
                found.append((path.parent.name, record))
        return found

    def test_machine_fields_are_present_and_well_formed(self) -> None:
        """A retrieved source carries a digest; a failed sweep keeps the last one.

        A source that timed out on the most recent sweep still holds the
        digest from the sweep that reached it, and that is deliberate: dropping
        it would restart the comparison and the next successful sweep would
        report `recorded` instead of saying whether the page had moved. So a
        non-200 record may or may not carry a digest, and what matters is that
        whatever it carries is a real one.
        """
        records = self.source_records()
        self.assertTrue(records)
        for skill, record in records:
            with self.subTest(skill=skill, url=record.get("url")):
                self.assertIsInstance(record["http_status"], int)
                self.assertRegex(str(record["fetched_at"]), ISO_DATE)
                self.assertTrue(str(record["final_url"]).startswith("https://"))
                digest = str(record["content_hash"])
                published = str(record["source_last_modified"])
                content_url = str(record.get("content_url", ""))
                if content_url:
                    self.assertTrue(content_url.startswith(("https://", "http://")))
                    self.assertRegex(digest, SHA256, "a readable destination must carry a digest")
                if digest:
                    self.assertRegex(digest, SHA256)
                    self.assertIn(
                        str(record["content_hash_covers"]),
                        ("html", "bytes"),
                        "a digest must say which reading produced it",
                    )
                if published:
                    self.assertRegex(published, ISO_DATE)

    def test_a_fetch_date_never_stands_in_for_a_review_date(self) -> None:
        """The two dates answer different questions and must stay independent.

        `checked_at` means a person read the source and judged it still
        supports the workflow. `fetched_at` means a script retrieved the page.
        Letting a sweep advance `checked_at` would turn every unattended run
        into a fresh review that nobody performed.
        """
        for skill, record in self.source_records():
            with self.subTest(skill=skill, url=record.get("url")):
                checked = str(record["checked_at"])
                if not checked:
                    self.assertEqual(
                        record.get("verification_status"),
                        "source-discovery-only-human-review-pending",
                    )
                    self.assertRegex(str(record.get("review_required_since", "")), ISO_DATE)
                    self.assertFalse(record.get("reviewed_content"))
                    self.assertFalse(record.get("content_hash"))
                    self.assertFalse(record.get("content_url"))
                else:
                    self.assertRegex(checked, ISO_DATE)
                self.assertNotIn(
                    "checked_at",
                    str(record.get("fetched_at", "")),
                    "fetched_at must be a date, not a reference to the review date",
                )

    def test_sources_that_moved_since_review_are_reported_not_hidden(self) -> None:
        """Whatever the tree says, the matrix has to say the same thing."""
        moved: set[str] = set()
        for skill, record in self.source_records():
            published = str(record.get("source_last_modified", ""))
            if published and published > str(record.get("checked_at", "")):
                moved.add(skill)
        reported = {row["skill"] for row in rows() if row["sources"]["moved_since_review"]}
        self.assertEqual(moved, reported)


if __name__ == "__main__":
    unittest.main()
