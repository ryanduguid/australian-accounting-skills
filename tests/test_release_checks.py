"""Require the reviewed component checks before a release can publish."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
POLICY = "87767ec809dc7f77bcd45808219adaf67841ae7b"
# These are component jobs from successful main-branch runs, never skip-tolerant
# aggregate gates. Review the list when a component's CI contract changes.
REQUIRED = {
    "release.yml": [
        ".github/workflows/no-ai-attribution.yml: Attribution policy / Attribution policy runner",
        ".github/workflows/verify.yml: lint",
        ".github/workflows/verify.yml: secrets",
        ".github/workflows/verify.yml: shared conformance / verify skill-pack consumer",
        ".github/workflows/verify.yml: verify (3.10)",
        ".github/workflows/verify.yml: verify (3.12)",
        ".github/workflows/verify.yml: verify (3.13)",
        ".github/workflows/verify.yml: verify (3.14)"
    ]
}


class ReleaseChecksTests(unittest.TestCase):
    def test_every_release_caller_requires_its_component_checks(self) -> None:
        workflows = ROOT / ".github" / "workflows"
        callers = sorted(
            path.name for path in workflows.glob("release*") if path.suffix in {".yml", ".yaml"}
        )
        self.assertEqual(callers, sorted(REQUIRED))
        for filename, expected in REQUIRED.items():
            with self.subTest(workflow=filename):
                text = (workflows / filename).read_text(encoding="utf-8")
                job = text.split("\n  release:\n", 1)[1].split("\n  pypi:", 1)[0]
                self.assertRegex(
                    job,
                    r"(?m)^    uses: ryanduguid/release-policy/\.github/workflows/"
                    r"release-(?:python|archive|skills)\.yml@" + POLICY + r"$",
                )
                permissions = job.split("    permissions:\n", 1)[1].split("    uses:", 1)[0]
                self.assertRegex(permissions, r"(?m)^      actions: read(?: #.*)?$")
                match = re.search(
                    r"^      required-checks: \|\n((?:        [^\n]*\n)+)", job, re.MULTILINE,
                )
                self.assertIsNotNone(match, "missing explicit component checks")
                assert match is not None
                actual = [line.strip() for line in match.group(1).splitlines()]
                self.assertCountEqual(actual, expected)
                self.assertEqual(len(actual), len(set(actual)), "duplicate check selector")
                for selector in actual:
                    path, name = selector.split(": ", 1)
                    self.assertTrue((ROOT / path).is_file(), path)
                    self.assertFalse(name.endswith(" / gates"), name)


if __name__ == "__main__":
    unittest.main()
