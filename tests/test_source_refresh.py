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
from datetime import date
from email.message import Message
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
                self.assertEqual(source_refresh.classify(record, fetched())[0], source_refresh.BASELINE_REQUIRED)
                record[source_refresh.CONTENT_URL_FIELD] = "https://example.test/page"
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
        destination = "https://www.ato.gov.au/redirected"
        error = urllib.error.HTTPError(destination, 404, "Not Found", Message(), None)
        with mock.patch.object(source_refresh.urllib.request, "build_opener") as build, \
                mock.patch.object(source_refresh, "check_public_resolution"):
            build.return_value.open.side_effect = error
            result = source_refresh.fetch("https://www.ato.gov.au/page", tries=1, delay=0)
        self.assertEqual(result.status, 404)
        self.assertEqual(result.final_url, destination)
        record: dict[str, object] = {"url": "https://example.test/page",
                                     source_refresh.CONTENT_URL_FIELD: "https://example.test/old"}
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
                    record: dict[str, object] = {"url": "https://example.test/page",
                                                 source_refresh.CONTENT_URL_FIELD: "https://example.test/old",
                                                 source_refresh.DIGEST_FIELD: UNCHANGED_DIGEST,
                                                 source_refresh.DIGEST_KIND_FIELD: source_refresh.HTML_KIND}
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
            set(record) - {"url", "checked_at"},
            set(source_refresh.MACHINE_FIELDS) | {source_refresh.PENDING_FIELD, source_refresh.REVIEW_REQUIRED_FIELD}
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
        self.assertEqual(saved["content_url"], "https://example.test/old")
        self.assertEqual(saved["pending_review"]["content_url"], "https://example.test/page")

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
        self.assertIn("- review-due (manual review overdue or reverify_by passed): 1",
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


class ReverifyTests(unittest.TestCase):
    """A recorded fact expires after its `reverify_by` date, whatever the page does."""

    def sweep(self, record: dict[str, object], today: str, **fetch: object):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        skill = Path(directory.name) / "skills" / "example-skill"
        skill.mkdir(parents=True)
        (skill / "sources.json").write_text(
            json.dumps({"skill": "example-skill", "sources": [record]}), encoding="utf-8"
        )
        with mock.patch.object(source_refresh, "fetch", return_value=fetched(**fetch)):
            report = source_refresh.refresh(skills=skill.parent, spacing=0, today=today)
        [outcome] = report.outcomes
        return outcome

    def record(self, **overrides: object) -> dict[str, object]:
        base = ClassifyTests().record(reverify_by="2027-06-30")
        base.update(overrides)
        return base

    def test_the_date_itself_is_the_last_usable_day(self) -> None:
        self.assertEqual(self.sweep(self.record(), "2027-06-30").outcome, source_refresh.UNCHANGED)
        late = self.sweep(self.record(), "2027-07-01")
        self.assertEqual(late.outcome, source_refresh.REVIEW_DUE)
        self.assertIn("passed its reverify_by date (2027-06-30)", late.detail)

    def test_a_mistyped_date_counts_as_passed(self) -> None:
        outcome = self.sweep(self.record(reverify_by="30 June 2027"), "2026-10-01")
        self.assertEqual(outcome.outcome, source_refresh.REVIEW_DUE)
        self.assertIn("not a real date", outcome.detail)

    def test_a_record_without_the_field_never_expires(self) -> None:
        record = self.record()
        del record["reverify_by"]
        self.assertEqual(self.sweep(record, "2099-01-01").outcome, source_refresh.UNCHANGED)

    def test_a_fetch_finding_that_asks_for_an_edit_keeps_its_name(self) -> None:
        changed = self.sweep(self.record(), "2027-07-01", digest="b" * 64)
        self.assertEqual(changed.outcome, source_refresh.CHANGED)
        self.assertIn("reverify_by", changed.detail)
        missing = self.sweep(self.record(), "2027-07-01", status=404, digest="", kind="", error="HTTP 404")
        self.assertEqual(missing.outcome, source_refresh.MISSING)

    def test_an_unreachable_page_is_still_a_review_due_once_the_fact_expires(self) -> None:
        blocked = self.sweep(self.record(), "2027-07-01", status=403, digest="", kind="", error="HTTP 403")
        self.assertEqual(blocked.outcome, source_refresh.REVIEW_DUE)
        self.assertIn("Retrieval: HTTP 403", blocked.detail)
        self.assertTrue(blocked.actionable)

    def test_an_expired_fact_on_a_hand_reviewed_source_is_due_before_its_schedule(self) -> None:
        record = self.record(manual_review={"cadence": "monthly", "next_review": "2027-07-26"})
        outcome = self.sweep(record, "2027-07-01")
        self.assertEqual(outcome.outcome, source_refresh.REVIEW_DUE)
        self.assertIn("passed its reverify_by date", outcome.detail)

    def test_a_write_never_touches_the_reverify_date(self) -> None:
        record: dict[str, object] = {"url": "https://example.test/page", "checked_at": "2026-09-08",
                                     "reverify_by": "2027-06-30"}
        source_refresh.apply_fetch(record, fetched(), "2026-09-16")
        self.assertEqual(record["reverify_by"], "2027-06-30")

    def test_every_volatile_record_carries_a_reverify_date_within_400_days(self) -> None:
        """Extending the date past 400 days needs a fresh human `checked_at` as well."""
        for path in source_refresh.index_files():
            for record in json.loads(path.read_text(encoding="utf-8")).get("sources", []):
                if not record.get("volatile") and source_refresh.REVERIFY_FIELD not in record:
                    continue
                with self.subTest(skill=path.parent.name, url=record.get("url")):
                    due = source_refresh.review_date({"next_review": record.get("reverify_by", "")})
                    self.assertTrue(due, "reverify_by must be a real YYYY-MM-DD date")
                    checked = date.fromisoformat(str(record["checked_at"]))
                    self.assertLessEqual(checked, date.fromisoformat(due))
                    self.assertLessEqual((date.fromisoformat(due) - checked).days, 400)


class PreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.skills = Path(temporary.name)
        directory = self.skills / "example-skill"
        directory.mkdir()
        (directory / "SKILL.md").write_text("# Example", encoding="utf-8")
        self.path = directory / "sources.json"
        self.record: dict[str, object] = {
            "url": "https://example.test/page", "checked_at": "2026-09-26",
            "fact": "A reviewed synthetic source fact.", "content_url": "https://example.test/page",
            "content_hash": UNCHANGED_DIGEST, "content_hash_covers": source_refresh.HTML_KIND,
            "volatile": True, "reverify_by": "2026-10-03",
            "source_last_modified": "",
        }

    def run_preflight(self, *records: dict[str, object], response: source_refresh.Fetched | None = None) -> tuple[str, int]:
        self.path.write_text(json.dumps({"skill": "example-skill", "sources": list(records)}), encoding="utf-8")
        original = self.path.read_bytes()
        with mock.patch.object(source_refresh, "fetch", return_value=response or fetched()):
            result = source_refresh.preflight("example-skill", skills=self.skills, today="2026-10-03", spacing=0)
        self.assertEqual(self.path.read_bytes(), original)
        return result

    def test_current_record_and_inclusive_expiry_are_ready_without_writes(self) -> None:
        text, exit_code = self.run_preflight(self.record)
        self.assertEqual(exit_code, 0)
        self.assertIn("READY:", text)
        self.assertIn("effective period at use time", text)

    def test_written_changes_remain_pending_until_explicit_human_acceptance(self) -> None:
        for response in (fetched(digest="b" * 64),
                         fetched(final_url="https://example.test/new"),
                         fetched(kind=source_refresh.BYTES_KIND)):
            with self.subTest(response=response):
                self.run_preflight(self.record)
                with mock.patch.object(source_refresh, "fetch", return_value=response):
                    source_refresh.refresh(skills=self.skills, today="2026-10-03", spacing=0, write=True)
                    text, code = source_refresh.preflight("example-skill", skills=self.skills,
                                                         today="2026-10-03", spacing=0)
                self.assertEqual(code, 2)
                self.assertIn("Pending human review", text)
                saved = json.loads(self.path.read_text(encoding="utf-8"))["sources"][0]
                for key in ("content_hash", "content_hash_covers", "content_url", "checked_at", "fact"):
                    self.assertEqual(saved[key], self.record[key])
                candidate = saved["pending_review"]
                # Merely removing the pending marker and advancing the machine baseline is insufficient.
                for key in ("content_hash", "content_hash_covers", "content_url", "source_last_modified"):
                    saved[key] = candidate[key]
                del saved["pending_review"]
                self.assertEqual(self.run_preflight(saved, response=response)[1], 2)
                saved["checked_at"] = "2026-10-03"
                saved["fact"] = "A person reviewed this synthetic revision."
                saved["reviewed_content"] = {
                    key: saved[key] for key in ("content_hash", "content_hash_covers", "content_url", "source_last_modified", "checked_at")
                }
                text, code = self.run_preflight(saved, response=response)
                self.assertEqual(code, 0)
                self.assertIn("READY:", text)

    def test_pending_review_survives_a_return_to_the_old_baseline_and_manual_schedule(self) -> None:
        self.run_preflight(self.record)
        with mock.patch.object(source_refresh, "fetch", return_value=fetched(digest="b" * 64)):
            source_refresh.refresh(skills=self.skills, today="2026-10-03", spacing=0, write=True)
        with mock.patch.object(source_refresh, "fetch", return_value=fetched()):
            source_refresh.refresh(skills=self.skills, today="2026-10-03", spacing=0, write=True)
        saved = json.loads(self.path.read_text(encoding="utf-8"))["sources"][0]
        for manual in (False, True):
            record = dict(saved)
            if manual:
                record["manual_review"] = {"cadence": "monthly", "next_review": "2026-10-03"}
            text, code = self.run_preflight(record)
            self.assertEqual(code, 2)
            self.assertIn("Pending human review", text)

    def test_human_binding_must_match_the_reading_destination_and_current_review_date(self) -> None:
        record = {**self.record, "review_required_since": "2026-10-03", "checked_at": "2026-10-03"}
        binding = {key: record[key] for key in ("content_hash", "content_hash_covers", "content_url", "source_last_modified", "checked_at")}
        for key in binding:
            with self.subTest(key=key):
                self.assertEqual(self.run_preflight({**record, "reviewed_content": {**binding, key: "wrong"}})[1], 2)
        self.assertEqual(self.run_preflight({**record, "reviewed_content": binding})[1], 0)

    def test_post_review_upstream_dates_remain_actionable_through_missing_or_older_writes(self) -> None:
        for later in (fetched(), fetched(last_modified="2026-09-20")):
            with self.subTest(later=later):
                self.run_preflight(self.record)
                with mock.patch.object(source_refresh, "fetch", return_value=fetched(last_modified="2026-10-01")):
                    report = source_refresh.refresh(skills=self.skills, today="2026-10-03", spacing=0, write=True)
                with mock.patch.object(source_refresh, "refresh", return_value=report), mock.patch("sys.stdout"):
                    self.assertEqual(source_refresh.main(["--write", "--check"]), 2)
                with mock.patch.object(source_refresh, "fetch", return_value=later):
                    source_refresh.refresh(skills=self.skills, today="2026-10-03", spacing=0, write=True)
                saved = json.loads(self.path.read_text(encoding="utf-8"))["sources"][0]
                self.assertEqual(saved["source_last_modified"], "2026-10-01")
                self.assertEqual(saved["pending_review"]["source_last_modified"], "2026-10-01")
                for manual in (False, True):
                    record = dict(saved)
                    if manual:
                        record["manual_review"] = {"cadence": "monthly", "next_review": "2026-10-03"}
                    text, code = self.run_preflight(record, response=later)
                    self.assertEqual(code, 2)
                    self.assertIn("Pending human review", text)
                candidate = saved.pop("pending_review")
                for key in ("content_hash", "content_hash_covers", "content_url", "source_last_modified"):
                    saved[key] = candidate[key]
                saved["checked_at"] = "2026-10-03"
                saved["fact"] = "Human review acknowledges the published update."
                saved["reviewed_content"] = {key: saved[key] for key in
                                            ("content_hash", "content_hash_covers", "content_url", "checked_at")}
                self.assertEqual(self.run_preflight(saved, response=later)[1], 2)
                saved["reviewed_content"]["source_last_modified"] = "2026-10-01"
                self.assertEqual(self.run_preflight(saved, response=later)[1], 0)

    def test_human_dates_status_and_expiry_cannot_be_replaced_by_unchanged_hashes(self) -> None:
        for changes in ({"checked_at": ""}, {"checked_at": "2026-99-99"}, {"checked_at": "2026-10-04"},
                        {"reverify_by": "2026-10-02"}, {"reverify_by": "unknown"}, {"fact": ""},
                        {"verification_status": "indexed-source-discovery-only"},
                        {"checked_at": "2024-10-03"},
                        {"verification_status": "indexed-source-discovery-only",
                         "manual_review": {"cadence": "monthly", "next_review": "2026-10-03"}},
                        {"verification_status": "unavailable-http-403"}):
            with self.subTest(changes=changes):
                self.assertEqual(self.run_preflight({**self.record, **changes})[1], 2)
        record = dict(self.record)
        del record["reverify_by"]
        self.assertEqual(self.run_preflight(record)[1], 2)
        record["volatile"] = False
        self.assertEqual(self.run_preflight(record)[1], 0)

    def test_retrieval_failures_and_changed_reading_are_unavailable(self) -> None:
        for response in (fetched(status=404, error="missing"), fetched(status=403, error="blocked"),
                         fetched(status=None, error="offline"), fetched(digest="b" * 64),
                         fetched(digest="", error="empty"), fetched(kind=source_refresh.BYTES_KIND),
                         fetched(last_modified="2026-10-01")):
            with self.subTest(response=response):
                self.assertEqual(self.run_preflight(self.record, response=response)[1], 2)
        record = dict(self.record)
        del record["content_hash"]
        self.assertEqual(self.run_preflight(record)[1], 2)

    def test_manual_review_is_not_fetched_and_remains_subject_to_dates(self) -> None:
        record = {**self.record, "manual_review": {"cadence": "monthly", "next_review": "2026-10-03"}}
        self.path.write_text(json.dumps({"skill": "example-skill", "sources": [record]}), encoding="utf-8")
        with mock.patch.object(source_refresh, "fetch", side_effect=AssertionError("manual source fetched")):
            text, exit_code = source_refresh.preflight("example-skill", skills=self.skills, today="2026-10-03")
        self.assertEqual(exit_code, 0)
        self.assertIn("READY_MANUAL", text)
        for schedule in ({"cadence": "monthly", "next_review": "2026-10-02"},
                         {"cadence": "monthly", "next_review": "2026-99-99"}):
            self.assertEqual(self.run_preflight({**record, "manual_review": schedule})[1], 2)

    def test_manual_review_and_retrieval_warning_have_independent_meanings(self) -> None:
        record = {**self.record, "manual_review": {"cadence": "monthly", "next_review": "2026-10-03"}}
        for name in (source_refresh.BLOCKED, source_refresh.UNREACHABLE):
            outcome = source_refresh.Outcome("example-skill", "Example", str(record["url"]), name,
                                             "not fetched", "2026-09-26", fetched(status=403))
            ready, detail = source_refresh.source_readiness(record, outcome, "2026-10-03")
            self.assertTrue(ready)
            self.assertIn("Retrieval remains unavailable", detail)
            self.assertFalse(source_refresh.source_readiness(self.record, outcome, "2026-10-03")[0])

    def test_integrated_manual_review_reports_retrieval_not_attempted_and_recorded_failure(self) -> None:
        record = {**self.record, "verification_status": "unavailable-http-403",
                  "manual_review": {"cadence": "monthly", "next_review": "2026-10-03"}}
        self.path.write_text(json.dumps({"skill": "example-skill", "sources": [record]}), encoding="utf-8")
        original = self.path.read_bytes()
        with mock.patch.object(source_refresh, "fetch", side_effect=AssertionError("manual source fetched")):
            text, exit_code = source_refresh.preflight("example-skill", skills=self.skills, today="2026-10-03")
        self.assertEqual(exit_code, 0)
        self.assertIn("READY_MANUAL", text)
        self.assertIn("retrieval: not attempted: explicit manual review", text)
        self.assertIn("Recorded automatic retrieval remains unavailable", text)
        self.assertNotIn("retrieval: scheduled", text)
        self.assertEqual(self.path.read_bytes(), original)
        malformed = {**self.record, "manual_review": "monthly"}
        self.path.write_text(json.dumps({"skill": "example-skill", "sources": [malformed]}), encoding="utf-8")
        with mock.patch.object(source_refresh, "fetch", return_value=fetched()) as fetch:
            text, exit_code = source_refresh.preflight("example-skill", skills=self.skills, today="2026-10-03", spacing=0)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(exit_code, 2)
        self.assertIn("retrieval: unchanged", text)
        self.assertNotIn("retrieval: not attempted", text)

    def test_shared_url_does_not_share_human_review(self) -> None:
        records = [self.record, {**self.record, "verification_status": "indexed-source-discovery-only"}]
        self.path.write_text(json.dumps({"skill": "example-skill", "sources": records}), encoding="utf-8")
        with mock.patch.object(source_refresh, "fetch", return_value=fetched()) as fetch:
            text, exit_code = source_refresh.preflight("example-skill", skills=self.skills, today="2026-10-03", spacing=0)
        self.assertEqual(fetch.call_count, 1)
        self.assertEqual(exit_code, 2)
        self.assertIn("READY:", text)
        self.assertIn("discovery-only", text)

    def test_overdue_invalid_or_incomplete_manual_schedule_is_a_human_review_finding(self) -> None:
        for schedule, weekly in (({"cadence": "monthly", "next_review": "2026-10-02"}, source_refresh.REVIEW_DUE),
                                 ({"cadence": "monthly", "next_review": "2026-99-99"}, source_refresh.REVIEW_DUE),
                                 ({"cadence": "", "next_review": "2026-10-03"}, source_refresh.SCHEDULED)):
            with self.subTest(schedule=schedule):
                record = {**self.record, "manual_review": schedule}
                self.path.write_text(json.dumps({"skill": "example-skill", "sources": [record]}), encoding="utf-8")
                original = self.path.read_bytes()
                with mock.patch.object(source_refresh, "fetch", side_effect=AssertionError("manual source fetched")):
                    text, exit_code = source_refresh.preflight("example-skill", skills=self.skills, today="2026-10-03")
                    report = source_refresh.refresh(skills=self.skills, only_skill="example-skill", today="2026-10-03")
                self.assertEqual(report.outcomes[0].outcome, weekly)
                self.assertEqual(exit_code, 2)
                self.assertIn("retrieval: not attempted: explicit manual review", text)
                self.assertIn("Manual review", text)
                self.assertNotIn("Retrieval requires review", text)
                self.assertEqual(self.path.read_bytes(), original)

    def test_unknown_empty_exempt_and_partial_modes_fail_explicitly(self) -> None:
        self.assertEqual(source_refresh.preflight("missing-skill", skills=self.skills)[1], 1)
        self.assertEqual(source_refresh.preflight("../example-skill", skills=self.skills)[1], 1)
        self.path.write_text('{"skill":"example-skill","sources":[]}', encoding="utf-8")
        self.assertEqual(source_refresh.preflight("example-skill", skills=self.skills)[1], 1)
        self.path.unlink()
        (self.path.parent / "sources.exempt.json").write_text('{"exempt":true}', encoding="utf-8")
        self.assertEqual(source_refresh.preflight("example-skill", skills=self.skills)[1], 2)
        for extra in (["--write"], ["--check"], ["--url", "https://example.test/page"]):
            with self.subTest(extra=extra), mock.patch("sys.stderr"), self.assertRaises(SystemExit) as error:
                source_refresh.main(["--preflight", "--skill", "example-skill", *extra])
            self.assertEqual(error.exception.code, 2)


class LinkedIndexTests(unittest.TestCase):
    def test_linked_files_and_skill_directories_are_rejected_without_reading_or_writing(self) -> None:
        for directory_link in (False, True):
            with self.subTest(directory_link=directory_link), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                skills = root / "skills"
                external = root / "external"
                skills.mkdir()
                external.mkdir()
                sentinel = external / "sources.json"
                original = b'{"skill":"example-skill","sources":[{"url":"https://example.test/page"}]}\n'
                sentinel.write_bytes(original)
                directory = skills / "example-skill"
                try:
                    if directory_link:
                        directory.symlink_to(external, target_is_directory=True)
                    else:
                        directory.mkdir()
                        (directory / "sources.json").symlink_to(sentinel)
                except OSError as exc:
                    self.skipTest(f"Operating system refused test symlink: {exc}")
                with mock.patch.object(source_refresh, "fetch", side_effect=AssertionError("must not fetch")), \
                        mock.patch.object(source_refresh, "load_index", side_effect=AssertionError("must not read")):
                    with self.assertRaisesRegex(ValueError, "Linked|outside"):
                        source_refresh.refresh(skills=skills, write=True, spacing=0)
                    with mock.patch.object(source_refresh, "refresh", side_effect=ValueError("Linked source index")), \
                            mock.patch("sys.stderr"):
                        self.assertEqual(source_refresh.main(["--write"]), 1)
                self.assertEqual(sentinel.read_bytes(), original)

    def test_write_rechecks_a_path_replaced_with_a_link_after_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            skills = root / "skills"
            directory = skills / "example-skill"
            directory.mkdir(parents=True)
            path = directory / "sources.json"
            original = b'{"skill":"example-skill","sources":[{"url":"https://example.test/page"}]}\n'
            path.write_bytes(original)
            sentinel = root / "external.json"
            sentinel.write_bytes(original)
            probe = root / "link-probe"
            try:
                probe.symlink_to(sentinel)
            except OSError as exc:
                self.skipTest(f"Operating system refused test symlink: {exc}")
            probe.unlink()

            def replace_then_fetch(_url: str) -> source_refresh.Fetched:
                path.unlink()
                path.symlink_to(sentinel)
                return fetched()

            with mock.patch.object(source_refresh, "fetch", side_effect=replace_then_fetch):
                with self.assertRaisesRegex(ValueError, "Linked|outside"):
                    source_refresh.refresh(skills=skills, write=True, spacing=0)
            self.assertEqual(sentinel.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
