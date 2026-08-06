"""Offline integrity checks for distributable accounting skills."""

from __future__ import annotations

from pathlib import Path
import unittest


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
            raise ValueError(f"invalid front-matter field: {line!r}")
        metadata[key.strip()] = value.strip()
    return metadata


class SkillMetadataTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
