"""The artwork the README embeds must render the way it is published."""

from __future__ import annotations

import re
import unittest
import xml.etree.ElementTree as ElementTree
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
ASSETS = REPOSITORY / "assets"
TEXT_NODE = re.compile(r"<text\b[^>]*>(?P<label>[^<>]*)</text>")
# XML 1.0 permits tab, line feed and carriage return; every other C0 control is
# a fatal token wherever it appears, and renders as nothing where it does not.
FORBIDDEN_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


class ReadmeAssetTests(unittest.TestCase):
    def svg_assets(self) -> list[Path]:
        assets = sorted(ASSETS.rglob("*.svg"))
        self.assertGreaterEqual(len(assets), 1, "the README embeds at least one SVG")
        return assets

    def test_embedded_svgs_are_strict_utf8_and_well_formed(self) -> None:
        """A byte a conforming parser must reject is a broken README image."""
        for path in self.svg_assets():
            with self.subTest(asset=path.relative_to(REPOSITORY).as_posix()):
                payload = path.read_bytes()
                try:
                    markup = payload.decode("utf-8", errors="strict")
                except UnicodeDecodeError as error:
                    self.fail(f"asset is not strict UTF-8: {error}")
                try:
                    ElementTree.fromstring(markup)
                except ElementTree.ParseError as error:
                    self.fail(f"asset is not well-formed XML: {error}")

    def test_embedded_svg_labels_carry_no_invisible_control_characters(self) -> None:
        """A punctuation mark mangled into a control byte reads as a gap."""
        for path in self.svg_assets():
            markup = path.read_text(encoding="utf-8", errors="replace")
            for match in TEXT_NODE.finditer(markup):
                label = match.group("label")
                with self.subTest(
                    asset=path.relative_to(REPOSITORY).as_posix(),
                    label=label,
                ):
                    self.assertIsNone(
                        FORBIDDEN_CONTROL.search(label),
                        "a rendered label must not hide a control character where "
                        "its separator belongs",
                    )


if __name__ == "__main__":
    unittest.main()
