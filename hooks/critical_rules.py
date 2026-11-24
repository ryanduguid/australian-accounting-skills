# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: Apache-2.0
"""Claude Code plugin hook: attach matching skills' anchored critical rules.

`prompt` mode (UserPromptSubmit) matches the prompt against each skill's
keywords in skill-keywords.json. `compact` mode (SessionStart after compaction)
matches skill names in the tail of the session transcript. Either way it prints
the anchored no-lodgement, evidence-boundary, untrusted-instruction and
risk-rating items of at most MAX_SKILLS skills, at most MAX_CHARS characters in
all, and prints nothing when no skill matches or anything goes wrong.

Standard library only and no network access: a plugin hook runs on the user's
machine without a build step.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / ".claude" / "skills"
KEYWORDS = Path(__file__).resolve().parent / "skill-keywords.json"
PLUGIN = "australian-accounting-skills"
MAX_SKILLS = 3
MAX_CHARS = 6000
#: How much of the transcript's end compact mode reads.
TRANSCRIPT_TAIL = 1024 * 1024
ANCHOR = re.compile(r" <!-- rule: ([a-z-]+) -->$")
ITEM_START = re.compile(r"^\s*(?:[-*+]|\d+[a-z]?[.)])\s|^#")
MARKER = re.compile(r"^\s*(?:[-*+]|\d+[a-z]?[.)])\s+")
EVENTS = {"prompt": "UserPromptSubmit", "compact": "SessionStart"}


def skill_names() -> list[str]:
    return sorted(path.parent.name for path in SKILLS.glob("*/SKILL.md"))


def rules(skill: str) -> list[str]:
    """The skill's anchored items, in file order, anchors and list markers removed."""
    lines = (SKILLS / skill / "SKILL.md").read_text(encoding="utf-8").splitlines()
    items: list[str] = []
    for index, line in enumerate(lines):
        if not ANCHOR.search(line):
            continue
        while match := ANCHOR.search(line):
            line = line[: match.start()]
        item = [MARKER.sub("", line).strip()]
        for following in lines[index + 1 :]:
            if not following.strip() or ITEM_START.match(following):
                break
            item.append(following.strip())
        items.append(" ".join(item))
    return items


def pattern(phrase: str) -> re.Pattern[str]:
    """A phrase as whole words, ignoring case, with an optional plural ending."""
    return re.compile(r"(?<![\w-])" + re.escape(phrase) + r"(?:e?s)?(?![\w-])", re.I)


def prompt_matches(prompt: str) -> list[str]:
    """Skills whose name or a keyword appears in the prompt, earliest mention first."""
    keywords = json.loads(KEYWORDS.read_text(encoding="utf-8"))
    found: dict[str, int] = {}
    for skill in skill_names():
        phrases = [skill, *keywords.get(skill, [])]
        hits = [m.start() for phrase in phrases if (m := pattern(phrase).search(prompt))]
        if hits:
            found[skill] = min(hits)
    return sorted(found, key=lambda skill: (found[skill], skill))


def transcript_matches(transcript: str) -> list[str]:
    """Skills named in the transcript's tail, most recent mention first."""
    path = Path(transcript)
    with path.open("rb") as handle:
        size = handle.seek(0, 2)
        handle.seek(max(0, size - TRANSCRIPT_TAIL))
        tail = handle.read().decode("utf-8", errors="replace")
    found: dict[str, int] = {}
    for skill in skill_names():
        last = [m.start() for m in pattern(skill).finditer(tail)]
        if last:
            found[skill] = last[-1]
    return sorted(found, key=lambda skill: (-found[skill], skill))


def context(skills: list[str], reason: str) -> str:
    """The rules text for up to MAX_SKILLS skills, never longer than MAX_CHARS."""
    text = ""
    for skill in skills[:MAX_SKILLS]:
        block = f"Critical rules of the {PLUGIN} skill {skill} ({reason}):\n" + "".join(
            f"- {item}\n" for item in rules(skill)
        )
        if len(text) + len(block) > MAX_CHARS:
            break
        text += block
    return text.strip()


def run(mode: str, payload: dict[str, object]) -> str:
    """The hook's JSON output for `payload`, or an empty string."""
    if mode == "prompt" and isinstance(prompt := payload.get("prompt"), str):
        text = context(prompt_matches(prompt), "the prompt mentions it")
    elif (
        mode == "compact"
        and payload.get("source") == "compact"
        and isinstance(transcript := payload.get("transcript_path"), str)
    ):
        text = context(transcript_matches(transcript), "used before compaction")
    else:
        return ""
    if not text:
        return ""
    output = {"hookEventName": EVENTS[mode], "additionalContext": text}
    return json.dumps({"hookSpecificOutput": output})


def main(argv: list[str]) -> int:
    try:
        payload = json.loads(sys.stdin.buffer.read().decode("utf-8"))
        output = run(argv[1], payload) if len(argv) == 2 and isinstance(payload, dict) else ""
    except (OSError, ValueError, KeyError):
        return 0
    if output:
        sys.stdout.write(output + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
