"""The release workflow is the closed shared skill policy, not a local copy."""

from pathlib import Path
import unittest

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
                    "8b4de1ed339f1358b5f3e850b63412d8717d01da"
                ),
                "with": {"skills-verification-mode": "subcontractor-accounting-v1"},
            },
        )

    def test_release_workflow_uses_the_shared_skill_policy(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8",
        )
        self.assertIn(
            "ryanduguid/release-policy/.github/workflows/release-skills.yml@"
            "8b4de1ed339f1358b5f3e850b63412d8717d01da",
            workflow,
        )
        self.assertIn("artifact-stem: australian-accounting-skills", workflow)
        self.assertIn(
            "skills-verification-mode: subcontractor-accounting-v1",
            workflow,
        )


if __name__ == "__main__":
    unittest.main()
