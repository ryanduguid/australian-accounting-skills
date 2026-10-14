"""Skill prose must not hard-code dollar amounts or percentages.

CONTRIBUTING.md sends the agent to the primary source for anything that
changes, because a hard-coded current-year figure goes wrong the next year
without saying so. This gate finds dollar amounts and percentages in skill
Markdown outside code, inline code and URLs. Only the figures listed
below with a reason may appear, each at most its listed number of times; any
other figure fails until a person replaces it with a source pointer or lists
it with a reason.
"""

from __future__ import annotations

import re
import unittest
from collections import Counter
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS_DIRECTORY = REPOSITORY / ".claude" / "skills"

FENCED = re.compile(r"^(```|~~~).*?^\1", re.MULTILINE | re.DOTALL)
INLINE_CODE = re.compile(r"`[^`\n]*`")
LINK_TARGET = re.compile(r"\]\([^)\s]*\)")
BARE_URL = re.compile(r"https?://\S+")
FIGURE = re.compile(r"\$\s?\d[\d,]*(?:\.\d+)?|\b\d+(?:\.\d+)?\s?(?:%|per\s?cent\b)", re.IGNORECASE)

# The only figures allowed in skill prose, by file and exact text, with the
# number of occurrences and the reason each stays. Every other figure was
# replaced by a pointer to its primary source on 15 October 2026.
KEPT_FIGURES: dict[tuple[str, str], tuple[int, str]] = {
    ("bas-preparation/references/transaction-gst-review.md", "$100"): (
        2, "fabricated input to a worked arithmetic example, not a rate or threshold"),
    ("bas-preparation/references/transaction-gst-review.md", "$60"): (
        1, "result of the same fabricated worked example"),
    ("bas-preparation/references/transaction-gst-review.md", "60%"): (
        1, "fabricated creditable-use input to the same worked example"),
    ("coal-lsl-levy/SKILL.md", "75%"): (
        1, "Formula B in s 3B(1) of the Payroll Levy Collection Act 1992 as read in "
        "C2026C00364; test_legal_source_gates.py pins the formula wording"),
    ("contractor-super-tpar/SKILL.md", "10%"): (
        1, "the turnover condition of determination F2019L00864 as read; "
        "test_legal_source_gates.py pins the condition wording"),
}


def prose(text: str) -> str:
    """The text a reader sees as prose: no code, inline code or URLs."""
    for pattern in (FENCED, INLINE_CODE, LINK_TARGET, BARE_URL):
        text = pattern.sub(" ", text)
    return text


def figures_in(text: str) -> list[str]:
    return [" ".join(match.group(0).split()) for match in FIGURE.finditer(prose(text))]


def skill_figures() -> Counter[tuple[str, str]]:
    found: Counter[tuple[str, str]] = Counter()
    for path in sorted(SKILLS_DIRECTORY.rglob("*.md")):
        name = path.relative_to(SKILLS_DIRECTORY).as_posix()
        for figure in figures_in(path.read_text(encoding="utf-8")):
            found[(name, figure)] += 1
    return found


class SkillFigureTests(unittest.TestCase):
    def test_no_new_figures_in_skill_prose(self) -> None:
        found = skill_figures()
        new = {
            key: count
            for key, count in found.items()
            if count > KEPT_FIGURES.get(key, (0, ""))[0]
        }
        self.assertEqual(
            new,
            {},
            "replace each figure with a pointer to its primary source, "
            "or list it in KEPT_FIGURES with a reason",
        )

    def test_listed_figures_are_still_present(self) -> None:
        """A removed figure leaves a stale entry that would allow it back."""
        found = skill_figures()
        stale = {key: count for key, (count, _) in KEPT_FIGURES.items() if found[key] < count}
        self.assertEqual(stale, {})

    def test_every_kept_figure_has_a_reason(self) -> None:
        self.assertEqual([key for key, (_, reason) in KEPT_FIGURES.items() if not reason.strip()], [])

    def test_detection_ignores_code_and_urls_but_not_prose(self) -> None:
        self.assertEqual(figures_in("Apply the $1,234.50 cap and a 9.5% rate."), ["$1,234.50", "9.5%"])
        self.assertEqual(figures_in("A 12 per cent loading."), ["12 per cent"])
        self.assertEqual(figures_in("Run `pay --rate 11%`."), [])
        self.assertEqual(figures_in("```\n$500\n```\nNo figure."), [])
        self.assertEqual(figures_in("[ruling](https://x.test/view?docid=TXR%2FTR20223)"), [])
        self.assertEqual(figures_in("See https://x.test/a%20b for detail."), [])
        self.assertEqual(figures_in("Section 26-50 and 7.30 pm on 12 May 2026."), [])


if __name__ == "__main__":
    unittest.main()
