"""Derive the evidence matrix that says what backs each skill.

`docs/skill-catalogue.md` says what each skill is for. Nothing said what
*backs* it: how many primary sources it indexes, whether any of them have moved
since a person last reviewed them, which validation cards exercise it, and
whether any test asserts its text rather than merely counting it in an
inventory sweep.

That answer has to be derived, never asserted. A hand-maintained coverage table
records what its author believed on the day they wrote it, and the first
skill added afterwards makes it wrong and nothing notices. This reads the tree
and writes `coverage.json`; `tests/test_coverage_matrix.py` rebuilds it and
fails on any difference, so the file cannot claim more than the tree supports.

Run `python scripts/build_coverage.py --write` after adding a skill, a
validation card, a gate test or a source.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence, TypedDict

REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS_DIRECTORY = REPOSITORY / ".claude" / "skills"
CASES_DIRECTORY = REPOSITORY / "validation" / "cases"
TESTS_DIRECTORY = REPOSITORY / "tests"
COVERAGE_FILE = REPOSITORY / "coverage.json"

SCHEMA_VERSION = 1

# A test that walks the skills directory names every skill by construction, so
# counting it as evidence for any one skill would make the matrix uniformly
# green and tell a reader nothing. These files are the inventory sweeps; every
# other mention of a skill name in tests is a check on that skill's own text.
# `inventory_sweeps_still_sweep` proves each one still names nearly every
# skill, so this list cannot quietly become wrong.
INVENTORY_SWEEPS = frozenset({"verify_skills_cli.py"})
INVENTORY_SHARE = 0.8

# The seeded card. A skill whose only validation card is this one has the
# template and nothing written for its own failure modes.
SEEDED_CASE = "{skill}-missing-evidence"

CASE_TARGET = re.compile(r"^\s*-\s*([a-z0-9][a-z0-9-]*)\s*$", re.MULTILINE)


def front_matter(path: Path) -> str:
    """Return the text between the opening and closing front-matter markers."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError(f"{path.name}: front matter must start with '---'")
    try:
        end = lines.index("---", 1)
    except ValueError as error:
        raise ValueError(f"{path.name}: front matter must end with '---'") from error
    return "\n".join(lines[1:end])


def discover_skills() -> list[str]:
    return sorted(path.parent.name for path in SKILLS_DIRECTORY.glob("*/SKILL.md"))


def case_targets() -> dict[str, list[str]]:
    """Map each skill to the validation cards that name it as a target."""
    targets: dict[str, list[str]] = {}
    for path in sorted(CASES_DIRECTORY.glob("*.md")):
        for skill in CASE_TARGET.findall(front_matter(path)):
            targets.setdefault(skill, []).append(path.stem)
    return {skill: sorted(set(cards)) for skill, cards in targets.items()}


def test_mentions() -> dict[str, dict[str, list[str]]]:
    """Map each skill to the test files that name it, split by what that means."""
    skills = discover_skills()
    quoted = {skill: re.compile("[\"']" + re.escape(skill) + "[\"']") for skill in skills}
    mentions: dict[str, dict[str, list[str]]] = {
        skill: {"behavioural": [], "inventory": []} for skill in skills
    }
    for path in sorted(TESTS_DIRECTORY.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        kind = "inventory" if path.name in INVENTORY_SWEEPS else "behavioural"
        for skill in skills:
            if quoted[skill].search(text):
                mentions[skill][kind].append(path.name)
    return mentions


class SourceSummary(TypedDict):
    """What one skill's sources index says about itself."""

    indexed: int
    exempt: bool
    reviewed: str
    fetched: str
    unreachable: int
    moved_since_review: list[str]


class ValidationSummary(TypedDict):
    cases: int
    case_ids: list[str]
    only_seeded_case: bool


class GateSummary(TypedDict):
    behavioural: list[str]
    inventory: list[str]


class SkillRow(TypedDict):
    skill: str
    sources: SourceSummary
    validation: ValidationSummary
    gates: GateSummary


class Totals(TypedDict):
    skills: int
    sources_indexed: int
    skills_source_exempt: int
    skills_with_unreachable_sources: int
    skills_with_sources_moved_since_review: int
    skills_with_behavioural_gate: int
    skills_with_only_the_seeded_case: int


class Matrix(TypedDict):
    schema_version: int
    note: str
    totals: Totals
    skills: list[SkillRow]


def source_evidence(skill: str) -> SourceSummary:
    """Read one skill's index, including which sources outran their review.

    `moved_since_review` is the question the index exists to answer: the page
    published a change after the date a person last read it, so the workflow
    now rests on material nobody in this repository has seen.
    """
    directory = SKILLS_DIRECTORY / skill
    exempt = (directory / "sources.exempt.json").is_file()
    index = directory / "sources.json"
    if not index.is_file():
        return SourceSummary(
            indexed=0, exempt=exempt, reviewed="", fetched="", unreachable=0, moved_since_review=[]
        )

    payload = json.loads(index.read_text(encoding="utf-8"))
    sources = [record for record in payload.get("sources", []) if isinstance(record, dict)]
    reviewed = sorted(str(r.get("checked_at", "")) for r in sources if r.get("checked_at"))
    fetched = sorted(str(r.get("fetched_at", "")) for r in sources if r.get("fetched_at"))
    unreachable = sum(1 for record in sources if record.get("http_status") not in (200, None))
    moved = sorted(
        str(record.get("url", ""))
        for record in sources
        if record.get("source_last_modified")
        and str(record.get("source_last_modified", "")) > str(record.get("checked_at", ""))
    )
    return SourceSummary(
        indexed=len(sources),
        exempt=exempt,
        reviewed=reviewed[0] if reviewed else "",
        fetched=fetched[0] if fetched else "",
        unreachable=unreachable,
        moved_since_review=moved,
    )


def build() -> Matrix:
    """Assemble the matrix from the tree."""
    skills = discover_skills()
    cards = case_targets()
    mentions = test_mentions()

    rows: list[SkillRow] = []
    for skill in skills:
        skill_cards = cards.get(skill, [])
        rows.append(
            SkillRow(
                skill=skill,
                sources=source_evidence(skill),
                validation=ValidationSummary(
                    cases=len(skill_cards),
                    case_ids=skill_cards,
                    only_seeded_case=skill_cards == [SEEDED_CASE.format(skill=skill)],
                ),
                gates=GateSummary(
                    behavioural=mentions[skill]["behavioural"],
                    inventory=mentions[skill]["inventory"],
                ),
            )
        )

    return Matrix(
        schema_version=SCHEMA_VERSION,
        note=(
            "Derived from the tree by scripts/build_coverage.py. Do not edit by hand: "
            "tests/test_coverage_matrix.py rebuilds this file and fails on any difference. "
            "'reviewed' is the date a person last read the source; 'fetched' is the date "
            "of the latest recorded retrieval attempt, and never stands in for a review."
        ),
        totals=Totals(
            skills=len(skills),
            sources_indexed=sum(row["sources"]["indexed"] for row in rows),
            skills_source_exempt=sum(1 for row in rows if row["sources"]["exempt"]),
            skills_with_unreachable_sources=sum(
                1 for row in rows if row["sources"]["unreachable"]
            ),
            skills_with_sources_moved_since_review=sum(
                1 for row in rows if row["sources"]["moved_since_review"]
            ),
            skills_with_behavioural_gate=sum(1 for row in rows if row["gates"]["behavioural"]),
            skills_with_only_the_seeded_case=sum(
                1 for row in rows if row["validation"]["only_seeded_case"]
            ),
        ),
        skills=rows,
    )


def rendered(matrix: Matrix) -> str:
    return json.dumps(matrix, indent=2, ensure_ascii=False) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/build_coverage.py",
        description="Rebuild coverage.json from the skills, validation cards and tests.",
    )
    parser.add_argument("--write", action="store_true", help="Write coverage.json.")
    parser.add_argument(
        "--check", action="store_true", help="Exit 2 when coverage.json is out of date."
    )
    arguments = parser.parse_args(argv)

    matrix = rendered(build())
    if arguments.write:
        COVERAGE_FILE.write_text(matrix, encoding="utf-8")
        print(f"wrote {COVERAGE_FILE.relative_to(REPOSITORY)}")
        return 0

    current = COVERAGE_FILE.read_text(encoding="utf-8") if COVERAGE_FILE.is_file() else ""
    if arguments.check and current != matrix:
        print(
            "coverage.json is out of date. Run: python scripts/build_coverage.py --write",
            file=sys.stderr,
        )
        return 2
    print(matrix, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
