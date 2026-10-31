# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""Task-only preparation must withhold answers and preserve frozen evidence."""

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from prepare_trial import ROOT, digest, main, prepare, task_input  # noqa: E402


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

    def test_missing_or_symbolic_skill_context_is_refused_before_packet_creation(self) -> None:
        card = ROOT / "validation/cases/month-end-mismatched-period.md"
        _, skills = task_input(card.read_bytes(), card.name)
        for unsafe in ("missing", "folder-link", "file-link"):
            with self.subTest(unsafe=unsafe), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "repository"
                cards = root / "validation/cases"
                cards.mkdir(parents=True)
                (cards / card.name).write_bytes(card.read_bytes())
                for skill in skills:
                    folder = root / ".claude/skills" / skill
                    folder.mkdir(parents=True)
                    if unsafe != "missing":
                        (folder / "SKILL.md").write_text("Synthetic context", encoding="utf-8")
                first = root / ".claude/skills" / skills[0]
                flagged = first if unsafe == "folder-link" else first / "SKILL.md"
                destination = Path(temporary) / "trial"
                message = "missing skill" if unsafe == "missing" else "symbolic links"
                with patch.object(
                    Path, "is_symlink", lambda path: unsafe != "missing" and path == flagged
                ), self.assertRaisesRegex(ValueError, message):
                    prepare(card.stem, destination, "unselected", "unselected", root=root)
                self.assertFalse(destination.exists())

    def test_nested_context_records_files_and_ignores_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "repository"
            cards = root / "validation/cases"
            cards.mkdir(parents=True)
            card = ROOT / "validation/cases/month-end-mismatched-period.md"
            (cards / card.name).write_bytes(card.read_bytes())
            _, skills = task_input(card.read_bytes(), card.name)
            expected = {}
            for skill in skills:
                folder = root / ".claude/skills" / skill
                (folder / "references").mkdir(parents=True)
                for relative in ("SKILL.md", "references/guide.md"):
                    path = folder / relative
                    path.write_bytes(b"Fabricated context\n")
                    expected[path.relative_to(root).as_posix()] = digest(path.read_bytes())
            destination = Path(temporary) / "trial"
            prepare(card.stem, destination, "model", "runtime", root=root)
            context = json.loads((destination / "context.json").read_text(encoding="utf-8"))
            self.assertEqual(context["files"], expected)

    def test_cli_preserves_the_selected_model_and_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            destination = Path(temporary) / "trial"
            arguments = [
                "prepare_trial.py", "month-end-mismatched-period", str(destination),
                "--model", "test-model", "--runtime", "test-runtime",
            ]
            with patch.object(sys, "argv", arguments):
                main()
            context = json.loads((destination / "context.json").read_text(encoding="utf-8"))
            self.assertEqual(context["model"], "test-model")
            self.assertEqual(context["runtime"], "test-runtime")


if __name__ == "__main__":
    unittest.main()
