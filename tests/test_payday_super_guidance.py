"""Contract checks for Payday Super guidance used by maintained skills."""

from __future__ import annotations

import re
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
SKILL_FILES = {
    "stp-finalisation": REPOSITORY / ".claude" / "skills" / "stp-finalisation" / "SKILL.md",
    "month-end-close": REPOSITORY / ".claude" / "skills" / "month-end-close" / "SKILL.md",
    "cashflow-forecast-13week": (
        REPOSITORY / ".claude" / "skills" / "cashflow-forecast-13week" / "SKILL.md"
    ),
}
USE_TIME_RECORDS = {
    "stp-finalisation": "finalisation workpaper",
    "month-end-close": "close pack",
    "cashflow-forecast-13week": "forecast source log",
}

ATO_PAYDAY_SUPER = "https://softwaredevelopers.ato.gov.au/PaydaySuper"
PAYDAY_SUPER_ACT = "https://www.legislation.gov.au/C2025A00057/asmade/text"
SGA_REGULATIONS = "https://www.legislation.gov.au/F2018L01289/latest/text"


def compact(text: str) -> str:
    """Normalise Markdown whitespace while retaining its substantive wording."""
    return re.sub(r"\s+", " ", text).strip().lower()


class PaydaySuperGuidanceTests(unittest.TestCase):
    def assert_use_time_evidence_contract(self, skill: str, content: str) -> None:
        """Require one complete, bound at-use instruction for a maintained skill."""
        paragraphs = [
            paragraph.strip()
            for paragraph in re.split(r"\r?\n[ \t]*\r?\n", content)
            if paragraph.strip()
        ]
        at_use_paragraphs = [
            paragraph for paragraph in paragraphs if paragraph.startswith("At use time,")
        ]
        self.assertEqual(
            len(at_use_paragraphs),
            1,
            "each skill must contain exactly one At use time paragraph",
        )
        paragraph = at_use_paragraphs[0]
        artefact = USE_TIME_RECORDS[skill]

        self.assertIn("before applying this control", paragraph)
        self.assertIn("reverify the current Payday Super timing", paragraph)
        self.assertIn(
            f"[ATO Payday Super source]({ATO_PAYDAY_SUPER})",
            paragraph,
            "the at-use paragraph must contain the exact ATO Payday Super URL",
        )
        self.assertIn(
            f"In the {artefact}, record",
            paragraph,
            f"the at-use paragraph must bind the recording action to the {artefact}",
        )
        self.assertIn("direct URL", paragraph)
        self.assertIn("access/check date", paragraph)
        self.assertIn("relevant payday or period", paragraph)
        self.assertIn("precise timing fact relied on", paragraph)
        self.assertIn("if the source is unavailable", paragraph)
        self.assertIn("mark it unverified", paragraph)
        self.assertIn("`UNKNOWN`", paragraph)

    def test_each_skill_checks_allowable_period_before_a_late_classification(self) -> None:
        """A universal seven-day shortcut must not drive a late or SGC outcome."""
        for skill, path in SKILL_FILES.items():
            content = compact(path.read_text(encoding="utf-8"))
            with self.subTest(skill=skill):
                self.assertRegex(content, r"ordinary.{0,80}(?:seven|7)[ -]business-day")
                self.assertIn(
                    "by the end of the seventh business day after the payday",
                    content,
                )
                self.assertIn("allowable longer period", content)
                self.assertRegex(
                    content,
                    r"check.{0,160}allowable longer period.{0,220}before.{0,120}(?:late|sgc)",
                )
                self.assertRegex(
                    content,
                    r"(?:missing|insufficient|unproven) facts.{0,160}(?:unknown|human review|review state)",
                )

    def test_each_skill_names_the_fact_dependent_longer_periods(self) -> None:
        """Removing any statutory branch must fail the maintained-skill contract."""
        for skill, path in SKILL_FILES.items():
            content = compact(path.read_text(encoding="utf-8"))
            with self.subTest(skill=skill):
                self.assertIn("20 business days", content)
                self.assertIn("first eligible contribution to a particular fund", content)
                self.assertIn("new starter", content)
                self.assertIn("recommencement", content)
                self.assertIn("fund change", content)
                self.assertIn("out-of-cycle", content)
                self.assertIn("subsequent standard qualifying-earnings payment", content)
                self.assertIn("exceptional-circumstances determination", content)
                self.assertIn("earlier contribution", content)
                self.assertIn("s 18c", content)
                self.assertIn("actual allocation", content)
                self.assertRegex(
                    content,
                    r"(?:planned|remitted).{0,120}(?:is not|does not establish).{0,80}fund receipt",
                )
                self.assertIn("enterprise agreements", content)
                self.assertIn("awards", content)
                self.assertIn("fund terms", content)
                self.assertIn("earlier payment", content)

    def test_each_skill_records_primary_sources_and_check_date(self) -> None:
        """Mutable deadline guidance must retain its source trail."""
        for skill, path in SKILL_FILES.items():
            content = path.read_text(encoding="utf-8")
            with self.subTest(skill=skill):
                self.assertIn(ATO_PAYDAY_SUPER, content)
                self.assertIn(PAYDAY_SUPER_ACT, content)
                self.assertIn(SGA_REGULATIONS, content)
                self.assertIn("20 August 2026", content)

    def test_each_skill_requires_use_time_source_reverification(self) -> None:
        """A static maintenance date must not replace the at-use source check."""
        for skill, path in SKILL_FILES.items():
            with self.subTest(skill=skill):
                self.assert_use_time_evidence_contract(
                    skill,
                    path.read_text(encoding="utf-8"),
                )

    def test_use_time_contract_rejects_a_misdirected_source_link(self) -> None:
        """The static source list must not mask a wrong operative hyperlink."""
        skill = "month-end-close"
        content = SKILL_FILES[skill].read_text(encoding="utf-8")
        mutated = content.replace(
            f"[ATO Payday Super source]({ATO_PAYDAY_SUPER})",
            "[ATO Payday Super source](https://example.invalid/)",
            1,
        )
        self.assertNotEqual(mutated, content)

        with self.assertRaisesRegex(AssertionError, "exact ATO Payday Super URL"):
            self.assert_use_time_evidence_contract(skill, mutated)

    def test_use_time_contract_rejects_an_unbound_record_instruction(self) -> None:
        """Other artefact references must not mask a detached record action."""
        skill = "month-end-close"
        artefact = USE_TIME_RECORDS[skill]
        content = SKILL_FILES[skill].read_text(encoding="utf-8")
        mutated = content.replace(f"In the {artefact}, record", "Record", 1)
        self.assertNotEqual(mutated, content)

        with self.assertRaisesRegex(
            AssertionError,
            f"bind the recording action to the {artefact}",
        ):
            self.assert_use_time_evidence_contract(skill, mutated)


if __name__ == "__main__":
    unittest.main()
