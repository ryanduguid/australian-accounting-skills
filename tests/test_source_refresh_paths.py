# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""Source sweep paths the scenario tests in test_source_refresh.py do not reach."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "scripts"))

import source_refresh  # noqa: E402

UNCHANGED_DIGEST = "a" * 64


def fetched(**overrides: object) -> source_refresh.Fetched:
    values: dict[str, object] = {
        "status": 200, "final_url": "https://example.test/page", "digest": UNCHANGED_DIGEST,
        "kind": source_refresh.HTML_KIND, "content_type": "text/html", "last_modified": "",
        "error": "",
    }
    values.update(overrides)
    return source_refresh.Fetched(**values)  # type: ignore[arg-type]


class SkillsTree(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.skills = Path(temporary.name) / "skills"
        self.skill = self.skills / "example-skill"
        self.skill.mkdir(parents=True)
        (self.skill / "SKILL.md").write_text("# Example", encoding="utf-8")

    def index(self, sources: object, skill: str = "example-skill") -> Path:
        path = self.skill / "sources.json"
        path.write_text(json.dumps({"skill": skill, "sources": sources}), encoding="utf-8")
        return path

    def refresh(self, only_skill: str = "", only_url: str = "") -> source_refresh.Report:
        with mock.patch.object(source_refresh, "fetch", return_value=fetched()):
            return source_refresh.refresh(skills=self.skills, spacing=0, today="2026-10-03",
                                          only_skill=only_skill, only_url=only_url)


class SweepFilterTests(SkillsTree):
    def test_index_files_without_a_source_list_or_with_stray_entries_are_skipped(self) -> None:
        self.index({"not": "a list"})
        self.assertEqual(self.refresh().outcomes, [])
        self.index(["not a record", {"url": "https://example.test/page", "checked_at": "2026-09-08"}])
        self.assertEqual([outcome.url for outcome in self.refresh().outcomes], ["https://example.test/page"])

    def test_filters_and_empty_urls_skip_records(self) -> None:
        self.index([{"url": "https://example.test/page"}, {"url": ""}])
        self.assertEqual(self.refresh(only_skill="other-skill").outcomes, [])
        self.assertEqual(self.refresh(only_url="https://example.test/other").outcomes, [])
        self.assertEqual(len(self.refresh().outcomes), 1)

    def test_distinct_urls_are_spaced(self) -> None:
        self.index([{"url": "https://example.test/a"}, {"url": "https://example.test/b"}])
        with mock.patch.object(source_refresh, "fetch", return_value=fetched()), \
                mock.patch.object(source_refresh.time, "sleep") as sleep:
            source_refresh.refresh(skills=self.skills, spacing=0.5, today="2026-10-03")
        sleep.assert_called_once_with(0.5)

    def test_a_late_manual_review_also_names_a_passed_reverify_date(self) -> None:
        self.index([{
            "url": "https://example.test/page", "checked_at": "2026-01-01",
            "manual_review": {"cadence": "yearly", "next_review": "2026-02-01"},
            "reverify_by": "2026-03-01",
        }])
        detail = self.refresh().outcomes[0].detail
        self.assertIn("Manual review was due 2026-02-01", detail)
        self.assertIn("passed its reverify_by date (2026-03-01)", detail)

    def test_an_index_outside_the_skills_tree_is_refused(self) -> None:
        outside = self.skills.parent / "elsewhere" / "sources.json"
        outside.parent.mkdir()
        outside.write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "resolves outside the skills tree"):
            source_refresh.checked_index(outside, self.skills)


class FetchRetryTests(unittest.TestCase):
    def test_transport_faults_are_retried_then_reported(self) -> None:
        with mock.patch.object(source_refresh.urllib.request, "build_opener") as build, \
                mock.patch.object(source_refresh, "check_public_resolution"), \
                mock.patch.object(source_refresh.time, "sleep") as sleep:
            build.return_value.open.side_effect = OSError("connection reset")
            result = source_refresh.fetch("https://www.ato.gov.au/page", tries=2, delay=0.1)
        self.assertEqual(result.status, 0)
        self.assertEqual(result.error, "OSError: connection reset")
        self.assertEqual(build.return_value.open.call_count, 2)
        sleep.assert_called_once_with(0.1)


class UpstreamDateTests(unittest.TestCase):
    def test_an_unreadable_published_date_falls_through_to_the_next_source(self) -> None:
        body = b'<meta property="article:modified_time" content="not a date">'
        self.assertEqual(
            source_refresh.upstream_last_modified(body, "Mon, 01 Sep 2026 00:00:00 GMT",
                                                  "Wed, 03 Sep 2026 00:00:00 GMT"),
            "2026-09-01",
        )


class PreflightPathTests(SkillsTree):
    def preflight(self) -> tuple[str, int]:
        with mock.patch.object(source_refresh, "fetch", return_value=fetched()):
            return source_refresh.preflight("example-skill", skills=self.skills, today="2026-10-03", spacing=0)

    def test_a_skill_without_a_source_index(self) -> None:
        text, code = self.preflight()
        self.assertEqual(code, 1)
        self.assertIn("No source index.", text)

    def test_a_linked_source_index_is_unsupported(self) -> None:
        target = self.skills.parent / "real-sources.json"
        target.write_text(json.dumps({"skill": "example-skill", "sources": []}), encoding="utf-8")
        try:
            os.symlink(target, self.skill / "sources.json")
        except OSError as error:
            self.skipTest(f"file links are unavailable: {error}")
        text, code = self.preflight()
        self.assertEqual(code, 1)
        self.assertIn("Linked source index is unsupported.", text)

    def test_an_unparsable_source_index_is_invalid(self) -> None:
        (self.skill / "sources.json").write_text("{not json", encoding="utf-8")
        text, code = self.preflight()
        self.assertEqual(code, 1)
        self.assertIn("Invalid source index:", text)

    def test_a_sweep_that_loses_records_is_incomplete(self) -> None:
        self.index([{"url": "https://example.test/page", "checked_at": "2026-09-26"}])
        with mock.patch.object(source_refresh, "refresh", return_value=source_refresh.Report()):
            text, code = source_refresh.preflight("example-skill", skills=self.skills, today="2026-10-03")
        self.assertEqual(code, 1)
        self.assertIn("Source inventory changed or was incomplete.", text)

    def test_preflight_command_without_a_report_file_prints_only(self) -> None:
        printed = StringIO()
        with mock.patch.object(source_refresh, "preflight", return_value=("rendered", 0)), \
                redirect_stdout(printed):
            code = source_refresh.main(["--preflight", "--skill", "example-skill"], skills=self.skills)
        self.assertEqual(code, 0)
        self.assertEqual(printed.getvalue(), "rendered\n")


if __name__ == "__main__":
    unittest.main()
