"""Every contributor guide must list the checks CI actually gates on."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

REPOSITORY = Path(__file__).resolve().parents[1]
VERIFY_WORKFLOW = REPOSITORY / ".github" / "workflows" / "verify.yml"
CONTRIBUTOR_GUIDES = ("AGENTS.md", "CONTRIBUTING.md")


GATE_JOBS = ("lint", "verify")
SETUP_STEP_PREFIXES = ("Check out", "Set up", "Install")


def ci_gate_commands() -> list[str]:
    """Return every gate command from the lint and verify jobs, skipping setup steps."""
    workflow = yaml.safe_load(VERIFY_WORKFLOW.read_text(encoding="utf-8"))
    commands: list[str] = []
    for job in GATE_JOBS:
        for step in workflow["jobs"][job]["steps"]:
            if "run" not in step:
                continue
            if str(step.get("name", "")).startswith(SETUP_STEP_PREFIXES):
                continue
            commands.append(" ".join(step["run"].split()))
    return commands


class ContributorCheckTests(unittest.TestCase):
    def test_agents_is_the_shared_guide_and_claude_imports_it(self) -> None:
        """One substantive guide prevents cross-runtime instruction drift."""
        agents = (REPOSITORY / "AGENTS.md").read_text(encoding="utf-8")
        claude = (REPOSITORY / "CLAUDE.md").read_text(encoding="utf-8")

        for section in (
            "## What this repository is",
            "## Hard boundary",
            "## Scope and data",
            "## Accuracy and professional boundaries",
            "## Where things live",
            "## Checks before opening a pull request",
            "## Maintaining skills",
            "## Writing rules",
            "## Before hand-off",
        ):
            with self.subTest(section=section):
                self.assertIn(section, agents)

        self.assertIn(claude, ("@AGENTS.md", "@AGENTS.md\n"))

    def test_gate_discovery_covers_the_lint_job_and_skips_setup(self) -> None:
        """A lint command dropped from a guide must fail here, not after hand-off."""
        gates = ci_gate_commands()
        self.assertIn("python -m mypy", gates)
        self.assertEqual(len(gates), 5)
        for gate in gates:
            with self.subTest(gate=gate):
                self.assertNotIn("pip install", gate)

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
