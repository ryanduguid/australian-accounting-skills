from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
TARGET_FILES = (
    ROOT / "README.md",
    ROOT / ".claude/skills/bas-preparation/SKILL.md",
    ROOT / ".claude/skills/month-end-close/SKILL.md",
    ROOT / ".claude/skills/workpaper-tie-out/SKILL.md",
    ROOT / ".claude/skills/year-end-workpapers/SKILL.md",
)
OLD_URLS = (
    "https://github.com/ryanduguid/au-tax-mcp-server",
    "https://github.com/ryanduguid/review-ready-gate",
    "https://github.com/ryanduguid/monthly-close-control-plane",
)
CANONICAL_URLS = (
    "https://github.com/ryanduguid/aus-accounting-mcp",
    "https://github.com/ryanduguid/workpaper-review-gate",
    "https://github.com/ryanduguid/monthly-close-controls",
)
COMPATIBILITY_IDENTIFIERS = (
    "aus-accounting-mcp",
    "review-ready gate",
)


class PortfolioLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.aggregate_text = "\n".join(
            path.read_text(encoding="utf-8") for path in TARGET_FILES
        )

    def test_old_repository_urls_are_absent(self) -> None:
        for url in OLD_URLS:
            with self.subTest(url=url):
                self.assertNotIn(url, self.aggregate_text)

    def test_canonical_repository_urls_are_present(self) -> None:
        for url in CANONICAL_URLS:
            with self.subTest(url=url):
                self.assertIn(url, self.aggregate_text)

    def test_compatibility_identifiers_remain(self) -> None:
        for identifier in COMPATIBILITY_IDENTIFIERS:
            with self.subTest(identifier=identifier):
                self.assertIn(identifier, self.aggregate_text)


if __name__ == "__main__":
    unittest.main()
