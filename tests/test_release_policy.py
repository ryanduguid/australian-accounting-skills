"""The release workflow is the shared archive policy, not a local copy."""

from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ReleasePolicyTests(unittest.TestCase):
    def test_release_workflow_uses_the_shared_archive_policy(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8",
        )
        self.assertIn(
            "ryanduguid/release-policy/.github/workflows/release-archive.yml@"
            "47480b782926179b621ec1c6643ef88c80fc8fd4",
            workflow,
        )
        self.assertIn("artifact-stem: australian-accounting-skills", workflow)


if __name__ == "__main__":
    unittest.main()
