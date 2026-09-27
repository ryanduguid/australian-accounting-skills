"""Calculator safeguard contracts for skills that use a calculator."""

from __future__ import annotations

import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS = REPOSITORY / ".claude" / "skills"
class CalculatorSafeguardTests(unittest.TestCase):
    """A skill that uses a calculator must carry the calculator boundaries.

    Neither plugin manifest ships `.claude/rules/`, so a consumer installing
    one skill gets the skill and nothing else. AGENTS.md already requires each
    SKILL.md to be self-contained enough for individual installation; this
    checks it for the rules a calculator-using skill depends on, which is the
    place the gap actually mattered.
    """

    #: Each safeguard, and a phrase the skill has to carry in its own words.
    #: Phrases, not the rule text, because a skill states a rule in its own
    #: workflow's terms and copying the rule verbatim would be worse writing.
    REQUIRED_PHRASES = {
        "local first (rule 7)": ("never as a fallback when a local tool refuses",),
        "supported periods (rule 8)": ("supports the reporting month",),
        "evidence captured (rule 9)": ("Record what it consumed",),
        "labels stay the engine's (rule 10)": ("own labels as its own",),
    }

    def test_no_manifest_ships_the_shared_rules(self) -> None:
        # The premise of the test below. If a manifest starts shipping the
        # rules, this fails and the requirement can be relaxed deliberately.
        for manifest in (
            REPOSITORY / ".claude-plugin" / "plugin.json",
            REPOSITORY / ".codex-plugin" / "plugin.json",
        ):
            text = manifest.read_text(encoding="utf-8")
            self.assertNotIn(".claude/rules", text, f"{manifest.name} now ships the rules")

    def test_a_skill_that_uses_a_calculator_carries_the_calculator_boundaries(self) -> None:
        skills = sorted((REPOSITORY / ".claude" / "skills").iterdir())
        using = [
            path for path in skills
            if path.is_dir() and "calculator" in (path / "SKILL.md").read_text(
                encoding="utf-8",
            ).lower()
        ]
        self.assertTrue(using, "no skill mentions a calculator; the check has lost its subject")
        for path in using:
            text = (path / "SKILL.md").read_text(encoding="utf-8")
            for safeguard, phrases in self.REQUIRED_PHRASES.items():
                with self.subTest(skill=path.name, safeguard=safeguard):
                    self.assertTrue(
                        any(phrase in text for phrase in phrases),
                        f"{path.name}/SKILL.md does not carry {safeguard}",
                    )


if __name__ == "__main__":
    unittest.main()
