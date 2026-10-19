"""Command entry points and small refusals of the support scripts."""

from __future__ import annotations

import hashlib
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import yaml

REPOSITORY = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY / "scripts"))

import build_coverage  # noqa: E402
import source_fetch_policy  # noqa: E402
import source_passages  # noqa: E402
import strict_yaml  # noqa: E402
import sweep_outcome  # noqa: E402

# A URL the public source index carries, which a snapshot must name.
INDEXED_URL = "https://www.austrac.gov.au/industry-and-business/your-industry/accountants"


class TemporaryDirectory(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)


class BuildCoverageTests(TemporaryDirectory):
    def test_front_matter_needs_both_markers(self) -> None:
        for text, message in (
            ("no markers\n", "must start with '---'"),
            ("---\nid: card\n", "must end with '---'"),
        ):
            with self.subTest(message=message):
                path = self.directory / "card.md"
                path.write_text(text, encoding="utf-8")
                with self.assertRaisesRegex(ValueError, message):
                    build_coverage.front_matter(path)

    def run_main(self, *arguments: str) -> tuple[int, str, str]:
        stdout, stderr = io.StringIO(), io.StringIO()
        with redirect_stdout(stdout), redirect_stderr(stderr):
            code = build_coverage.main(list(arguments))
        return code, stdout.getvalue(), stderr.getvalue()

    def test_write_check_and_print(self) -> None:
        matrix = build_coverage.rendered(build_coverage.build())
        target = self.directory / "coverage.json"
        with mock.patch.object(build_coverage, "COVERAGE_FILE", target), \
                mock.patch.object(build_coverage, "REPOSITORY", self.directory):
            self.assertEqual(self.run_main("--check"), (2, "", (
                "coverage.json is out of date. Run: python scripts/build_coverage.py --write\n")))
            self.assertEqual(self.run_main("--write"), (0, "wrote coverage.json\n", ""))
            self.assertEqual(target.read_text(encoding="utf-8"), matrix)
            self.assertEqual(self.run_main("--check"), (0, matrix, ""))


class SourcePassagesTests(TemporaryDirectory):
    def snapshot_file(self, name: str, text: str) -> Path:
        path = self.directory / name
        path.write_text(json.dumps({
            "url": INDEXED_URL, "final_url": INDEXED_URL,
            "text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "available": True, "text_truncated": False, "source_digest": "a" * 64,
        }), encoding="utf-8")
        return path

    def test_a_snapshot_without_text_is_malformed(self) -> None:
        path = self.directory / "bad.json"
        path.write_text(json.dumps({"text": 1}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Malformed passage snapshot"):
            source_passages.load_snapshot(path)

    def test_compare_command_writes_a_new_report_or_reports_unavailable(self) -> None:
        before = self.snapshot_file("before.json", "Line one\n")
        after = self.snapshot_file("after.json", "Line two\n")
        output = self.directory / "out" / "comparison.json"
        code = source_passages.main(["compare", "--before", str(before), "--after", str(after),
                                     "--output", str(output)])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(output.read_text(encoding="utf-8"))["status"], "different")

        broken = self.directory / "broken.json"
        broken.write_text("{not json", encoding="utf-8")
        printed = io.StringIO()
        with redirect_stdout(printed):
            code = source_passages.main(["compare", "--before", str(broken), "--after", str(after),
                                         "--output", str(self.directory / "second.json")])
        self.assertEqual(code, 1)
        self.assertEqual(json.loads(printed.getvalue())["status"], "unavailable")


class SmallRefusalTests(unittest.TestCase):
    def test_redirects_are_never_followed(self) -> None:
        handler = source_fetch_policy.NoRedirect()
        # The handler ignores its request, file and headers, so placeholders stand in for them.
        refusal = handler.redirect_request(None, None, 302, "Found", {}, "https://example.test/")  # pyright: ignore[reportArgumentType]
        self.assertIsNone(refusal)

    def test_a_complex_yaml_key_is_refused(self) -> None:
        loader = strict_yaml.unique_key_safe_loader(
            ValueError, field_noun="YAML field", keys_noun="YAML mapping keys")
        with self.assertRaisesRegex(ValueError, "YAML mapping keys must be scalar"):
            yaml.load("? [a, b]\n: 1\n", Loader=loader)  # nosec B506: the strict SafeLoader subclass under test

    def test_a_failed_sweep_exit_is_not_a_result(self) -> None:
        counts: dict[str, int] = dict.fromkeys((*sweep_outcome.ACTIONABLE, *sweep_outcome.UNCHECKED), 0)
        with self.assertRaisesRegex(sweep_outcome.SweepError, "source_refresh.py exited 1"):
            sweep_outcome.decide(1, counts)


if __name__ == "__main__":
    unittest.main()
