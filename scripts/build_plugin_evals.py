"""Build a clean plugin copy with task-only `claude plugin eval` cases from the cards."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path
from typing import cast

import yaml

from validate_validation import ROOT, parse_front_matter

# Held back from the evaluated session; everything else in a card is the task, so
# a variant a required check depends on stays visible.
WITHHELD_SECTIONS = ("Required checks", "Must not do", "Source-verification and reviewer boundary")
PLUGIN_PATHS = (".claude-plugin", ".claude/skills", ".claude/rules", "DISCLAIMER.md", "LICENSE")
ALLOWED_TOOLS = ["Read", "Glob", "Grep", "Skill"]
JUDGE_PREFACE = (
    "The answer comes from a session with no web access and no way to create files. "
    "Reporting a mutable rate, threshold or rule as unverified, and leaving it for a "
    "reviewer, satisfies a check that asks for verification. Judge substance, not "
    "wording: an equivalent statement counts. Numbers must match."
)


def card_sections(card: str, name: str) -> tuple[dict[str, object], dict[str, str]]:
    metadata, body = parse_front_matter(card, name)
    sections: dict[str, str] = {}
    matches = list(re.finditer(r"(?m)^## ([^\r\n]+)\r?$", body))
    for index, match in enumerate(matches):
        heading = match.group(1)
        if heading in sections:
            raise ValueError(f"{name}: duplicate section: {heading}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[heading] = body[match.end():end].strip()
    for heading in WITHHELD_SECTIONS:
        if heading not in sections:
            raise ValueError(f"{name}: missing section: {heading}")
    return metadata, sections


def front_matter(fields: dict[str, object]) -> str:
    return "---\n" + yaml.safe_dump(fields, sort_keys=False, allow_unicode=True, width=100) + "---\n"


def build_case(card: str, case_id: str, runs: int, max_turns: int) -> dict[str, str]:
    """Return one case's files, relative to its directory."""
    metadata, sections = card_sections(card, f"{case_id}.md")
    skills = cast(list[str], metadata["target_skills"])
    task = "\n\n".join(
        f"## {heading}\n\n{text}" for heading, text in sections.items() if heading not in WITHHELD_SECTIONS
    )
    skill_pattern = "|".join(re.escape(skill) for skill in skills)
    return {
        "prompt.md": front_matter({
            "name": case_id,
            "description": f"Task-only input from validation card {case_id}.",
            "tags": ["card", *skills],
            "runs": runs,
            "max_turns": max_turns,
            "allowed_tools": ALLOWED_TOOLS,
        }) + "\n" + task + "\n",
        "graders/skill-fired.md": front_matter({
            "type": "tool_used",
            "tool": "Skill",
            "input_match": f'"skill"\\s*:\\s*"(?:australian-accounting-skills:)?(?:{skill_pattern})"',
            "min": 1,
        }) + "\nA target skill must fire.\n",
        "graders/required-checks.md": front_matter({
            "type": "llm",
            "criteria": (
                f"{JUDGE_PREFACE}\n\nPASS only if the answer meets every check below. "
                f"FAIL if it misses any.\n\n{sections['Required checks']}\n"
            ),
            "focus": "last_message",
        }) + "\nJudge the final answer against the criteria.\n",
        "graders/restraint.md": front_matter({
            "type": "llm",
            "criteria": (
                f"{JUDGE_PREFACE}\n\nPASS unless the answer does any of the following. "
                f"FAIL if it does.\n\n{sections['Must not do']}\n"
            ),
            "focus": "last_message",
        }) + "\nJudge the final answer against the criteria.\n",
    }


def build(destination: Path, runs: int, max_turns: int, root: Path = ROOT) -> dict[str, object]:
    destination = destination.resolve()
    if destination.is_relative_to(root.resolve()):
        raise ValueError("the evaluated plugin copy must be outside the repository")
    if destination.exists():
        raise ValueError("destination already exists; preserve the earlier build")
    destination.mkdir(parents=True)
    # Cards and tests stay behind, so the evaluated session cannot read them.
    for relative in PLUGIN_PATHS:
        source = root / relative
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if source.is_dir():
            shutil.copytree(source, target)
        else:
            shutil.copyfile(source, target)
    cards = sorted((root / "validation/cases").glob("*.md"))
    digests = {}
    for path in cards:
        data = path.read_bytes()
        digests[path.stem] = hashlib.sha256(data).hexdigest()
        for relative, text in build_case(data.decode("utf-8"), path.stem, runs, max_turns).items():
            target = destination / "evals" / path.stem / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("x", encoding="utf-8", newline="\n") as stream:
                stream.write(text)
    head = subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True, check=False
    ).stdout.strip()
    manifest: dict[str, object] = {"commit": head, "runs": runs, "card_sha256": digests}
    (destination / "evals-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--max-turns", type=int, default=12)
    args = parser.parse_args()
    manifest = build(args.destination, args.runs, args.max_turns)
    print(f"built {len(cast(dict[str, str], manifest['card_sha256']))} cases in {args.destination}")


if __name__ == "__main__":
    main()
