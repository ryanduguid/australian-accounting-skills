"""Every contributor guide must list the checks CI actually gates on."""

from __future__ import annotations

import unittest
from pathlib import Path

import yaml

REPOSITORY = Path(__file__).resolve().parents[1]
VERIFY_WORKFLOW = REPOSITORY / ".github" / "workflows" / "verify.yml"
PRE_COMMIT_CONFIG = REPOSITORY / ".pre-commit-config.yaml"
CONTRIBUTOR_GUIDES = ("AGENTS.md", "CONTRIBUTING.md")

# Which pre-commit hook covers each CI gate. A hook rarely spells its gate
# the same way: the Ruff and mypy mirrors run their own entry points, so a
# substring search would report drift that is not there and miss drift that
# is. Naming the pairs makes a new gate with no local hook fail here.
GATE_HOOKS = {
    "python -m ruff check .": "ruff-check",
    "python -m mypy": "mypy",
    "python -m unittest discover -s tests -v": "unittest",
    "python scripts/validate_validation.py": "validation-pack",
    "python tests/verify_skills_cli.py": "skills-cli-discovery",
    "python scripts/build_coverage.py --check": "coverage-matrix",
}


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
        self.assertEqual(len(gates), 6)
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


    def test_every_ci_gate_has_a_pre_commit_hook(self) -> None:
        """A gate that only runs after a push is a gate found too late.

        The local config and the workflow are two lists of the same checks, and
        nothing stops one from gaining an entry the other never hears about.
        """
        config = yaml.safe_load(PRE_COMMIT_CONFIG.read_text(encoding="utf-8"))
        hook_ids = {
            hook["id"] for repo in config["repos"] for hook in repo["hooks"]
        }

        for gate in ci_gate_commands():
            with self.subTest(gate=gate):
                hook = GATE_HOOKS.get(gate)
                self.assertIsNotNone(
                    hook,
                    f"verify.yml gates on {gate!r} with no entry in GATE_HOOKS, so nobody "
                    "has said which pre-commit hook runs it locally",
                )
                self.assertIn(
                    hook,
                    hook_ids,
                    f"{gate!r} maps to pre-commit hook {hook!r}, which is not configured",
                )

    def test_the_gate_map_describes_gates_that_still_exist(self) -> None:
        """A mapping left behind after a gate is removed is a false assurance."""
        self.assertEqual(set(GATE_HOOKS), set(ci_gate_commands()))

    def test_secret_scanning_runs_locally_and_in_ci(self) -> None:
        """Gitleaks is not a `run:` step, so the gate map cannot reach it."""
        workflow = yaml.safe_load(VERIFY_WORKFLOW.read_text(encoding="utf-8"))
        actions = [
            step.get("uses", "")
            for job in workflow["jobs"].values()
            if isinstance(job, dict)
            for step in job.get("steps", [])
        ]
        self.assertTrue(
            any("gitleaks" in action for action in actions),
            "verify.yml must scan for secrets and client identifiers",
        )

        config = yaml.safe_load(PRE_COMMIT_CONFIG.read_text(encoding="utf-8"))
        hook_ids = {hook["id"] for repo in config["repos"] for hook in repo["hooks"]}
        self.assertIn("gitleaks", hook_ids)
        self.assertTrue((REPOSITORY / ".gitleaks.toml").is_file())


if __name__ == "__main__":
    unittest.main()
