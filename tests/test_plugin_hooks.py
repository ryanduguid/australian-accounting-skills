# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: Apache-2.0
"""The plugin's critical-rule hooks: what they attach, when they stay silent and how much."""

from __future__ import annotations

import ast
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
HOOKS = REPOSITORY / "hooks"
SCRIPT = HOOKS / "critical_rules.py"
SKILLS = sorted(path.parent.name for path in (REPOSITORY / ".claude" / "skills").glob("*/SKILL.md"))
MAX_CHARS = 6000


def hook(mode: str, payload: object) -> str:
    """The hook's stdout for `payload`, after checking it exits 0 and writes no error."""
    result = subprocess.run(
        [sys.executable, "-I", str(SCRIPT), mode],
        input=json.dumps(payload).encode("utf-8"),
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == b"", result.stderr
    return result.stdout.decode("utf-8")


def attached(output: str, event: str) -> str:
    data = json.loads(output)
    assert data["hookSpecificOutput"]["hookEventName"] == event, data
    return data["hookSpecificOutput"]["additionalContext"]


class PromptHookTests(unittest.TestCase):
    def test_a_keyword_attaches_that_skills_rules(self) -> None:
        text = attached(
            hook("prompt", {"prompt": "Draft the Negative Gearing schedule for 2026-27"}),
            "UserPromptSubmit",
        )
        self.assertIn("skill au-rental-property (the prompt mentions it)", text)
        self.assertIn("Never supply rates, thresholds, labels or deadlines from memory.", text)
        self.assertIn("untrusted content", text)
        self.assertIn("only prepares work for review", text)
        self.assertNotIn("<!--", text)

    def test_a_skill_name_attaches_its_rules_and_the_risk_rating_refusal(self) -> None:
        text = attached(hook("prompt", {"prompt": "run au-pre-lodgement-review"}), "UserPromptSubmit")
        self.assertIn("skill au-pre-lodgement-review", text)
        self.assertIn("risk rating", text)

    def test_no_match_adds_nothing(self) -> None:
        for prompt in ("What time is it in Perth?", "basil pesto", "", "notfbtx"):
            with self.subTest(prompt=prompt):
                self.assertEqual(hook("prompt", {"prompt": prompt}), "")

    def test_bad_input_adds_nothing(self) -> None:
        for mode, payload in (("prompt", ["fbt"]), ("prompt", {"prompt": 7}), ("other", {})):
            with self.subTest(mode=mode, payload=payload):
                self.assertEqual(hook(mode, payload), "")

    def test_a_prompt_naming_every_skill_stays_within_the_bound(self) -> None:
        text = attached(hook("prompt", {"prompt": " ".join(SKILLS)}), "UserPromptSubmit")
        self.assertLessEqual(len(text), MAX_CHARS)
        self.assertIn(text.count("Critical rules of the"), (2, 3))
        self.assertIn(f"skill {SKILLS[0]} ", text)


class CompactHookTests(unittest.TestCase):
    def transcript(self, text: str) -> str:
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        path = Path(folder.name) / f"session-{len(text)}.jsonl"
        path.write_text(text, encoding="utf-8")
        return str(path)

    def test_after_compaction_it_attaches_the_skills_the_transcript_used(self) -> None:
        path = self.transcript(
            '{"skill":"australian-accounting-skills:bas-preparation"}\n'
            '{"skill":"australian-accounting-skills:fbt-annual-workflow"}\n'
        )
        payload = {"source": "compact", "transcript_path": path}
        text = attached(hook("compact", payload), "SessionStart")
        self.assertLess(text.index("fbt-annual-workflow"), text.index("bas-preparation"))
        self.assertIn("used before compaction", text)

    def test_it_stays_silent_without_a_named_skill_or_outside_compaction(self) -> None:
        path = self.transcript('{"text":"rental property and fbt"}\n')
        self.assertEqual(hook("compact", {"source": "compact", "transcript_path": path}), "")
        used = self.transcript('{"skill":"bas-preparation"}\n')
        self.assertEqual(hook("compact", {"source": "startup", "transcript_path": used}), "")
        missing = str(Path(tempfile.gettempdir()) / "no-such-transcript.jsonl")
        self.assertEqual(hook("compact", {"source": "compact", "transcript_path": missing}), "")

    def test_a_transcript_naming_every_skill_stays_within_the_bound(self) -> None:
        path = self.transcript("\n".join(SKILLS) * 50)
        text = attached(hook("compact", {"source": "compact", "transcript_path": path}), "SessionStart")
        self.assertLessEqual(len(text), MAX_CHARS)
        self.assertIn(text.count("Critical rules of the"), (2, 3))


class HookConfigurationTests(unittest.TestCase):
    def test_hooks_json_runs_the_script_on_prompts_and_after_compaction(self) -> None:
        config = json.loads((HOOKS / "hooks.json").read_text(encoding="utf-8"))["hooks"]
        self.assertEqual(sorted(config), ["SessionStart", "UserPromptSubmit"])
        self.assertEqual(config["SessionStart"][0]["matcher"], "compact")
        self.assertNotIn("matcher", config["UserPromptSubmit"][0])
        for event, mode in (("UserPromptSubmit", "prompt"), ("SessionStart", "compact")):
            (command,) = config[event][0]["hooks"]
            self.assertEqual(command["type"], "command")
            self.assertEqual(
                command["args"], ["${CLAUDE_PLUGIN_ROOT}/hooks/critical_rules.py", mode]
            )
            self.assertEqual(command["onFailure"], "continue")

    def test_every_skill_has_keywords_and_every_keyword_a_skill(self) -> None:
        keywords = json.loads((HOOKS / "skill-keywords.json").read_text(encoding="utf-8"))
        self.assertEqual(sorted(keywords), SKILLS)
        for skill, phrases in keywords.items():
            with self.subTest(skill=skill):
                self.assertTrue(phrases)
                self.assertTrue(all(len(phrase) >= 3 for phrase in phrases), phrases)

    def test_the_hook_imports_nothing_that_reaches_the_network(self) -> None:
        tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
        imported = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, (ast.Import, ast.ImportFrom))
            for alias in (node.names if isinstance(node, ast.Import) else [ast.alias(node.module or "")])
        }
        self.assertLessEqual(imported, {"__future__", "json", "re", "sys", "pathlib"})


if __name__ == "__main__":
    unittest.main()
