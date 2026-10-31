# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""Every distributed file keeps the copyright notice LICENSE requires redistributors to keep."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROSE_NOTICE = (
    "Copyright 2026 Ryan Duguid. From github.com/ryanduguid/australian-accounting-skills, "
    "FSL-1.1-ALv2. Copies and adaptations must keep this notice.\n"
)
CODE_NOTICE = "# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2\n"
CREDIT_LINE = "Based on australian-accounting-skills by Ryan Duguid"


class AttributionTests(unittest.TestCase):
    def test_every_skill_reference_and_rule_ends_with_the_notice(self) -> None:
        paths = [
            *ROOT.glob(".claude/skills/*/SKILL.md"),
            *ROOT.glob(".claude/skills/*/references/*.md"),
            *ROOT.glob(".claude/rules/*.md"),
        ]
        self.assertGreaterEqual(len(paths), 76)
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                self.assertTrue(path.read_text(encoding="utf-8").endswith("\n\n" + PROSE_NOTICE))

    def test_every_script_and_test_opens_with_the_notice(self) -> None:
        paths = [*ROOT.glob("scripts/*.py"), *ROOT.glob("tests/*.py")]
        self.assertGreaterEqual(len(paths), 2)
        for path in paths:
            with self.subTest(path=path.relative_to(ROOT).as_posix()):
                lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
                position = 1 if lines[0].startswith("#!") else 0
                self.assertEqual(lines[position], CODE_NOTICE)

    def test_the_credit_and_author_stay_in_the_notices_and_manifests(self) -> None:
        self.assertIn(CREDIT_LINE, (ROOT / "NOTICE").read_text(encoding="utf-8"))
        self.assertIn("NOTICE's credit", (ROOT / "AGENTS.md").read_text(encoding="utf-8"))
        codex = json.loads((ROOT / ".codex-plugin/plugin.json").read_text(encoding="utf-8"))
        self.assertEqual(codex["author"]["name"], "Ryan Duguid")
        marketplace = json.loads((ROOT / ".claude-plugin/marketplace.json").read_text(encoding="utf-8"))
        self.assertEqual(marketplace["plugins"][0]["author"]["name"], "Ryan Duguid")


if __name__ == "__main__":
    unittest.main()
