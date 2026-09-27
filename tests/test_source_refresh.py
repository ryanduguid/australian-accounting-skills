"""What the source sweep must never do quietly.

The sweep exists to say which primary sources moved. Every failure mode worth
a test here is one where it would keep answering "nothing moved" while being
wrong, because that answer is indistinguishable from a healthy run and nobody
would look again until the next hand review.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[1]

# `scripts/` is a directory of standalone entry points, not a package, so it is
# put on the path rather than imported through a parent module. `mypy_path` in
# pyproject.toml points the type checker at the same directory.
sys.path.insert(0, str(REPOSITORY / "scripts"))

import source_refresh  # noqa: E402

HTML = "text/html"
UNCHANGED_DIGEST = "a" * 64


def fetched(**overrides: object) -> source_refresh.Fetched:
    defaults: dict[str, object] = {
        "status": 200,
        "final_url": "https://example.test/page",
        "digest": UNCHANGED_DIGEST,
        "kind": source_refresh.HTML_KIND,
        "content_type": HTML,
        "last_modified": "",
        "error": "",
    }
    defaults.update(overrides)
    return source_refresh.Fetched(**defaults)  # type: ignore[arg-type]


class ReadableTextTests(unittest.TestCase):
    def test_an_omitted_head_close_does_not_swallow_the_document(self) -> None:
        """HTML5 makes `</head>` optional and HTMLParser does not supply one.

        While `head` was skipped, a page that omits the closing tag left the
        skip open for the whole document, the digest covered an empty string,
        and every later sweep reported that page unchanged whatever it said.
        """
        omitted = b"<html><head><title>T</title><body><p>Body text</p></body></html>"
        closed = b"<html><head><title>T</title></head><body><p>Body text</p></body></html>"
        self.assertIn("Body text", source_refresh.readable_text(omitted, "utf-8"))
        self.assertEqual(
            source_refresh.readable_text(omitted, "utf-8"),
            source_refresh.readable_text(closed, "utf-8"),
        )

    def test_scripts_and_styles_stay_out_of_the_digest(self) -> None:
        markup = b"<html><body><style>p{color:red}</style><script>var a=1</script><p>Real</p></body></html>"
        text = source_refresh.readable_text(markup, "utf-8")
        self.assertEqual(text, "Real")

    def test_a_main_region_excludes_the_page_furniture_around_it(self) -> None:
        markup = b"<html><body><nav>menu</nav><main><p>Content</p></main><footer>foot</footer></body></html>"
        self.assertEqual(source_refresh.readable_text(markup, "utf-8"), "Content")


class DigestTests(unittest.TestCase):
    def test_a_pdf_is_hashed_as_bytes_not_parsed_as_markup(self) -> None:
        """Six indexed sources are PDFs. An HTML parser cannot read one.

        Decoding PDF bytes as text replaces everything undecodable and leaves
        object tables and font data standing in for the document.
        """
        digest, kind = source_refresh.body_digest(b"%PDF-1.4 ...", "application/pdf", None)
        self.assertEqual(kind, source_refresh.BYTES_KIND)
        self.assertRegex(digest, r"^[0-9a-f]{64}$")

    def test_markup_that_yields_no_text_produces_no_digest(self) -> None:
        """An empty digest would compare equal for ever."""
        digest, kind = source_refresh.body_digest(b"<html><body></body></html>", HTML, "utf-8")
        self.assertEqual(digest, "")
        self.assertEqual(kind, source_refresh.HTML_KIND)

    def test_an_empty_body_produces_no_digest(self) -> None:
        self.assertEqual(source_refresh.body_digest(b"", "application/pdf", None)[0], "")


class ClassifyTests(unittest.TestCase):
    def record(self, **overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "url": "https://example.test/page",
            "checked_at": "2026-09-08",
            source_refresh.DIGEST_FIELD: UNCHANGED_DIGEST,
            source_refresh.DIGEST_KIND_FIELD: source_refresh.HTML_KIND,
            source_refresh.CONTENT_URL_FIELD: "https://example.test/page",
            source_refresh.FETCHED_FIELD: "2026-09-16",
        }
        base.update(overrides)
        return base

    def test_a_matching_digest_is_unchanged(self) -> None:
        outcome, _ = source_refresh.classify(self.record(), fetched())
        self.assertEqual(outcome, source_refresh.UNCHANGED)

    def test_a_different_digest_is_changed(self) -> None:
        outcome, _ = source_refresh.classify(self.record(), fetched(digest="b" * 64))
        self.assertEqual(outcome, source_refresh.CHANGED)

    def test_a_changed_destination_is_reported_even_when_the_text_matches(self) -> None:
        previous = "https://example.test/old"
        current = "https://example.test/new"
        for kind in (source_refresh.HTML_KIND, source_refresh.BYTES_KIND):
            with self.subTest(kind=kind):
                outcome, detail = source_refresh.classify(
                    self.record(content_url=previous), fetched(final_url=current, kind=kind)
                )
                self.assertEqual(outcome, source_refresh.CHANGED)
                self.assertIn(previous, detail)
                self.assertIn(current, detail)

    def test_an_unchanged_destination_ignores_fragments(self) -> None:
        for previous in ("https://example.test/page", "https://example.test/page#section"):
            with self.subTest(previous=previous):
                outcome, _ = source_refresh.classify(
                    self.record(content_url=previous), fetched()
                )
                self.assertEqual(outcome, source_refresh.UNCHANGED)

    def test_an_existing_redirect_is_not_reported_again(self) -> None:
        destination = "https://example.test/current"
        outcome, _ = source_refresh.classify(
            self.record(url="https://example.test/legacy", content_url=destination),
            fetched(final_url=destination),
        )
        self.assertEqual(outcome, source_refresh.UNCHANGED)

    def test_a_first_destination_does_not_invent_a_change(self) -> None:
        outcome, _ = source_refresh.classify(
            self.record(content_hash="", content_url=""),
            fetched(final_url="https://example.test/new"),
        )
        self.assertEqual(outcome, source_refresh.BASELINE_REQUIRED)

    def test_a_different_failure_destination_keeps_its_failure_outcome(self) -> None:
        for status, expected in (
            (200, source_refresh.UNREADABLE),
            (404, source_refresh.MISSING),
            (403, source_refresh.BLOCKED),
            (0, source_refresh.UNREACHABLE),
        ):
            with self.subTest(status=status):
                outcome, _ = source_refresh.classify(
                    self.record(content_url="https://example.test/old"),
                    fetched(status=status, digest=""),
                )
                self.assertEqual(outcome, expected)

    def test_a_legacy_record_requires_a_baseline_without_trusting_the_last_attempt(self) -> None:
        for status in (0, 200, 403, 404):
            with self.subTest(status=status):
                record = self.record(final_url="https://example.test/old", http_status=status)
                del record[source_refresh.CONTENT_URL_FIELD]
                outcome, detail = source_refresh.classify(record, fetched())
                self.assertEqual(outcome, source_refresh.BASELINE_REQUIRED)
                self.assertIn("destination baseline", detail)
                self.assertEqual(
                    source_refresh.classify(record, fetched(kind=source_refresh.BYTES_KIND))[0],
                    source_refresh.BASELINE_REQUIRED,
                )
                self.assertEqual(
                    source_refresh.classify(record, fetched(digest="b" * 64))[0],
                    source_refresh.CHANGED,
                )
                source_refresh.apply_fetch(record, fetched(), "2026-09-16")
                self.assertEqual(source_refresh.classify(record, fetched())[0], source_refresh.UNCHANGED)
                self.assertEqual(
                    source_refresh.classify(record, fetched(final_url="https://example.test/new"))[0],
                    source_refresh.CHANGED,
                )

    def test_a_readable_response_with_no_digest_is_a_fault_here(self) -> None:
        outcome, detail = source_refresh.classify(self.record(), fetched(digest=""))
        self.assertEqual(outcome, source_refresh.UNREADABLE)
        self.assertIn("source_refresh.py", detail)

    def test_a_digest_from_a_different_reading_is_re_recorded_not_compared(self) -> None:
        """Changing how a response is read is not the source changing.

        A stored hash of a PDF's readable text and a hash of its bytes are not
        comparable, and reporting the difference as a content change would send
        a reviewer to a page that never moved.
        """
        outcome, _ = source_refresh.classify(
            self.record(),
            fetched(kind=source_refresh.BYTES_KIND, content_type="application/pdf"),
        )
        self.assertEqual(outcome, source_refresh.RECORDED)

    def test_a_record_without_a_digest_requires_a_baseline(self) -> None:
        outcome, _ = source_refresh.classify(
            self.record(**{source_refresh.DIGEST_FIELD: ""}), fetched()
        )
        self.assertEqual(outcome, source_refresh.BASELINE_REQUIRED)

    def test_the_failure_outcomes_say_what_to_do_about_them(self) -> None:
        """Three failures, three different actions, so three outcomes."""
        for status, expected in (
            (404, source_refresh.MISSING),
            (410, source_refresh.MISSING),
            (403, source_refresh.BLOCKED),
            (429, source_refresh.BLOCKED),
        ):
            with self.subTest(status=status):
                outcome, _ = source_refresh.classify(
                    self.record(), fetched(status=status, digest="", error=f"HTTP {status}")
                )
                self.assertEqual(outcome, expected)

        outcome, _ = source_refresh.classify(
            self.record(), fetched(status=0, digest="", error="TimeoutError: timed out")
        )
        self.assertEqual(outcome, source_refresh.UNREACHABLE)

    def test_check_fails_only_on_what_an_edit_here_can_fix(self) -> None:
        """An alert that can never be cleared is one nobody reads.

        legislation.nsw.gov.au refuses automated retrieval to every user agent,
        so 7 records can never come back clean from CI. Failing the scheduled
        run on them would hold its issue open for ever and train the reader to
        ignore it, taking the real findings with it. An overdue manual review is
        different: the review itself clears it.
        """
        self.assertEqual(
            set(source_refresh.ACTIONABLE),
            {source_refresh.CHANGED, source_refresh.MISSING, source_refresh.UNREADABLE,
             source_refresh.REVIEW_DUE, source_refresh.BASELINE_REQUIRED},
        )
        for outcome in (source_refresh.BLOCKED, source_refresh.UNREACHABLE):
            with self.subTest(outcome=outcome):
                self.assertNotIn(outcome, source_refresh.ACTIONABLE)
                self.assertIn(
                    outcome,
                    source_refresh.NEEDS_ATTENTION,
                    "a blocked source must still appear in the report",
                )

    def test_every_failure_outcome_asks_for_attention(self) -> None:
        for outcome in (
            source_refresh.CHANGED,
            source_refresh.MISSING,
            source_refresh.BLOCKED,
            source_refresh.UNREACHABLE,
            source_refresh.UNREADABLE,
        ):
            with self.subTest(outcome=outcome):
                self.assertIn(outcome, source_refresh.NEEDS_ATTENTION)


class FetchTests(unittest.TestCase):
    def test_an_http_error_records_the_resolved_destination(self) -> None:
        destination = "https://example.test/redirected"
        error = urllib.error.HTTPError(destination, 404, "Not Found", None, None)
        with mock.patch.object(source_refresh.urllib.request, "urlopen", side_effect=error):
            result = source_refresh.fetch("https://example.test/page", tries=1, delay=0)
        self.assertEqual(result.status, 404)
        self.assertEqual(result.final_url, destination)
        record: dict[str, object] = {"url": "https://example.test/page"}
        source_refresh.apply_fetch(record, fetched(final_url="https://example.test/old"), "2026-09-15")
        source_refresh.apply_fetch(record, result, "2026-09-16")
        self.assertEqual(record[source_refresh.FINAL_URL_FIELD], destination)
        self.assertEqual(record[source_refresh.CONTENT_URL_FIELD], "https://example.test/old")


class ApplyFetchTests(unittest.TestCase):
    def test_a_first_failed_write_does_not_establish_a_destination(self) -> None:
        for status in (0, 403, 404, 200):
            with self.subTest(status=status):
                record: dict[str, object] = {"url": "https://example.test/page"}
                source_refresh.apply_fetch(record, fetched(status=status, digest=""), "2026-09-16")
                self.assertEqual(set(record) - {"url"}, set(source_refresh.MACHINE_FIELDS))
                self.assertEqual(record[source_refresh.CONTENT_URL_FIELD], "")
                self.assertEqual(
                    source_refresh.classify(record, fetched(final_url="https://example.test/new"))[0],
                    source_refresh.BASELINE_REQUIRED,
                )

    def test_recovery_compares_with_the_last_readable_destination(self) -> None:
        for status in (0, 403, 404, 200):
            for destination, expected in (
                ("https://example.test/old", source_refresh.UNCHANGED),
                ("https://example.test/new", source_refresh.CHANGED),
            ):
                with self.subTest(status=status, destination=destination):
                    record: dict[str, object] = {"url": "https://example.test/page"}
                    source_refresh.apply_fetch(
                        record, fetched(final_url="https://example.test/old"), "2026-09-15"
                    )
                    source_refresh.apply_fetch(
                        record, fetched(status=status, digest=""), "2026-09-16"
                    )
                    source_refresh.apply_fetch(
                        record, fetched(status=status, digest="", final_url="https://example.test/temporary"),
                        "2026-09-17",
                    )
                    self.assertEqual(record[source_refresh.CONTENT_URL_FIELD], "https://example.test/old")
                    self.assertEqual(record[source_refresh.FINAL_URL_FIELD], "https://example.test/temporary")
                    self.assertEqual(record[source_refresh.STATUS_FIELD], status)
                    self.assertEqual(
                        source_refresh.classify(record, fetched(final_url=destination))[0], expected
                    )

    def test_a_sweep_writes_every_machine_field_and_only_those(self) -> None:
        """A write supplies the whole machine-field set.

        A partially written record reads as a checked source while missing the
        field that would have shown otherwise.
        """
        record: dict[str, object] = {"url": "https://example.test/page", "checked_at": "2026-09-08"}
        source_refresh.apply_fetch(record, fetched(), "2026-09-16")
        self.assertEqual(
            set(record) - {"url", "checked_at"}, set(source_refresh.MACHINE_FIELDS)
        )

    def test_a_sweep_never_touches_the_human_review_date(self) -> None:
        record: dict[str, object] = {"url": "https://example.test/page", "checked_at": "2026-09-08"}
        source_refresh.apply_fetch(record, fetched(), "2026-09-16")
        self.assertEqual(record["checked_at"], "2026-09-08")
        self.assertEqual(record[source_refresh.FETCHED_FIELD], "2026-09-16")

    def test_an_unreadable_response_never_overwrites_a_good_digest(self) -> None:
        """Losing a digest to one bad sweep would restart the comparison."""
        record: dict[str, object] = {
            "url": "https://example.test/page",
            "checked_at": "2026-09-08",
            source_refresh.DIGEST_FIELD: UNCHANGED_DIGEST,
            source_refresh.DIGEST_KIND_FIELD: source_refresh.HTML_KIND,
        }
        source_refresh.apply_fetch(record, fetched(status=404, digest="", error="HTTP 404"), "2026-09-16")
        self.assertEqual(record[source_refresh.DIGEST_FIELD], UNCHANGED_DIGEST)
        self.assertEqual(record[source_refresh.STATUS_FIELD], 404)


class UpstreamDateTests(unittest.TestCase):
    def test_the_three_observed_date_shapes_reduce_to_one_spelling(self) -> None:
        self.assertEqual(source_refresh.iso_day("2026-06-29T13:18:58Z"), "2026-06-29")
        self.assertEqual(source_refresh.iso_day("2026-08-10"), "2026-08-10")
        self.assertEqual(
            source_refresh.iso_day("Tue, 15 Sep 2026 12:58:04 GMT"), "2026-09-15"
        )
        self.assertEqual(source_refresh.iso_day("not a date"), "")

    def test_markup_beats_a_header(self) -> None:
        body = b'<script type="application/ld+json">{"dateModified":"2026-06-29T13:18:58Z"}</script>'
        self.assertEqual(
            source_refresh.upstream_last_modified(body, "Tue, 15 Sep 2026 12:58:04 GMT", None),
            "2026-06-29",
        )

    def test_a_last_modified_that_repeats_the_request_time_is_not_a_content_date(self) -> None:
        """A page rendered per request stamps the header with now.

        Recording that would put today's date in every record on every sweep
        and the field would stop meaning anything.
        """
        same_day = "Tue, 15 Sep 2026 12:58:04 GMT"
        served = "Tue, 15 Sep 2026 18:01:45 GMT"
        self.assertEqual(source_refresh.upstream_last_modified(b"", same_day, served), "")
        older = "Mon, 01 Sep 2026 01:00:00 GMT"
        self.assertEqual(source_refresh.upstream_last_modified(b"", older, served), "2026-09-01")


class SweepTests(unittest.TestCase):
    def temporary_skills_directory(self) -> Path:
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        return Path(directory.name) / "skills"

    def test_a_new_destination_fails_check_and_preserves_review_fields(self) -> None:
        skills = self.temporary_skills_directory()
        skill = skills / "example-skill"
        skill.mkdir(parents=True)
        record = {
            "url": "https://example.test/page",
            "checked_at": "2026-09-08",
            "fact": "A discovery link, not approval of a current rule.",
            "verification_status": "indexed-source-discovery-only",
            "limitations": "Read the authority at use time.",
            "final_url": "https://example.test/old",
            "content_url": "https://example.test/old",
            "content_hash": UNCHANGED_DIGEST,
            "content_hash_covers": source_refresh.HTML_KIND,
        }
        path = skill / "sources.json"
        path.write_text(json.dumps({"skill": "example-skill", "sources": [record]}),
                        encoding="utf-8")
        with mock.patch.object(source_refresh, "fetch", return_value=fetched()):
            report = source_refresh.refresh(skills=skills, spacing=0, write=True)
        with mock.patch.object(source_refresh, "refresh", return_value=report), \
                mock.patch("sys.stdout"):
            self.assertEqual(source_refresh.main(["--check"]), 2)
        rendered = source_refresh.render(report, write=True)
        self.assertIn("https://example.test/old", rendered)
        self.assertIn("https://example.test/page", rendered)
        saved = json.loads(path.read_text(encoding="utf-8"))["sources"][0]
        for key in ("checked_at", "fact", "verification_status", "limitations", "url"):
            self.assertEqual(saved[key], record[key])
        self.assertEqual(saved["final_url"], "https://example.test/page")
        self.assertEqual(saved["content_url"], "https://example.test/page")

    def test_sections_of_one_page_are_retrieved_once(self) -> None:
        """A fragment never reaches the server.

        Three records cite sections of one NSW Act. Fetching that page three
        times triples the load on a host that already refuses automation.
        """
        skills = self.temporary_skills_directory()
        skill = skills / "example-skill"
        skill.mkdir(parents=True)
        (skill / "sources.json").write_text(
            json.dumps(
                {
                    "skill": "example-skill",
                    "sources": [
                        {"url": "https://example.test/act#sec.11", "checked_at": "2026-09-08"},
                        {"url": "https://example.test/act#sec.32", "checked_at": "2026-09-08"},
                        {"url": "https://example.test/act", "checked_at": "2026-09-08"},
                    ],
                }
            ),
            encoding="utf-8",
        )

        with mock.patch.object(source_refresh, "fetch", return_value=fetched()) as fetch:
            report = source_refresh.refresh(skills=skills, spacing=0)

        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(fetch.call_args.args[0], "https://example.test/act")
        self.assertEqual(len(report.outcomes), 3)

    def test_a_source_reviewed_by_hand_is_not_fetched_and_fails_the_check_once_overdue(self) -> None:
        """AUSTRAC's pages time out this script and change often, so a person reviews them monthly.

        The sweep listed them as unreachable every week and caught nothing; now it names the
        next review date, and an overdue review is a finding.
        """
        skills = self.temporary_skills_directory()
        skill = skills / "example-skill"
        skill.mkdir(parents=True)
        schedule = {"cadence": "monthly", "next_review": "2026-10-26"}
        (skill / "sources.json").write_text(
            json.dumps({"skill": "example-skill", "sources": [
                {"url": "https://example.test/guidance", "checked_at": "2026-09-26",
                 "manual_review": schedule},
            ]}),
            encoding="utf-8",
        )
        with mock.patch.object(source_refresh, "fetch", side_effect=AssertionError("fetched")):
            on_time = source_refresh.refresh(skills=skills, spacing=0, today="2026-10-26", write=True)
            overdue = source_refresh.refresh(skills=skills, spacing=0, today="2026-10-27")

        self.assertEqual([o.outcome for o in on_time.outcomes], [source_refresh.SCHEDULED])
        self.assertEqual(on_time.actionable, [])
        self.assertIn("Reviewed by hand monthly, next review 2026-10-26.", on_time.outcomes[0].detail)
        self.assertIn("- scheduled (reviewed by hand, next review 2026-10-26): 1",
                      source_refresh.render(on_time, write=False))
        self.assertNotIn("Nothing changed", source_refresh.render(on_time, write=False))
        self.assertEqual([o.outcome for o in overdue.outcomes], [source_refresh.REVIEW_DUE])
        self.assertEqual(len(overdue.actionable), 1)
        self.assertIn("- review-due (scheduled manual review overdue): 1",
                      source_refresh.render(overdue, write=False))
        # Not fetched, so the machine fields are never written for it.
        record = json.loads((skill / "sources.json").read_text(encoding="utf-8"))["sources"][0]
        self.assertNotIn(source_refresh.FETCHED_FIELD, record)

    def test_a_mistyped_review_date_counts_as_due(self) -> None:
        """2026-99-99 sorts after any real date and would keep the source unreviewed for ever."""
        for value in ("2026-99-99", "26 October 2026", "", "2026-10-26T00:00"):
            with self.subTest(value=value):
                self.assertEqual(source_refresh.review_date({"next_review": value}), "")
        self.assertEqual(source_refresh.review_date({"next_review": "2026-10-26"}), "2026-10-26")

    def test_every_manual_review_in_the_index_names_a_cadence_and_a_real_date(self) -> None:
        for path in source_refresh.index_files():
            for record in json.loads(path.read_text(encoding="utf-8")).get("sources", []):
                schedule = record.get(source_refresh.SCHEDULE_FIELD)
                if schedule is None:
                    continue
                with self.subTest(skill=path.parent.name, url=record.get("url")):
                    self.assertIsInstance(schedule, dict)
                    self.assertTrue(schedule.get("cadence"))
                    self.assertTrue(source_refresh.review_date(schedule))


if __name__ == "__main__":
    unittest.main()
