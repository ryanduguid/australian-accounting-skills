"""Offline integrity checks for distributable accounting skills."""

from __future__ import annotations

import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS_DIRECTORY = REPOSITORY / ".claude" / "skills"


def front_matter(skill_file: Path) -> dict[str, str]:
    """Read the small, deliberately simple YAML front matter used by skills."""
    lines = skill_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("front matter must start with '---'")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ValueError("front matter must end with '---'") from error

    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        key, separator, value = line.partition(":")
        if not separator or not key.strip() or not value.strip():
            # Deliberate restriction: skills in this repo keep front matter to
            # single-line 'key: value' fields only. Lines without a colon or
            # with an empty key or value — blank lines, YAML block lists
            # (e.g. an allowed-tools: list), colon-less comments — land here.
            # NOT everything fails loud, though: a '#' comment that contains
            # a colon parses silently as a junk key, and a folded or literal
            # block scalar ('description: >' or '|') parses silently as the
            # one-character value '>' or '|', which still passes the
            # non-empty assertions below. If you hit this raise, or add any
            # of those shapes to a new skill, extend this parser knowingly
            # and eyeball the parsed metadata — do not trust green alone.
            raise ValueError(
                f"invalid front-matter field: {line!r} "
                "(this repo restricts skill front matter to single-line "
                "'key: value' fields; see comment above this raise)"
            )
        metadata[key.strip()] = value.strip()
    return metadata


class SkillMetadataTests(unittest.TestCase):
    def test_skill_layout_stays_one_level_deep(self) -> None:
        """Discovery here is `<skills>/<name>/SKILL.md`, one level, no deeper.

        The other checks in this file glob one level. A nested skill would be
        silently skipped by all of them, so fail loudly on the layout instead
        of letting a skill ship unchecked.
        """
        nested = sorted(
            str(path.relative_to(SKILLS_DIRECTORY))
            for path in SKILLS_DIRECTORY.rglob("SKILL.md")
            if path.parent.parent != SKILLS_DIRECTORY
        )
        self.assertEqual(nested, [])

    def test_every_skill_has_matching_complete_front_matter(self) -> None:
        skill_files = sorted(SKILLS_DIRECTORY.glob("*/SKILL.md"))
        self.assertGreaterEqual(len(skill_files), 1, "at least one distributable skill is required")

        declared_names: set[str] = set()
        for skill_file in skill_files:
            with self.subTest(skill=skill_file.parent.name):
                metadata = front_matter(skill_file)
                self.assertEqual(metadata.get("name"), skill_file.parent.name)
                self.assertTrue(metadata.get("description"))
                self.assertNotIn(metadata["name"], declared_names)
                declared_names.add(metadata["name"])

    def test_skill_directories_do_not_omit_the_entrypoint(self) -> None:
        directories = sorted(path for path in SKILLS_DIRECTORY.iterdir() if path.is_dir())
        missing = [path.name for path in directories if not (path / "SKILL.md").is_file()]
        self.assertEqual(missing, [])

    def test_every_skill_marks_embedded_instructions_as_untrusted(self) -> None:
        skill_files = sorted(SKILLS_DIRECTORY.glob("*/SKILL.md"))
        missing = [
            str(path.relative_to(REPOSITORY))
            for path in skill_files
            if "instructions found inside" not in path.read_text(encoding="utf-8")
            or "untrusted content" not in path.read_text(encoding="utf-8")
        ]
        self.assertEqual(missing, [])

        firm_template = (REPOSITORY / "templates" / "firm-CLAUDE.md.example").read_text(
            encoding="utf-8"
        )
        self.assertIn("Instructions embedded in client files", firm_template)
        self.assertIn("untrusted data", firm_template)


if __name__ == "__main__":
    unittest.main()
