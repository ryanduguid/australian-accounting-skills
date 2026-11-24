# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: Apache-2.0
"""Every case skill opens its hand-off with the same 5-part close-out, and every
rule a skill applies from a stated income year has a row in docs/year-changes.md.
"""

from __future__ import annotations

import datetime
import re
import unittest

from skill_prose import SKILLS, raw_section, records, skill_text, workflow_step

CLOSE_OUT = """**Close-out.** Begin the hand-off with these 5 parts, in this order: <!-- close-out -->

1. Bottom line: the prepared result for the reviewer, or what stops one, in 1 or 2 sentences.
2. Done: what was prepared and checked.
3. Figures: where each key figure came from, agreeing with the workpaper.
4. Open items: each with its owner and next action.
5. Files: at most 5 links to the workpapers and sources relied on.
"""
HANDOFF = ("Hand-off and checks", "Checks before handing over", "Output")
#: Export references with no case to close out.
NO_CLOSE_OUT = {"myob-exports", "xero-exports"}
YEAR_CHANGES = SKILLS.parents[1] / "docs" / "year-changes.md"
MARKER = re.compile(r"<!-- year-change: (\d{4}-\d{2}) -->")
COLUMNS = ["Income year", "Skill", "Section", "Change", "Source", "Quote", "Checked"]


def handoff(skill: str) -> str:
    """The first hand-off section in the skill."""
    first = re.search(rf"^## ({'|'.join(map(re.escape, HANDOFF))})$", skill_text(skill), re.MULTILINE)
    assert first, f"{skill} has no hand-off section"
    return raw_section(skill, first.group(1))


def year_change_rows() -> list[dict[str, str]]:
    lines = [line for line in YEAR_CHANGES.read_text(encoding="utf-8").splitlines() if line.startswith("|")]
    header = [cell.strip() for cell in lines[0].strip("|").split("|")]
    assert header == COLUMNS, header
    return [dict(zip(COLUMNS, (cell.strip() for cell in line.strip("|").split("|")), strict=True)) for line in lines[2:]]


class CloseOutTests(unittest.TestCase):
    def test_every_case_skill_opens_its_hand_off_with_the_close_out(self) -> None:
        for path in sorted(SKILLS.glob("*/SKILL.md")):
            name = path.parent.name
            with self.subTest(skill=name):
                if name in NO_CLOSE_OUT:
                    self.assertNotIn("<!-- close-out -->", skill_text(name))
                    continue
                self.assertEqual(skill_text(name).count("<!-- close-out -->"), 1)
                self.assertTrue(handoff(name).lstrip("\n").startswith(CLOSE_OUT), name)


class YearChangeTests(unittest.TestCase):
    def test_each_marker_has_one_row_and_each_row_a_marker(self) -> None:
        marked = sorted(
            (year, path.parent.name)
            for path in SKILLS.glob("*/SKILL.md")
            for year in MARKER.findall(path.read_text(encoding="utf-8"))
        )
        rows = sorted((row["Income year"], row["Skill"]) for row in year_change_rows())
        self.assertTrue(rows)
        self.assertEqual(marked, rows)

    def test_each_row_names_its_section_source_and_check_date(self) -> None:
        today = datetime.datetime.now(datetime.UTC).date()
        for row in year_change_rows():
            skill = row["Skill"]
            with self.subTest(skill=skill, year=row["Income year"]):
                step = re.fullmatch(r"Workflow step (\d+[a-z]?)", row["Section"])
                part = workflow_step(skill, step.group(1)) if step else raw_section(skill, row["Section"])
                self.assertIn(f"<!-- year-change: {row['Income year']} -->", part)
                self.assertIn(row["Source"], skill_text(skill))
                self.assertIn(row["Source"], records(skill))
                self.assertTrue(row["Change"].endswith("."))
                self.assertGreater(len(row["Quote"]), 20)
                checked = datetime.date.fromisoformat(row["Checked"])
                self.assertLessEqual(checked, today)


if __name__ == "__main__":
    unittest.main()
