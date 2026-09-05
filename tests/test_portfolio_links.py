from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
# The ten transferred contracting SKILL.md files are byte-pinned to the
# reviewed Hardhat Ledger source commit by tests/test_hardhat_consolidation.py,
# so wip-over-under-billing/SKILL.md keeps its original TheWIPTally link until
# a reviewed skill change retires that pin. Its destination-owned sources.json
# carries the maintained location and is checked here instead.
TARGET_FILES = (
    ROOT / "README.md",
    ROOT / ".claude/skills/bas-preparation/SKILL.md",
    ROOT / ".claude/skills/month-end-close/SKILL.md",
    ROOT / ".claude/skills/workpaper-tie-out/SKILL.md",
    ROOT / ".claude/skills/year-end-workpapers/SKILL.md",
    ROOT / ".claude/skills/stp-finalisation/SKILL.md",
    ROOT / ".claude/skills/xero-exports/SKILL.md",
    ROOT / ".claude/skills/wip-over-under-billing/sources.json",
)

# Renamed and then archived repositories. The September 2026 consolidation
# moved every engine into a monorepo and archived the source repositories, so
# a link to any of these names now resolves to a read-only archive.
OLD_URLS = (
    "https://github.com/ryanduguid/au-tax-mcp-server",
    "https://github.com/ryanduguid/review-ready-gate",
    "https://github.com/ryanduguid/monthly-close-control-plane",
    "https://github.com/ryanduguid/aus-accounting-mcp",
    "https://github.com/ryanduguid/workpaper-review-gate",
    "https://github.com/ryanduguid/monthly-close-controls",
    "https://github.com/ryanduguid/payday-super-checker",
    "https://github.com/ryanduguid/xero-trial-balance-export",
    "https://github.com/ryanduguid/TheWIPTally",
    "https://github.com/ryanduguid/hardhat-ledger",
)
CANONICAL_URLS = (
    "https://github.com/ryanduguid/australian-accounting/tree/main/apps/aus-accounting-mcp",
    "https://github.com/ryanduguid/accounting-review-pipeline/tree/main/packages/review-ready-gate",
    "https://github.com/ryanduguid/accounting-review-pipeline/tree/main/packages/monthly-close-control-plane",
    "https://github.com/ryanduguid/australian-accounting/tree/main/packages/payday-super-checker",
    "https://github.com/ryanduguid/accounting-review-pipeline/tree/main/packages/xero-trial-balance-export",
    "https://github.com/ryanduguid/australian-accounting/tree/main/packages/the-wip-tally",
)
COMPATIBILITY_IDENTIFIERS = (
    "aus-accounting-mcp",
    "review-ready gate",
    "monthly-close-control-plane",
    "payday-super-check",
    "wip-tally schedule",
)
# docs/HARDHAT-CONSOLIDATION.md keeps the rollback route to the archived
# Hardhat Ledger v0.1.5 release on purpose; that file is provenance.
PROVENANCE_FILES = (ROOT / "docs/HARDHAT-CONSOLIDATION.md",)


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

    def test_provenance_record_keeps_the_archived_hardhat_rollback_release(self) -> None:
        archived_release = "https://github.com/ryanduguid/hardhat-ledger/releases/tag/v0.1.5"
        for path in PROVENANCE_FILES:
            with self.subTest(path=path.name):
                self.assertIn(archived_release, path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
