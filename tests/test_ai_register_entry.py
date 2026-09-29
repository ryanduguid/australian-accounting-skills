"""The supplier record describes the release the README tells people to install."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
PUBLISHED = re.compile(r"(\d+) workflows in the published release,? \[v(\d+\.\d+\.\d+)\]")


class AiRegisterEntryTests(unittest.TestCase):
    def test_entry_names_the_published_release_and_its_inventory(self) -> None:
        """Firms use this record in their registers, so it must follow the README."""
        readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
        entry = (REPOSITORY / "docs" / "ai-register-entry.md").read_text(encoding="utf-8")
        published = PUBLISHED.search(readme)
        self.assertIsNotNone(published, "the README no longer names its published release")
        assert published is not None
        count, version = published.groups()
        self.assertIn(f"published release v{version} ({count} skills)", entry)

    def test_readme_links_the_entry(self) -> None:
        readme = (REPOSITORY / "README.md").read_text(encoding="utf-8")
        self.assertIn("(docs/ai-register-entry.md)", readme)


if __name__ == "__main__":
    unittest.main()
