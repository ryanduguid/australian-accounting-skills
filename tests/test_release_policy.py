"""The release workflow is the closed shared skill policy, not a local copy."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleasePolicyTests(unittest.TestCase):
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
