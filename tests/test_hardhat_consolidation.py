"""Replacement contracts for the Hardhat Ledger skill consolidation."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import unittest


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


class HardhatConsolidationTests(unittest.TestCase):
    def test_transferred_skill_bytes_match_the_reviewed_source_commit(self) -> None:
        for name, expected_hash in TRANSFERRED_SKILL_HASHES.items():
            with self.subTest(skill=name):
                content = (SKILLS / name / "SKILL.md").read_bytes()
                canonical = content.replace(b"\r\n", b"\n")
                self.assertNotIn(b"\r", canonical)
                self.assertEqual(hashlib.sha256(canonical).hexdigest(), expected_hash)

    def test_marketplace_exposes_the_complete_nineteen_skill_inventory(self) -> None:
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
        self.assertEqual(len(discovered), 19)
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


if __name__ == "__main__":
    unittest.main()
