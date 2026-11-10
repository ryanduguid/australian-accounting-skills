# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""Read a skill's sections, workflow steps and sentences for the prose tests.

The prose tests check the dates, authorities, exceptions and prohibitions a step
must carry, not its wording. Their helpers live here so a change to how a
sentence is split or a negator found is made once. The name does not match the
`test*.py` discovery pattern, so unittest imports it but collects nothing from it.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

SKILLS = Path(__file__).resolve().parents[1] / ".claude" / "skills"
PENDING = "source-discovery-only-human-review-pending"
PENDING_FACT = "Primary-source discovery only; no human-reviewed current-law fact is recorded."
ISO_DATE = r"^\d{4}-\d{2}-\d{2}$"
# A negator directly before the matched verb, allowing only auxiliaries, 'to', articles
# and a set-off 'however' between ('do not apply', 'not to escalate', 'not be apportioned',
# 'does not, however, apply'). 'No. 86' is a number and 'no longer' a change.
NEGATED = r"(?:\b(?:not|never|cannot|no(?!\.))|n't)(?:\W+(?:be|been|to|a|an|the|however|also))*\W+$"
# A required negative predicate keeps its negator before its verb.
NOT = r"(?:\bnot|\bnever|n't)\W+"
# A required prohibition keeps its negator directly before its verb.
DO_NOT = r"\b(?:do not|don't|never|must not)\W+"
# The text before an item of a prohibited list: the negator, then only earlier items of
# that list, each closed by a comma, 'or' or ', or'.
IN_PROHIBITED_LIST = DO_NOT + r"(?:[^,.;:]+?(?:,(?:\s+or)?|\s+or)\s+)*$"


def skill_text(skill: str) -> str:
    return (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8")


def raw_section(skill: str, heading: str) -> str:
    """The Markdown under the first `## <heading>...` until the next `## ` heading."""
    text = skill_text(skill)
    start = re.search(rf"^## {re.escape(heading)}.*$", text, re.MULTILINE)
    assert start, f"{skill} has no '## {heading}' section"
    end = re.compile(r"^## ", re.MULTILINE).search(text, start.end())
    return text[start.end() : end.start() if end else len(text)]


def section(skill: str, heading: str) -> str:
    return " ".join(raw_section(skill, heading).split())


def workflow_step(skill: str, number: int | str) -> str:
    """Workflow step `number` with its indented continuation paragraphs, up to the next step."""
    workflow = raw_section(skill, "Workflow")
    start = re.search(rf"^{number}\. ", workflow, re.MULTILINE)
    assert start, f"{skill} has no workflow step {number}"
    end = re.compile(r"^\d+[a-z]?\. ", re.MULTILINE).search(workflow, start.end())
    return " ".join(workflow[start.start() : end.start() if end else len(workflow)].split())


def table_row(skill: str, heading: str, first_cell: str) -> list[str]:
    """The other cells of the table row under `## <heading>` whose first cell is `first_cell`."""
    for line in raw_section(skill, heading).splitlines():
        cells = [" ".join(cell.split()) for cell in line.strip().strip("|").split("|")]
        if line.lstrip().startswith("|") and cells[0] == first_cell:
            return cells[1:]
    raise AssertionError(f"{skill} has no '{first_cell}' row under '## {heading}'")


def sentences(text: str) -> list[str]:
    """Sentences of normalised text; 'No. 86' and paragraph numbers such as 'R320.7' do not end one."""
    return re.split(r"(?<=\.)\s+(?=[A-Z*\[(])", text)


def affirms(sentence: str, pattern: str) -> bool:
    """`pattern` matches somewhere in `sentence` with no negator directly before it."""
    return any(
        not re.search(NEGATED, sentence[: match.start()], re.IGNORECASE)
        for match in re.finditer(rf"(?=(?:{pattern}))", sentence, re.IGNORECASE)
    )


def records(skill: str) -> dict[str, dict[str, object]]:
    payload = json.loads((SKILLS / skill / "sources.json").read_text(encoding="utf-8"))
    return {str(source["url"]): source for source in payload["sources"]}
