"""What the sweep workflow may conclude from an exit status and a report.

Every case here is one where the old workflow would have reported a healthy run,
closed the issue, or filed findings without a report to back them.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "scripts"))

import source_refresh  # noqa: E402
import sweep_outcome  # noqa: E402

STARTED = datetime(2026, 9, 20, 19, 0, 5, tzinfo=timezone.utc)


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
    """Render a real report through source_refresh so the parser tracks the renderer."""
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


class OutcomeTests(unittest.TestCase):
    def setUp(self) -> None:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.report = Path(directory.name) / "sweep.md"

    def write(self, outcomes: dict[str, int], at: datetime = STARTED) -> None:
        self.report.write_text(report_text(outcomes, at), encoding="utf-8")

    def outcome(self, status: int) -> sweep_outcome.Outcome:
        return sweep_outcome.outcome(status, self.report, STARTED)

    def test_exit_0_with_a_clean_current_report_is_clean(self) -> None:
        self.write({source_refresh.UNCHANGED: 3})
        result = self.outcome(0)
        self.assertEqual(result.name, "clean")
        self.assertEqual(result.comment, "Every indexed source was retrieved and none had moved.")

    def test_exit_2_with_a_findings_report_is_findings(self) -> None:
        self.write({source_refresh.UNCHANGED: 2, source_refresh.CHANGED: 1, source_refresh.MISSING: 1})
        result = self.outcome(2)
        self.assertEqual(result.name, "findings")
        self.assertIn("2 sources need an edit", result.comment)

    def test_exit_1_fails(self) -> None:
        self.write({source_refresh.UNCHANGED: 3})
        with self.assertRaisesRegex(sweep_outcome.SweepError, "exited 1"):
            self.outcome(1)

    def test_unexpected_exit_codes_fail(self) -> None:
        self.write({source_refresh.UNCHANGED: 3})
        for status in (3, 127, -1):
            with self.subTest(status=status), self.assertRaisesRegex(sweep_outcome.SweepError, "exited"):
                self.outcome(status)

    def test_exit_0_or_2_without_a_report_fails(self) -> None:
        """An argparse failure also exits 2, and writes nothing."""
        for status in (0, 2):
            with self.subTest(status=status), self.assertRaisesRegex(sweep_outcome.SweepError, "no report"):
                self.outcome(status)

    def test_a_report_that_contradicts_the_status_fails(self) -> None:
        self.write({source_refresh.CHANGED: 1})
        with self.assertRaisesRegex(sweep_outcome.SweepError, "exit 0 with a report that lists 1"):
            self.outcome(0)
        self.write({source_refresh.UNCHANGED: 1})
        with self.assertRaisesRegex(sweep_outcome.SweepError, "exit 2 with a report that lists nothing"):
            self.outcome(2)

    def test_a_stale_report_from_an_earlier_run_fails(self) -> None:
        self.write({source_refresh.UNCHANGED: 3}, at=STARTED - timedelta(minutes=2))
        with self.assertRaisesRegex(sweep_outcome.SweepError, "before this run started"):
            self.outcome(0)

    def test_a_report_written_in_the_same_minute_as_the_start_is_current(self) -> None:
        self.write({source_refresh.UNCHANGED: 3}, at=STARTED - timedelta(seconds=4))
        self.assertEqual(self.outcome(0).name, "clean")

    def test_an_empty_or_malformed_report_fails(self) -> None:
        for text, message in (
            ("", "sweep header"),
            ("# Primary source sweep\n\nnothing\n", "Swept N records"),
            (report_text({}), "covers no records"),
            (report_text({source_refresh.UNCHANGED: 1}).replace("- blocked", "- other"), "no count for blocked"),
        ):
            with self.subTest(text=text[:30]):
                self.report.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(sweep_outcome.SweepError, message):
                    self.outcome(0)

    def test_blocked_and_unreachable_sources_are_never_reported_as_checked(self) -> None:
        self.write({source_refresh.UNCHANGED: 5, source_refresh.BLOCKED: 7, source_refresh.UNREACHABLE: 1})
        result = self.outcome(0)
        self.assertEqual(result.name, "clean")
        self.assertNotIn("Every indexed source", result.comment)
        self.assertIn("7 blocked and 1 unreachable sources could not be checked", result.comment)


class MainTests(unittest.TestCase):
    def run_main(self, argv: list[str], output: Path | None = None) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        env = {"GITHUB_OUTPUT": str(output)} if output else {}
        with mock.patch.dict(os.environ, env, clear=True):
            with redirect_stdout(out), redirect_stderr(err):
                code = sweep_outcome.main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_the_outcome_goes_to_stdout_for_the_workflow_to_redirect(self) -> None:
        """source-sweep.yml appends this script's stdout to $GITHUB_OUTPUT.

        The script must not append to that file as well: two writers put every
        key in twice, and reading the path out of the environment made it a
        path-injection sink.
        """
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "sweep.md"
            report.write_text(report_text({source_refresh.UNCHANGED: 1}), encoding="utf-8")
            output = Path(directory) / "output"
            code, out, err = self.run_main(
                ["--status", "0", "--report", str(report), "--started", "2026-09-20T19:00:05Z"], output
            )
            self.assertEqual((code, err), (0, ""))
            self.assertIn("outcome=clean\n", out)
            self.assertFalse(output.exists())

    def test_reports_a_failure_and_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "sweep.md"
            for argv in (
                ["--status", "1", "--report", str(report), "--started", "2026-09-20T19:00:05Z"],
                ["--status", "0", "--report", str(report), "--started", "2026-09-20T19:00:05Z"],
                ["--status", "0", "--report", str(report), "--started", "yesterday"],
            ):
                with self.subTest(argv=argv):
                    code, out, err = self.run_main(argv)
                    self.assertEqual((code, out), (1, ""))
                    self.assertTrue(err.startswith("FAIL "))


class SourceRefreshExitTests(unittest.TestCase):
    """The statuses the outcome script relies on."""

    def index(self, directory: Path, records: list[dict[str, object]]) -> Path:
        """One index file; the sweep is pointed at it by stubbing discovery, never the network."""
        skill = directory / "example-skill"
        skill.mkdir(parents=True)
        path = skill / "sources.json"
        path.write_text(json.dumps({"skill": "example-skill", "sources": records}), encoding="utf-8")
        return path

    def test_an_empty_source_set_exits_1_and_writes_no_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skills = self.index(Path(directory) / "skills", [])
            report = Path(directory) / "sweep.md"
            with mock.patch.object(source_refresh, "index_files", return_value=iter([skills])):
                with redirect_stderr(io.StringIO()):
                    code = source_refresh.main(["--check", "--report", str(report), "--spacing", "0"])
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
                        source_refresh.main(["--check", "--report", str(report), "--spacing", "0"])

    def test_a_fetch_exception_raises_instead_of_exiting_0(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            skills = self.index(
                Path(directory) / "skills", [{"url": "https://example.test/page", "checked_at": "2026-09-08"}]
            )
            with mock.patch.object(source_refresh, "index_files", return_value=iter([skills])):
                with mock.patch.object(source_refresh, "fetch", side_effect=RuntimeError("boom")):
                    with self.assertRaisesRegex(RuntimeError, "boom"):
                        source_refresh.main(["--check", "--spacing", "0"])


if __name__ == "__main__":
    unittest.main()
