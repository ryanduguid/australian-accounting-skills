# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""Every relative Markdown link in a tracked file reaches a file, offline.

A link into another Markdown file must also name a heading that file has.
Anchors are checked with GitHub's heading slug rule, so a link that GitHub
resolves through an explicit HTML `id` or `name` is accepted too. A link to
any other kind of file is checked for the file only.

YAML front matter, fenced and indented code, code spans, HTML comments and
footnote definitions are skipped, and setext headings count as headings.
Unsupported: a prose line that starts `[Label]: value` is read as a reference
definition, and list tracking is approximate, so an indented block after a list
item counts as list content until a blank line and an unindented paragraph end
the list.
"""

from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]

FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
CODE_SPAN = re.compile(r"(`+).*?\1")
# An inline link or image, `[text](target "title")`, and a reference
# definition, `[label]: target`. Nested brackets in link text are rare here
# and the target is what matters.
INLINE_LINK = re.compile(r"\]\(\s*(<[^>]*>|[^)\s]+)")
# A footnote definition, `[^1]: text`, is not a reference definition.
REFERENCE_DEFINITION = re.compile(r"^ {0,3}\[(?!\^)[^\]]+\]:\s*(<[^>]*>|\S+)")
SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
HEADING = re.compile(r"^ {0,3}#{1,6}\s+(.*?)\s*#*\s*$")
SETEXT_UNDERLINE = re.compile(r"^ {0,3}(?:=+|-+)\s*$")
HTML_ANCHOR = re.compile(r"""<a\s[^>]*\b(?:id|name)=["']([^"']+)["']""")
HTML_COMMENT = re.compile(r"<!--.*?-->")
INDENTED = re.compile(r"^(?: {4}|\t)")
LIST_ITEM = re.compile(r"^ {0,3}(?:[-*+]|\d{1,9}[.)])(?:\s|$)")


def slug(heading: str) -> str:
    """GitHub's heading anchor: lower case, punctuation dropped, spaces to hyphens."""
    text = re.sub(r"<[^>]+>", "", heading)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = text.replace("`", "").lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return text.replace(" ", "-")


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Numbered lines outside code blocks and HTML comments, without code spans."""
    lines: list[tuple[int, str]] = []
    fence = ""
    comment = indented_code = in_list = False
    previous_blank = True
    front_matter = text.startswith("---\n")
    for number, line in enumerate(text.splitlines(), 1):
        if front_matter:
            # YAML front matter has no links or headings; its closing `---` is
            # not a setext underline.
            front_matter = number == 1 or line != "---"
            continue
        opened = FENCE.match(line)
        if fence:
            if opened and opened.group(1)[0] == fence[0] and len(opened.group(1)) >= len(fence):
                fence = ""
            continue
        if opened:
            fence = opened.group(1)
            continue
        blank = not line.strip()
        # An indented code block starts after a blank line, but not inside a list,
        # where the indent continues the item.
        if not blank and INDENTED.match(line):
            indented_code = indented_code or (previous_blank and not in_list)
        elif not blank:
            indented_code = False
            in_list = bool(LIST_ITEM.match(line)) or (in_list and not previous_blank)
        previous_blank = blank
        if indented_code:
            continue
        if comment:
            if "-->" not in line:
                continue
            line = line.split("-->", 1)[1]
        line = HTML_COMMENT.sub("", line)
        line, comment_opened, _ = line.partition("<!--")
        comment = bool(comment_opened)
        lines.append((number, CODE_SPAN.sub("", line)))
    return lines


def anchors(path: Path) -> set[str]:
    found: set[str] = set()
    seen: dict[str, int] = {}
    previous = ""
    for _, line in prose_lines(path.read_text(encoding="utf-8")):
        found.update(anchor.lower() for anchor in HTML_ANCHOR.findall(line))
        heading = HEADING.match(line)
        if not heading and SETEXT_UNDERLINE.match(line) and previous.strip():
            heading = HEADING.match(f"# {previous.strip()}")
        previous = "" if heading else line
        if heading:
            base = slug(heading.group(1))
            count = seen.get(base, 0)
            seen[base] = count + 1
            found.add(base if count == 0 else f"{base}-{count}")
    return found


def broken_links(root: Path, files: list[Path]) -> list[str]:
    broken: list[str] = []
    for path in files:
        for number, line in prose_lines(path.read_text(encoding="utf-8")):
            targets = INLINE_LINK.findall(line) + REFERENCE_DEFINITION.findall(line)
            for raw in targets:
                target = raw.strip("<>")
                if not target or SCHEME.match(target):
                    continue
                file_part, _, fragment = target.partition("#")
                file_part = unquote(file_part)
                if not file_part:
                    destination = path
                elif file_part.startswith("/"):
                    destination = root / file_part.lstrip("/")
                else:
                    destination = path.parent / file_part
                name = f"{path.relative_to(root).as_posix()}:{number}: {target}"
                if not destination.exists():
                    broken.append(f"{name} (no such file)")
                elif fragment and destination.suffix == ".md" and destination.is_file():
                    if unquote(fragment).lower() not in anchors(destination):
                        broken.append(f"{name} (no such heading)")
    return broken


def tracked_markdown() -> list[Path]:
    listed = subprocess.run(
        ["git", "ls-files", "-z", "--", "*.md"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [ROOT / name for name in listed.split("\0") if name]


class MarkdownLinkTests(unittest.TestCase):
    def test_every_relative_link_resolves(self) -> None:
        files = tracked_markdown()
        self.assertTrue(files, "git listed no tracked Markdown files")
        self.assertEqual(broken_links(ROOT, files), [])

    def test_a_broken_link_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            (root / "docs" / "guide.md").write_text("# Guide\n\n## Set up\n", encoding="utf-8")
            page = root / "README.md"
            page.write_text(
                "# Readme\n\n"
                "[ok](docs/guide.md#set-up) [ok](#readme) [ok](https://example.com/x)\n"
                "[missing](docs/gone.md) [bad heading](docs/guide.md#tear-down)\n"
                "`[code](docs/gone.md)`\n\n"
                "```\n[fenced](docs/gone.md)\n```\n\n"
                "[ref]: /docs/absent.md\n",
                encoding="utf-8",
            )
            self.assertEqual(
                broken_links(root, [page]),
                [
                    "README.md:4: docs/gone.md (no such file)",
                    "README.md:4: docs/guide.md#tear-down (no such heading)",
                    "README.md:11: /docs/absent.md (no such file)",
                ],
            )

    def test_text_that_is_not_a_link_is_not_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            page = root / "README.md"
            page.write_text(
                "Set up\n======\n\n"
                'Notes <a id="R1"></a>\n\n'
                "[setext](#set-up) [capital anchor](#R1)\n\n"
                "<!-- [one line](docs/gone.md) -->\n"
                "<!--\n[multi line](docs/gone.md)\n--> [after comment](docs/gone.md)\n\n"
                "    [indented code](docs/gone.md)\n\n"
                "A footnote.[^1]\n\n"
                "[^1]: See the ATO page.\n\n"
                "- A list item\n\n"
                "    [list continuation](docs/gone.md)\n",
                encoding="utf-8",
            )
            self.assertEqual(
                broken_links(root, [page]),
                [
                    "README.md:11: docs/gone.md (no such file)",
                    "README.md:21: docs/gone.md (no such file)",
                ],
            )
            # Front matter's closing line is not a setext underline.
            page.write_text("---\nname: x\n---\n\n[front matter](#name-x)\n", encoding="utf-8")
            self.assertEqual(broken_links(root, [page]), ["README.md:5: #name-x (no such heading)"])

    def test_slug_follows_github_heading_anchors(self) -> None:
        self.assertEqual(
            slug("Claude.ai or the Claude desktop app, without a terminal"),
            "claudeai-or-the-claude-desktop-app-without-a-terminal",
        )
        self.assertEqual(slug("Corrections since v0.2.1"), "corrections-since-v021")
        self.assertEqual(slug("Tagged 76-workflow release"), "tagged-76-workflow-release")


if __name__ == "__main__":
    unittest.main()
