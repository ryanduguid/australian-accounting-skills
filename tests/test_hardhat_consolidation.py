"""Replacement contracts for the Hardhat Ledger skill consolidation."""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS = REPOSITORY / ".claude" / "skills"
SOURCE_COMMIT = "eb3b8a6ba47dfcdc05cea434f2f6a7dba82f96ef"
TRANSFERRED_SKILL_HASHES = {
    "coal-lsl-levy": "c0330c9ec817435c731872452e5984040c89b16a5ad432193b0135ba1a322c23",
    "contract-cost-tracking": "c385d832d1bfc00bd4e4eed12c2b86740047049f50cfcf11325a5adbdc0e1690",
    "contracting-exports": "bcfec0dd235e2940eb2f0a5c447f097bc2257d85cc723c1151b4c1885aef929e",
    "contractor-super-tpar": "47ba8863485798b80cc25d1fe7485c58918b853032bc81e1f4128cce39e1eece",
    "fuel-tax-credits": "a2721d3afc420b17a4a13503b046870564f1f8e6bc0700ed144376ace2ae99be",
    "payroll-tax-contractors": "1e6e58397fb139c4c3d7320f3c3cf38e86f632517921e1942447a70189bc9108",
    "plant-and-equipment-costing": "7718b8226306e3ec6c546758a2839ee04c6ea964e550fdf83586e4081cac80af",
    "progress-claim-preparation": "9d4b7bbf3789cab8c4e3e3686b7194eb6a7ec9f7604191151c4d5593917233e4",
    "retention-schedule": "84e23a7a268391cb352c3d1f36d7bb5628690b6aa390a0492cfc81106832373c",
    "wip-over-under-billing": "c1aa5c432c41a5ac79ab384ce5ab7e472a555b6825faa01536e6e01aae8270b1",
}

# Destination-owned changes are recorded separately from the original transfer.
AMENDED_SKILL_HASHES = {
    "coal-lsl-levy": "424302826e8721dea1e5fbc92880e5d944f09b334fcf3e0166e4074334cc185a",
    "contract-cost-tracking": "7e8ee6f47caa283fa7fa0d282c43b902600fe87f9e6237ad15f2daab348a7957",
    "contracting-exports": "ad35a00cd2f093463f09eab096d032ed0de1e0a863686e170426d59ef0d2d7ef",
    "contractor-super-tpar": "f88a46cf4f6800d729f30b2e2499997b3a34bdde14e2b770d8d6ceed565a9a0f",
    "fuel-tax-credits": "d40287358d80f67ec75d6effebcccfaa1f99643e0ce2d92916356d0827e22916",
    "payroll-tax-contractors": "f3e69f7c074f5250172205bd8c662a9810e8e0242f0da005920b67a70e642d1f",
    "plant-and-equipment-costing": "11ce902d769e0b8be65d81a23dd6fdd7f6ed453070208240bf91a066877676b8",
    "progress-claim-preparation": "ffd4afb78b698ad20254729600b9b8c3db7bb36716fc53c6b22116526b289e00",
    "retention-schedule": "de0f9b9a42fc00032b5aee41d71d9171ddef82fa2e7705d13c6f3828f368bc3f",
    "wip-over-under-billing": "ce6d130bb924904edd617e06371d15b07104672333467cf364953cf01116bbe5",
}


class HardhatConsolidationTests(unittest.TestCase):
    def test_skill_bytes_match_the_transfer_or_documented_amendment(self) -> None:
        record = (REPOSITORY / "docs" / "HARDHAT-CONSOLIDATION.md").read_text(
            encoding="utf-8"
        )
        for name, expected_hash in TRANSFERRED_SKILL_HASHES.items():
            with self.subTest(skill=name):
                self.assertIn(expected_hash, record)
                expected_hash = AMENDED_SKILL_HASHES.get(name, expected_hash)
                self.assertIn(expected_hash, record)
                content = (SKILLS / name / "SKILL.md").read_bytes()
                canonical = content.replace(b"\r\n", b"\n")
                self.assertNotIn(b"\r", canonical)
                self.assertEqual(hashlib.sha256(canonical).hexdigest(), expected_hash)

    def test_marketplace_exposes_the_complete_fifty_skill_inventory(self) -> None:
        marketplace = json.loads(
            (REPOSITORY / ".claude-plugin" / "marketplace.json").read_text(
                encoding="utf-8"
            )
        )
        declared = {
            Path(item).name for item in marketplace["plugins"][0]["skills"]
        }
        discovered = {
            path.parent.name for path in SKILLS.glob("*/SKILL.md")
        }
        self.assertEqual(declared, discovered)
        self.assertEqual(len(discovered), 50)
        self.assertLessEqual(set(TRANSFERRED_SKILL_HASHES), discovered)

    def test_transition_record_preserves_replace_then_remove_order(self) -> None:
        record = (REPOSITORY / "docs" / "HARDHAT-CONSOLIDATION.md").read_text(
            encoding="utf-8"
        )
        self.assertIn(SOURCE_COMMIT, record)
        self.assertIn("uninstall", record.lower())
        self.assertIn("before installing", record.lower())
        self.assertIn("rollback", record.lower())
        self.assertIn("v0.1.5", record)
        self.assertNotIn("install both", record.lower())




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
