"""The margin scheme calculation in au-gst-property: its conditions and its worked figures."""

from __future__ import annotations

import json
import unittest
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILL = REPOSITORY / ".claude" / "skills" / "au-gst-property"


def section() -> str:
    text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
    start = text.index("## Margin scheme calculation")
    return text[start : text.index("\n## ", start + 1)]


def money(text: str) -> Decimal:
    return Decimal(text.replace("$", "").replace(",", ""))


def gst_on(margin: Decimal) -> Decimal:
    """1/11 of the margin (GST Act s 75-10(1)), rounded as s 9-90 rounds: to the cent, 0.5 up."""
    return (margin / 11).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


class MarginSchemeTests(unittest.TestCase):
    def test_eligibility_agreement_and_methods_rest_on_the_act(self) -> None:
        text = " ".join(section().split())
        for phrase in (
            "selling a freehold interest in land or a stratum unit, or by granting or selling a long-term lease (s 75-5(1) of the GST Act)",
            "acquired the entire interest, unit or lease through a supply that was ineligible for it (s 75-5(2) of the GST Act)",
            "on or before the making of the supply or within a further period the Commissioner allows (s 75-5(1A) of the GST Act)",
            "must be signed by both seller and purchaser, must clearly identify the property",
            "Without that evidence, the margin scheme does not apply",
            "1/11 of the margin (s 75-10(1) of the GST Act)",
            "exceeds the consideration for the supplier's acquisition of the interest (s 75-10(2) of the GST Act)",
            "the date of effect of its registration or, if earlier, the day it applied (item 2)",
            "cannot change to another valuation, another method or the consideration method",
            "is not a creditable acquisition (s 75-20 of the GST Act)",
            "s 75-11 of the GST Act can set the margin from the earlier history instead",
            "use the corresponding proportion of the acquisition consideration or valuation (s 75-15 of the GST Act)",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)
        # The skill states no figure from memory: each rule above has a record read that day.
        records = {r["url"] for r in json.loads((SKILL / "sources.json").read_text(encoding="utf-8"))["sources"]}
        for provision in ("9-90", "75-5", "75-10", "75-15", "75-20", "75-35"):
            with self.subTest(provision=provision):
                self.assertIn(f"https://www.ato.gov.au/law/view/document?docid=PAC/19990055/{provision}", records)
        self.assertIn("https://www.legislation.gov.au/F2020L00346/latest/text", records)

    def test_worked_figures_follow_from_their_facts(self) -> None:
        rows = {}
        for line in section().splitlines():
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if line.startswith("| ") and len(cells) == 4:
                rows[cells[0]] = cells[1:]
        consideration = [money(cell.split(" = ")[-1]) for cell in rows["Consideration for the supply"]]
        deducted = [money(cell.split(" ")[0]) for cell in rows["Deducted"]]
        margins = [money(cell) for cell in rows["Margin"]]
        self.assertEqual(consideration, [Decimal("1101320"), Decimal("990000"), Decimal("990000")])
        # The rates adjustment is part of the consideration; stamp duty and legal fees are not deducted.
        self.assertEqual(consideration[0], Decimal("1100000") + Decimal("1320"))
        self.assertEqual(deducted, [Decimal("480000"), Decimal("350000"), Decimal("95000")])
        for column, (supply, cost, margin, gst, full) in enumerate(
            zip(consideration, deducted, margins, rows["GST, 1/11 of the margin"], rows["GST on the full consideration"])
        ):
            with self.subTest(column=column):
                self.assertEqual(margin, supply - cost)
                self.assertEqual(money(gst.split(" rounded to ")[1]), gst_on(margin))
                self.assertEqual(money(full), gst_on(supply))
        # Rounding is visible: the exact 1/11 is shown before the rounded cent.
        self.assertIn("$56,483.636..., rounded to $56,483.64", section())


if __name__ == "__main__":
    unittest.main()
