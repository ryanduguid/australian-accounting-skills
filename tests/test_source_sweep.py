# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: Apache-2.0
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
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock

import yaml

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
            source_refresh.UNREACHABLE, source_refresh.CLIENT_RENDERED,
            source_refresh.RECORDED, source_refresh.SCHEDULED,
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


# Stands in for gh: logs each call, keeps each body file it is given, and
# answers the issue lookup, issue creation and comment listing.
FAKE_GH = """#!/usr/bin/env bash
printf '%s\\n' "$*" >> "$GH_LOG"
for arg in "$@"; do
  if [ "$take" = 1 ]; then cp "$arg" "$BODIES/$(ls "$BODIES" | wc -l).md"; fi
  take=0; [ "$arg" = --body-file ] && take=1
done
case "$1 $2" in
  "issue list") printf '%s\\n' "$EXISTING" ;;
  "issue create") echo https://github.com/o/r/issues/77 ;;
  "api --paginate") printf '7\\n8\\n' ;;
esac
"""


@unittest.skipUnless(shutil.which("bash") and shutil.which("awk"), "needs bash and awk")
class IssueFilingTests(unittest.TestCase):
    """Every report row must reach the issue, which outlives the run artifact."""

    MARKER = "<!-- source-sweep continuation -->"
    HEADER = "| Outcome | Skill | Source | Reviewed | Upstream | Detail |\n| --- | --- | --- | --- | --- | --- |\n"

    def file(self, report: str, existing: str) -> tuple[list[str], list[str]]:
        workflow = yaml.safe_load((REPOSITORY / ".github/workflows/source-sweep.yml").read_text(encoding="utf-8"))
        step = next(s for s in workflow["jobs"]["file"]["steps"] if s.get("name") == "File the result")
        self.assertEqual(step["env"]["MARKER"], self.MARKER)
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            (work / "bin").mkdir()
            (work / "bodies").mkdir()
            (work / "bin/gh").write_text(FAKE_GH, encoding="utf-8", newline="\n")
            (work / "bin/gh").chmod(0o755)
            (work / "sweep.md").write_text(report, encoding="utf-8", newline="\n")
            (work / "step.sh").write_text(step["run"], encoding="utf-8", newline="\n")
            env = dict(os.environ, PATH=f"{work / 'bin'}{os.pathsep}{os.environ['PATH']}", MARKER=self.MARKER,
                       GH_LOG=str(work / "gh.log"), BODIES=str(work / "bodies"), EXISTING=existing,
                       TITLE="Primary source sweep", GH_REPO="o/r")
            subprocess.run(["bash", "-e", "step.sh"], cwd=work, env=env, check=True, capture_output=True)
            calls = (work / "gh.log").read_text(encoding="utf-8").splitlines()
            bodies = sorted(work.joinpath("bodies").iterdir(), key=lambda path: int(path.stem))
            return calls, [path.read_text(encoding="utf-8") for path in bodies]

    def test_a_short_report_is_the_whole_body(self) -> None:
        report = "# Primary source sweep\n\n" + self.HEADER + "| changed | `a` | [x](https://example.test) | d | d | d |\n"
        calls, bodies = self.file(report, existing="12")
        self.assertEqual(bodies, [report])
        self.assertIn("issue edit 12 --body-file part-0.md", calls)
        # The previous sweep's continuation comments go, and none replace them.
        self.assertIn("api --method DELETE repos/o/r/issues/comments/7", calls)
        self.assertIn("api --method DELETE repos/o/r/issues/comments/8", calls)
        self.assertFalse([call for call in calls if call.startswith("issue comment")])

    def test_a_long_report_continues_in_comments_without_losing_a_row(self) -> None:
        rows = [f"| baseline-required | `skill-{n}` | [page {n}](https://example.test/{n}) | 2026-11-01 | not published | "
                + "A readable content or destination baseline is missing. " * 3 + "|\n" for n in range(700)]
        report = "# Primary source sweep\n\nSwept 700 records.\n\n" + self.HEADER + "".join(rows)
        calls, bodies = self.file(report, existing="")
        self.assertGreater(len(bodies), 2)
        self.assertIn("issue create --title Primary source sweep --body-file part-0.md --label monitoring", calls)
        comments = [call for call in calls if call.startswith("issue comment")]
        self.assertEqual(comments, [f"issue comment 77 --body-file part-{n}.md" for n in range(1, len(bodies))])
        self.assertTrue(bodies[0].endswith("\nThe report continues in the comments below.\n"))
        kept = bodies[0].removesuffix("\nThe report continues in the comments below.\n")
        for body in bodies:
            self.assertLessEqual(len(body.encode("utf-8")), 60100)
        for body in bodies[1:]:
            self.assertTrue(body.startswith(self.MARKER + "\n" + self.HEADER))
            kept += body.removeprefix(self.MARKER + "\n" + self.HEADER)
        self.assertEqual(kept, report)


if __name__ == "__main__":
    unittest.main()
