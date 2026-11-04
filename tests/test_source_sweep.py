# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: LicenseRef-Duguid-Public-Attribution-1.0
"""What the source sweep workflow relies on from source_refresh.py.

The workflow hands the exit status and report of `source_refresh.py --check`
to `accounting-skills sweep-outcome`, which accepts exit 0 or 2 only with a
report written during the run whose counts agree with the status. These checks
hold source_refresh.py to its side: the statuses it exits with, the report the
native command parses, and the issue the workflow files.
"""

from __future__ import annotations

import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "scripts"))

import source_refresh  # noqa: E402

STARTED = datetime(2026, 9, 20, 19, 0, 5, tzinfo=timezone.utc)
# tools/accounting-skills/tests/sweep.rs parses this report, so the native
# outcome command is tested against what this renderer writes.
RENDERED_REPORT = REPOSITORY / "tools/accounting-skills/tests/sweep-report.md.fixture"
COUNT = re.compile(r"^- ([a-z-]+)[^:\n]*: (\d+)$", re.M)


def fetched(status: int = 200, digest: str = "a" * 64, error: str = "") -> source_refresh.Fetched:
    return source_refresh.Fetched(
        status=status,
        final_url="https://example.test/page",
        digest=digest,
        kind=source_refresh.HTML_KIND,
        content_type="text/html",
        last_modified="",
        error=error,
    )


def report_text(outcomes: dict[str, int], at: datetime = STARTED) -> str:
    """Render a real report through source_refresh."""
    report = source_refresh.Report()
    for name, count in outcomes.items():
        for index in range(count):
            report.outcomes.append(
                source_refresh.Outcome(
                    skill="example-skill",
                    title=f"{name} {index}",
                    url=f"https://example.test/{name}/{index}",
                    outcome=name,
                    detail="detail",
                    checked_at="2026-09-08",
                    fetched=fetched(),
                )
            )

    class Clock(datetime):
        @classmethod
        def now(cls, tz: timezone | None = None) -> "Clock":  # type: ignore[override]
            return cls.fromtimestamp(at.timestamp(), tz)

    with mock.patch.object(source_refresh, "datetime", Clock):
        return source_refresh.render(report, write=False)


def lists_findings(report: Path) -> bool:
    """Whether the report counts a source that `--check` fails on."""
    counts = COUNT.findall(report.read_text(encoding="utf-8"))
    return any(int(count) for name, count in counts if name in source_refresh.ACTIONABLE)


class RenderedReportTests(unittest.TestCase):
    def test_the_report_matches_the_fixture_the_native_parser_reads(self) -> None:
        """A change to the renderer must reach the native outcome command's tests.

        If this fails, write the rendered text to the fixture, then run
        `cargo test` in tools/accounting-skills to confirm sweep-outcome still
        parses it.
        """
        categories = (
            source_refresh.UNCHANGED, source_refresh.CHANGED, source_refresh.MISSING,
            source_refresh.UNREADABLE, source_refresh.REVIEW_DUE,
            source_refresh.BASELINE_REQUIRED, source_refresh.BLOCKED,
            source_refresh.UNREACHABLE, source_refresh.RECORDED, source_refresh.SCHEDULED,
        )
        self.assertEqual(
            report_text(dict.fromkeys(categories, 1)),
            RENDERED_REPORT.read_text(encoding="utf-8"),
        )


class SourceRefreshExitTests(unittest.TestCase):
    """The statuses the outcome command relies on."""

    def index(self, directory: Path, records: list[dict[str, object]]) -> Path:
        """One index file; the sweep is pointed at it by stubbing discovery, never the network."""
        skill = directory / "example-skill"
        skill.mkdir(parents=True)
        path = skill / "sources.json"
        path.write_text(json.dumps({"skill": "example-skill", "sources": records}), encoding="utf-8")
        return path

    def test_read_only_runs_require_a_persisted_destination_baseline(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            record = {
                "url": "https://example.test/page", "checked_at": "2026-09-08",
                "fact": "Read the primary source at use time.", "http_status": 200,
                "final_url": "https://example.test/old", "content_hash": "a" * 64,
                "content_hash_covers": source_refresh.HTML_KIND,
            }
            index = self.index(Path(directory) / "skills", [record])
            original = index.read_bytes()
            report = Path(directory) / "sweep.md"
            response = fetched()

            def run(*extra: str) -> tuple[int, bool]:
                """The exit status, and whether the report it wrote lists findings."""
                report.unlink(missing_ok=True)
                with mock.patch.object(source_refresh, "index_files", return_value=[index]), \
                        mock.patch.object(source_refresh, "fetch", return_value=response), \
                        redirect_stdout(io.StringIO()):
                    code = source_refresh.main(["--check", "--report", str(report), "--spacing", "0", *extra],
                                               skills=index.parent.parent)
                return code, lists_findings(report)

            for _ in range(2):
                self.assertEqual(run(), (2, True))
                self.assertEqual(index.read_bytes(), original)
                self.assertIn("baseline-required", report.read_text(encoding="utf-8"))
            self.assertEqual(run("--write"), (2, True))
            saved = json.loads(index.read_text(encoding="utf-8"))["sources"][0]
            self.assertEqual(saved["content_url"], "")
            self.assertEqual(saved["pending_review"]["content_url"], response.final_url)
            self.assertEqual(saved["checked_at"], record["checked_at"])
            self.assertEqual(saved["fact"], record["fact"])
            self.assertEqual(run(), (2, True))
            candidate = saved.pop("pending_review")
            for key in ("content_hash", "content_hash_covers", "content_url", "source_last_modified"):
                saved[key] = candidate[key]
            saved["checked_at"] = saved["review_required_since"]
            saved["reviewed_content"] = {key: saved[key] for key in
                                        ("content_hash", "content_hash_covers", "content_url", "source_last_modified", "checked_at")}
            index.write_text(json.dumps({"skill": "example-skill", "sources": [saved]}), encoding="utf-8")
            self.assertEqual(run(), (0, False))
            response.final_url = "https://example.test/new"
            self.assertEqual(run(), (2, True))
            self.assertIn("Source destination changed", report.read_text(encoding="utf-8"))

    def test_an_empty_source_set_exits_1_and_writes_no_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skills = self.index(Path(directory) / "skills", [])
            report = Path(directory) / "sweep.md"
            with mock.patch.object(source_refresh, "index_files", return_value=iter([skills])):
                with redirect_stderr(io.StringIO()):
                    code = source_refresh.main(["--check", "--report", str(report), "--spacing", "0"],
                                               skills=skills.parent.parent)
            self.assertEqual(code, 1)
            self.assertFalse(report.exists())

    def test_a_report_writing_failure_raises_instead_of_exiting_0(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skills = self.index(
                Path(directory) / "skills", [{"url": "https://example.test/page", "checked_at": "2026-09-08"}]
            )
            report = Path(directory) / "missing-directory" / "sweep.md"
            with mock.patch.object(source_refresh, "index_files", return_value=iter([skills])):
                with mock.patch.object(source_refresh, "fetch", return_value=fetched()):
                    with redirect_stdout(io.StringIO()), self.assertRaises(OSError):
                        source_refresh.main(["--check", "--report", str(report), "--spacing", "0"],
                                            skills=skills.parent.parent)

    def test_a_fetch_exception_raises_instead_of_exiting_0(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skills = self.index(
                Path(directory) / "skills", [{"url": "https://example.test/page", "checked_at": "2026-09-08"}]
            )
            with mock.patch.object(source_refresh, "index_files", return_value=iter([skills])):
                with mock.patch.object(source_refresh, "fetch", side_effect=RuntimeError("boom")):
                    with self.assertRaisesRegex(RuntimeError, "boom"):
                        source_refresh.main(["--check", "--spacing", "0"], skills=skills.parent.parent)


class WorkflowTests(unittest.TestCase):
    def test_a_reissued_issue_keeps_the_monitoring_label(self) -> None:
        """Clean runs close the issue, so the next finding creates a new one."""
        workflow = (REPOSITORY / ".github/workflows/source-sweep.yml").read_text(encoding="utf-8")
        creates = [line for line in workflow.splitlines() if "gh issue create" in line]
        self.assertTrue(creates)
        for line in creates:
            self.assertIn("--label monitoring", line)


if __name__ == "__main__":
    unittest.main()
