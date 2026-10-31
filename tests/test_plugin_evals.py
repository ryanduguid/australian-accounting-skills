from __future__ import annotations

import re
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import build_plugin_evals as evals  # noqa: E402


def bullets(section: str) -> list[str]:
    return [line[2:].strip() for line in section.splitlines() if line.startswith("- ")]


class PluginEvalTests(unittest.TestCase):
    def test_every_card_withholds_its_answers_and_grades_them(self) -> None:
        for path in sorted((ROOT / "validation/cases").glob("*.md")):
            with self.subTest(card=path.stem):
                card = path.read_text(encoding="utf-8")
                _, sections = evals.card_sections(card, path.name)
                files = evals.build_case(card, path.stem, 1, 12)
                prompt = files["prompt.md"]
                for heading in evals.WITHHELD_SECTIONS:
                    self.assertNotIn(f"## {heading}", prompt)
                for check in bullets(sections["Required checks"]):
                    self.assertNotIn(check, prompt)
                    self.assertIn(check, yaml.safe_load(files["graders/required-checks.md"].split("---\n")[1])["criteria"])
                for limit in bullets(sections["Must not do"]):
                    self.assertIn(limit, yaml.safe_load(files["graders/restraint.md"].split("---\n")[1])["criteria"])

    def test_a_section_outside_the_withheld_list_stays_in_the_task(self) -> None:
        card = (ROOT / "validation/cases/au-bookkeeping-supported-reconciliation.md").read_text(encoding="utf-8")
        prompt = evals.build_case(card, "au-bookkeeping-supported-reconciliation", 1, 12)["prompt.md"]
        self.assertIn("## Incomplete-input variant", prompt)

    def test_skill_grader_matches_a_target_skill_with_or_without_the_namespace(self) -> None:
        card = (ROOT / "validation/cases/au-payroll-review-master-data-screen.md").read_text(encoding="utf-8")
        grader = evals.build_case(card, "au-payroll-review-master-data-screen", 1, 12)["graders/skill-fired.md"]
        pattern = yaml.safe_load(grader.split("---\n")[1])["input_match"]
        self.assertTrue(re.search(pattern, '{"skill": "australian-accounting-skills:stp-finalisation"}'))
        self.assertTrue(re.search(pattern, '{"skill": "au-payroll-review"}'))
        self.assertFalse(re.search(pattern, '{"skill": "bas-preparation"}'))

    def test_a_card_without_withheld_sections_is_refused(self) -> None:
        card = "---\nid: x\nsynthetic: true\ntarget_skills:\n  - bas-preparation\n---\n\n# X\n\n## Task\n\nDo it.\n"
        with self.assertRaisesRegex(ValueError, "missing section"):
            evals.build_case(card, "x", 1, 12)

    def test_build_refuses_the_repository_and_an_existing_destination(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            evals.build(ROOT / "build-here", 1, 12)
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(ValueError, "already exists"):
                evals.build(Path(folder), 1, 12)

    def test_the_built_copy_leaves_the_cards_behind(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "plugin"
            manifest = evals.build(target, 1, 12)
            self.assertFalse((target / "validation").exists())
            self.assertFalse((target / "tests").exists())
            self.assertTrue((target / ".claude-plugin/plugin.json").is_file())
            self.assertTrue((target / ".claude/skills/bas-preparation/SKILL.md").is_file())
            cases = sorted(path.parent.name for path in (target / "evals").glob("*/prompt.md"))
            self.assertEqual(cases, sorted(manifest["card_sha256"]))  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
