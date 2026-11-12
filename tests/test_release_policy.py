# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""The release workflow is the closed shared skill policy, not a local copy."""

import unittest
from pathlib import Path

import yaml

from test_markdown_links import slug
from test_skill_metadata import RELEASED_INVENTORIES

ROOT = Path(__file__).resolve().parents[1]


def missing_correction_notice(readme: str, notes: str, published: str) -> str | None:
    """Name the link a README lacks when the release notes correct the latest release.

    Only corrections of the latest published release need the notice above
    the install commands; older ones stay in the README's collapsed section.
    """
    heading = f"Corrections since v{published}"
    if f"\n## {heading}\n" not in f"\n{notes}":
        return None
    link = f"RELEASE_NOTES.md#{slug(heading)}"
    before_install, found, _ = readme.partition("\n## Install\n")
    if not found or link not in before_install:
        return link
    return None


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
                    "ca5492bd09693be9e1fd47d980e2740ef8daf023"
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


class CorrectionNoticeTests(unittest.TestCase):
    def test_readme_flags_corrections_of_the_latest_release_above_install(self) -> None:
        published = max(RELEASED_INVENTORIES, key=lambda value: tuple(map(int, value.split("."))))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        notes = (ROOT / "RELEASE_NOTES.md").read_text(encoding="utf-8")
        self.assertIsNone(missing_correction_notice(readme, notes, published))
        releasing = " ".join((ROOT / "RELEASING.md").read_text(encoding="utf-8").split())
        self.assertIn("put a short notice above the README's `## Install` heading", releasing)
        # The check keys on the latest published release, so it stops applying once
        # step 4 records the new one; the step must say so.
        self.assertIn(
            "the test requires the notice only until step 4 adds the new version to "
            "`RELEASED_INVENTORIES`",
            releasing,
        )
        self.assertIn("no test checks the removal", releasing)

    def test_a_correction_of_the_latest_release_needs_the_notice(self) -> None:
        notes = "# v1.1.0\n\n## Corrections since v1.0.0\n\n- A figure.\n"
        link = "RELEASE_NOTES.md#corrections-since-v100"
        hidden = f"# Pack\n\n## Install\n\n<details>[Corrections]({link})</details>\n"
        shown = f"# Pack\n\n[Corrections to v1.0.0]({link})\n\n## Install\n"
        self.assertEqual(missing_correction_notice(hidden, notes, "1.0.0"), link)
        self.assertIsNone(missing_correction_notice(shown, notes, "1.0.0"))
        # Corrections of an older release do not call for the notice.
        self.assertIsNone(missing_correction_notice(hidden, notes, "1.1.0"))


if __name__ == "__main__":
    unittest.main()
