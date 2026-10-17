"""Task-only preparation must withhold answers and preserve frozen evidence."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_trial import ROOT, digest, prepare, task_input  # noqa: E402


class PrepareTrialTests(unittest.TestCase):
    def test_every_current_card_can_be_prepared_without_its_grading_sections(self) -> None:
        for card in sorted((ROOT / "validation/cases").glob("*.md")):
            with self.subTest(card=card.name):
                task, skills = task_input(card.read_bytes(), card.name)
                self.assertTrue(skills)
                self.assertEqual(task.count(b"## "), 4)
                self.assertNotIn(b"## Required checks", task)
                self.assertNotIn(b"## Must not do", task)
                self.assertNotIn(b"## Source-verification and reviewer boundary", task)

    def test_preparation_binds_exact_bytes_and_never_overwrites(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "trial"
            prepare("month-end-mismatched-period", destination, "unselected", "unselected")
            context = json.loads((destination / "context.json").read_text(encoding="utf-8"))
            self.assertEqual(context["input_sha256"], digest((destination / "input.md").read_bytes()))
            self.assertEqual(context["rubric_sha256"], digest((destination / "rubric.md").read_bytes()))
            for relative, expected in context["files"].items():
                self.assertEqual(expected, digest((ROOT / relative).read_bytes()))
            with self.assertRaisesRegex(ValueError, "already exists"):
                prepare("month-end-mismatched-period", destination, "unselected", "unselected")

    def test_repository_output_and_path_traversal_are_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            prepare("month-end-mismatched-period", ROOT / "trial", "unselected", "unselected")
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaisesRegex(ValueError, "slug"):
                prepare("../README", Path(temporary) / "trial", "unselected", "unselected")

    def test_missing_or_duplicate_sections_are_refused(self) -> None:
        card = ROOT / "validation/cases/month-end-mismatched-period.md"
        text = card.read_bytes()
        with self.assertRaisesRegex(ValueError, "missing task sections"):
            task_input(text.replace(b"## Task", b"## Omitted"), card.name)
        with self.assertRaisesRegex(ValueError, "duplicate section"):
            task_input(text + b"\n## Task\nInjected answer\n", card.name)

    def test_credential_named_context_is_refused_before_packet_creation(self) -> None:
        for name in ("fixture.key", "fixture.KEY", ".ENV", ".env.local", "fixture.PEM"):
            with self.subTest(name=name), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "repository"
                cards = root / "validation/cases"
                cards.mkdir(parents=True)
                card = ROOT / "validation/cases/month-end-mismatched-period.md"
                (cards / card.name).write_bytes(card.read_bytes())
                _, skills = task_input(card.read_bytes(), card.name)
                for skill in skills:
                    folder = root / ".claude/skills" / skill
                    folder.mkdir(parents=True)
                    (folder / "SKILL.md").write_text("Synthetic test context", encoding="utf-8")
                    (folder / name).write_text("Synthetic non-secret sentinel", encoding="utf-8")
                destination = Path(temporary) / "trial"
                with self.assertRaisesRegex(ValueError, "credential files"):
                    prepare(card.stem, destination, "unselected", "unselected", root=root)
                self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
