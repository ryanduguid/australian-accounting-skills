"""Freeze one task-only input and its withheld rubric outside the checkout."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import cast

from validate_validation import ROOT, parse_front_matter

TASK_SECTIONS = ("Scenario", "Task", "Synthetic inputs", "Deliberately unavailable evidence")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def task_input(card: bytes, name: str) -> tuple[bytes, list[str]]:
    metadata, body = parse_front_matter(card.decode("utf-8"), name)
    sections: dict[str, str] = {}
    matches = list(re.finditer(r"(?m)^## ([^\r\n]+)\r?$", body))
    for index, match in enumerate(matches):
        heading = match.group(1)
        if heading in sections:
            raise ValueError(f"duplicate section: {heading}")
        end = matches[index + 1].start() if index + 1 < len(matches) else len(body)
        sections[heading] = body[match.end():end].strip()
    missing = set(TASK_SECTIONS) - sections.keys()
    if missing:
        raise ValueError(f"missing task sections: {sorted(missing)}")
    text = "\n\n".join(f"## {heading}\n\n{sections[heading]}" for heading in TASK_SECTIONS)
    skills = cast(list[str], metadata["target_skills"])
    return (text + "\n").encode("utf-8"), skills


def prepare(case_id: str, destination: Path, model: str, runtime: str, root: Path = ROOT) -> None:
    if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", case_id) is None:
        raise ValueError("case ID must be a lowercase hyphenated slug")
    destination = destination.resolve()
    if destination.is_relative_to(root.resolve()):
        raise ValueError("trial evidence must be outside the repository")
    if destination.exists():
        raise ValueError("destination already exists; preserve the frozen trial")
    card = (root / "validation/cases" / f"{case_id}.md").read_bytes()
    task, skills = task_input(card, f"{case_id}.md")
    files = {}
    for skill in skills:
        folder = root / ".claude/skills" / skill
        if folder.is_symlink():
            raise ValueError("skill context must not follow symbolic links")
        for path in sorted(folder.rglob("*")):
            if path.is_symlink():
                raise ValueError("skill context must not follow symbolic links")
            if path.name.casefold().startswith(".env") or path.suffix.casefold() in {
                ".pem", ".key", ".token", ".tokens"
            }:
                raise ValueError("credential files are not trial context")
            if path.is_file():
                files[path.relative_to(root).as_posix()] = digest(path.read_bytes())
        if not (folder / "SKILL.md").is_file():
            raise ValueError(f"missing skill: {skill}")
    manifest = {
        "case_id": case_id,
        "model": model,
        "runtime": runtime,
        "target_skills": skills,
        "files": files,
        "tools": "Freeze actual tool availability before observation; preparation establishes none.",
        "input_sha256": digest(task),
        "rubric_sha256": digest(card),
    }
    destination.mkdir(parents=True)
    payloads = {
        "input.md": task,
        "rubric.md": card,
        "context.json": (json.dumps(manifest, indent=2) + "\n").encode("utf-8"),
    }
    for name, content in payloads.items():
        with (destination / name).open("xb") as stream:
            stream.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case_id")
    parser.add_argument("destination", type=Path)
    parser.add_argument("--model", default="unselected")
    parser.add_argument("--runtime", default="unselected")
    args = parser.parse_args()
    prepare(args.case_id, args.destination, args.model, args.runtime)


if __name__ == "__main__":
    main()
