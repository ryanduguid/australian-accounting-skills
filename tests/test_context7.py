# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: Apache-2.0
"""Validate context7.json structure, bounds and indexed directories offline."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "context7.json"
SCHEMA_URL = "https://context7.com/schema/context7.json"
ALLOWED_KEYS = {
    "$schema",
    "projectTitle",
    "description",
    "branch",
    "folders",
    "excludeFolders",
    "excludeFiles",
    "includeExtensions",
    "rules",
    "disallow",
    "redirect",
    "previousVersions",
    "url",
    "public_key",
}


class Context7Tests(unittest.TestCase):
    def test_context7_config_matches_schema_bounds(self) -> None:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        self.assertIsInstance(config, dict)
        self.assertLessEqual(set(config), ALLOWED_KEYS)
        self.assertEqual(config.get("$schema"), SCHEMA_URL)

        title = config.get("projectTitle")
        self.assertIsInstance(title, str)
        self.assertTrue(1 <= len(title) <= 100)

        description = config.get("description")
        self.assertIsInstance(description, str)
        self.assertTrue(10 <= len(description) <= 500)

        folders = config.get("folders", [])
        self.assertIsInstance(folders, list)
        self.assertTrue(1 <= len(folders) <= 50)
        self.assertEqual(len(folders), len(set(folders)))
        for folder in folders:
            self.assertIsInstance(folder, str)
            self.assertTrue((ROOT / folder).is_dir(), folder)

        rules = config.get("rules", [])
        self.assertIsInstance(rules, list)
        self.assertTrue(1 <= len(rules) <= 50)
        for rule in rules:
            self.assertIsInstance(rule, str)
            self.assertTrue(1 <= len(rule) <= 255)


if __name__ == "__main__":
    unittest.main()
