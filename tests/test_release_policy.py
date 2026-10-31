# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""The release workflow is the closed shared skill policy, not a local copy."""

import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


class ReleasePolicyTests(unittest.TestCase):
    def test_verify_calls_the_read_only_shared_skill_policy(self) -> None:
        workflow = yaml.safe_load(
            (ROOT / ".github" / "workflows" / "verify.yml").read_text(
                encoding="utf-8",
            )
        )
        self.assertEqual(workflow["permissions"], {"contents": "read"})
        self.assertIn("shared-conformance", workflow["jobs"])
        self.assertEqual(
            workflow["jobs"]["shared-conformance"],
            {
                "name": "shared conformance",
                "permissions": {"contents": "read"},
                "uses": (
                    "ryanduguid/release-policy/.github/workflows/verify-skills.yml@"
                    "a601f1d8b143f92b0517f709216993660d21f480"
                ),
                "with": {"skills-verification-mode": "subcontractor-accounting-v1"},
            },
        )

    def test_release_workflow_uses_the_shared_skill_policy(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8",
        )
        # The pin is the caller's to set; a re-pin edits release.yml and nothing here.
        self.assertRegex(
            workflow,
            r"(?m)^\s*uses: ryanduguid/release-policy/\.github/workflows/"
            r"release-skills\.yml@[0-9a-f]{40}$",
        )
        self.assertIn("artifact-stem: australian-accounting-skills", workflow)
        self.assertIn(
            "skills-verification-mode: subcontractor-accounting-v1",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
