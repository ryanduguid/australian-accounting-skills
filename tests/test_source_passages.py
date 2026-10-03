import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import source_passages
import source_refresh


class SourcePassageTests(unittest.TestCase):
    def test_bounded_comparison_and_same_positive_control(self):
        base = {"url": "https://www.ato.gov.au/", "final_url": "https://www.ato.gov.au/",
                "available": True, "source_digest": "a" * 64, "text": "old\n" * 100,
                "text_truncated": False}
        self.assertEqual(source_passages.compare(base, base)["status"], "same")
        changed = {**base, "text": "new\n" * 100, "source_digest": "b" * 64}
        result = source_passages.compare(base, changed)
        self.assertEqual(result["status"], "different")
        self.assertEqual(len(result["passage_diff"]), 60)
        self.assertTrue(result["comparison_truncated"])
        self.assertEqual(source_passages.compare(base, {**changed, "available": False})["status"], "unavailable")
        self.assertEqual(source_passages.compare(base, {**changed, "url": "other"})["status"], "unavailable")

    def test_capture_uses_index_and_does_not_change_human_review(self):
        files = list(source_refresh.index_files())
        hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in files}
        url = next(str(record["url"]) for _, _, record in source_refresh.records(files))
        fetched = source_refresh.Fetched(200, url, "digest", "readable", "text/plain", "", "", text="fabricated")
        with mock.patch.object(source_refresh, "fetch", return_value=fetched) as fetch:
            result = source_passages.snapshot(url)
            self.assertTrue(result["available"])
            fetch.assert_called_once_with(source_passages.indexed_url(url), include_text=True)
        self.assertEqual(hashes, {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in files})
        with self.assertRaises(ValueError):
            source_passages.indexed_url("https://www.ato.gov.au/unindexed-path")

    def test_snapshot_integrity_size_and_overwrite_guards(self):
        url = next(str(record["url"]) for _, _, record in source_refresh.records(source_refresh.index_files()))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "snapshot.json"
            value = {"text": "changed", "text_sha256": hashlib.sha256(b"original").hexdigest(), "url": url}
            path.write_text(json.dumps(value))
            with self.assertRaises(ValueError):
                source_passages.load_snapshot(path)
            for field in ("url", "final_url"):
                malformed = {"text": "", "text_sha256": hashlib.sha256(b"").hexdigest(),
                             "url": url, "final_url": url, field: 123}
                path.write_text(json.dumps(malformed))
                with self.assertRaises(ValueError):
                    source_passages.load_snapshot(path)
            path.write_bytes(b"x" * (1024 * 1024 + 1))
            with self.assertRaises(ValueError):
                source_passages.load_snapshot(path)
            with self.assertRaises(SystemExit):
                source_passages.main(["snapshot", "--url", url, "--output", str(path)])
