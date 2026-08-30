"""Every contributor guide must list the checks CI actually gates on."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml


REPOSITORY = Path(__file__).resolve().parents[1]
VERIFY_WORKFLOW = REPOSITORY / ".github" / "workflows" / "verify.yml"
CONTRIBUTOR_GUIDES = ("CLAUDE.md", "AGENTS.md", "CONTRIBUTING.md")


def ci_gate_commands() -> list[str]:
    """Return the verify job's gate commands, skipping dependency setup."""
    workflow = yaml.safe_load(VERIFY_WORKFLOW.read_text(encoding="utf-8"))
    steps = workflow["jobs"]["verify"]["steps"]
    return [
        " ".join(step["run"].split())
        for step in steps
        if str(step.get("name", "")).startswith("Verify")
    ]


class ContributorCheckTests(unittest.TestCase):
    def test_every_ci_gate_appears_in_every_contributor_guide(self) -> None:
        """A gate missing from the local list fails only after hand-off."""
        gates = ci_gate_commands()
        self.assertGreaterEqual(len(gates), 1, "verify.yml must run at least one gate")

        for guide in CONTRIBUTOR_GUIDES:
            text = (REPOSITORY / guide).read_text(encoding="utf-8")
            for gate in gates:
                with self.subTest(guide=guide, gate=gate):
                    self.assertIn(
                        gate,
                        text,
                        f"{guide} omits a check .github/workflows/verify.yml gates on",
                    )


if __name__ == "__main__":
    unittest.main()
