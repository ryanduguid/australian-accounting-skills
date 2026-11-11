# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The routing cases `accounting-skills build-plugin-evals` turns into eval cases."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
ROUTING_CASES = ROOT / "validation/routing-cases.yaml"


class RoutingCaseTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cases = yaml.safe_load(ROUTING_CASES.read_text(encoding="utf-8"))
        cls.names = {path.name for path in (ROOT / ".claude/skills").iterdir() if path.is_dir()}

    def test_routing_cases_name_real_skills_and_never_the_expected_one(self) -> None:
        self.assertGreaterEqual(len(self.cases), 20)
        self.assertEqual(len(self.cases), len({case["id"] for case in self.cases}))
        for case in self.cases:
            with self.subTest(case=case["id"]):
                self.assertLessEqual({case["skill"], *case["not"]}, self.names)
                self.assertNotIn(case["skill"], case["not"])
                self.assertFalse([name for name in self.names if name in case["prompt"]])

    def test_every_skill_has_a_routing_case(self) -> None:
        self.assertEqual(set(), self.names - {case["skill"] for case in self.cases})


if __name__ == "__main__":
    unittest.main()
