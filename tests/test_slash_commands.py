# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: Apache-2.0
"""Integrity checks for paired Claude Code slash commands under commands/."""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

from test_attribution import PROSE_NOTICE
from test_skill_metadata import (
    DESCRIPTION_LIMIT,
    REPOSITORY,
    SKILLS_DIRECTORY,
    foreign_tax_term_hits,
)

COMMANDS_DIRECTORY = REPOSITORY / "commands"
ALLOWED_COMMAND_FIELDS = {"description", "argument-hint"}
SKILL_LINE = re.compile(r"^(?:Primary|Companion) skill: `([a-z0-9][a-z0-9-]*)`$", re.MULTILINE)
EXPECTED_COMMANDS = {
    "bas-prep",
    "cgt-workpaper",
    "depreciation-check",
    "div7a-review",
    "fbt-scan",
    "individual-return",
    "land-tax-duty",
    "stp-finalise",
    "super-check",
    "trust-distribution",
}


def parse_front_matter(command_file: Path) -> dict[str, str]:
    lines = command_file.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"{command_file.name}: front matter must start with '---'")
    end = lines.index("---", 1)
    fields: dict[str, str] = {}
    for line in lines[1:end]:
        key, sep, raw = line.partition(":")
        key = key.strip()
        value = raw.strip()
        if not sep or key not in ALLOWED_COMMAND_FIELDS or not value:
            raise ValueError(f"{command_file.name}: invalid front-matter line {line!r}")
        if key in fields:
            raise ValueError(f"{command_file.name}: duplicate front-matter key {key!r}")
        if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
            value = value[1:-1]
        fields[key] = value
    return fields


class SlashCommandTests(unittest.TestCase):
    def test_plugin_manifest_declares_commands_directory(self) -> None:
        manifest = json.loads(
            (REPOSITORY / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8")
        )
        self.assertEqual(manifest.get("commands"), "./commands")
        self.assertTrue((REPOSITORY / manifest["commands"]).is_dir())

    def test_expected_top_ten_compliance_commands_exist(self) -> None:
        discovered = {path.stem for path in COMMANDS_DIRECTORY.glob("*.md")}
        self.assertEqual(discovered, EXPECTED_COMMANDS)

    def test_every_command_has_valid_front_matter_skill_target_and_boundaries(self) -> None:
        installed_skills = {path.parent.name for path in SKILLS_DIRECTORY.glob("*/SKILL.md")}
        for path in sorted(COMMANDS_DIRECTORY.glob("*.md")):
            with self.subTest(command=path.stem):
                text = path.read_text(encoding="utf-8")
                meta = parse_front_matter(path)
                self.assertIn("description", meta)
                self.assertIn("argument-hint", meta)
                self.assertLessEqual(len(meta["description"]), DESCRIPTION_LIMIT)
                self.assertIn("$ARGUMENTS", text)
                targets = SKILL_LINE.findall(text)
                self.assertGreaterEqual(len(targets), 1, "each command must name its primary skill")
                for target in targets:
                    self.assertIn(target, installed_skills)
                    self.assertIn(f"`{target}`", text)
                self.assertIn("Prep only: never lodge", text)
                self.assertIn("UNVERIFIED", text)
                self.assertIn("untrusted content", text)
                self.assertIn("workpaper-renderer", text)
                self.assertNotIn("\u2014", text, "no em dashes")
                self.assertEqual(
                    foreign_tax_term_hits(path.relative_to(REPOSITORY).as_posix(), text),
                    [],
                )
                self.assertTrue(text.endswith("\n\n" + PROSE_NOTICE))


if __name__ == "__main__":
    unittest.main()
