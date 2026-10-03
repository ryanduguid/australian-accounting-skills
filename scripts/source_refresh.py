"""Re-fetch every indexed primary source and report which ones moved.

The sources index records where a workflow's primary-source material lives. It
adopts no rate, threshold, deadline or eligibility conclusion, so the index
cannot go wrong in the way a cached figure can. It can still go stale: a page
is rewritten, retitled, redirected or withdrawn, and nothing in the repository
notices until someone re-reads the indexed URLs by hand.

This records a content digest per source so the next run can answer "which of
these moved" in one pass. Two dates are kept apart on purpose:

* ``checked_at`` is the date a person reviewed the source. Only a person
  changes it, because only a person can judge whether the material still
  supports the workflow.
* ``fetched_at`` is the date this script last attempted retrieval. A machine
  writes it, and it never stands in for a review.

``final_url`` records the response URL when available, otherwise the requested
URL. ``content_url`` accompanies the reviewed digest and survives failed
attempts. Changed or missing baselines are stored as ``pending_review``;
human acceptance binds the candidate to ``reviewed_content`` before readiness
can resume. See docs/source-preflight.md for the manual acceptance procedure.

For an HTML page the digest covers the readable text, with scripts, styles
and markup removed, and prefers the ``<main>`` region when the page has one.
Without that region, changes to page navigation can also change the digest.

PDFs are hashed as raw bytes. A change to their metadata can change the digest
even when the visible text is unchanged.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable, Iterator, Sequence
from urllib.parse import urldefrag, urljoin, urlsplit

from source_fetch_policy import (
    APPROVED_REDIRECT_EDGES,
    MAX_REDIRECTS,
    NoRedirect,
    SourcePolicyError,
    bounded_body,
    check_public_resolution,
    checked_url,
)

REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS_DIRECTORY = REPOSITORY / ".claude" / "skills"

TIMEOUT = 30
TRIES = 3
RETRY_DELAY = 6.0
# Spacing between requests to the same run. These are public sector sites
# serving the source sweep. A courteous pace avoids a burst of requests.
REQUEST_SPACING = 1.0
USER_AGENT = (
    "australian-accounting-skills source-refresh "
    "(+https://github.com/ryanduguid/australian-accounting-skills)"
)

# A write supplies every machine field. Older records may lack `content_url`.
# `checked_at` and `fact` are never touched here.
DIGEST_FIELD = "content_hash"
CONTENT_URL_FIELD = "content_url"
FETCHED_FIELD = "fetched_at"
FINAL_URL_FIELD = "final_url"
STATUS_FIELD = "http_status"
# A person-written schedule, {"cadence": "monthly", "next_review": "YYYY-MM-DD"}, for a source
# reviewed by hand instead of fetched. AUSTRAC's guidance changes often and its host times out
# this script, so the sweep listed those pages as unreachable every week and caught nothing.
SCHEDULE_FIELD = "manual_review"
# A person-written date, YYYY-MM-DD, on every volatile record: the last day its
# recorded fact may serve as a cross-check without a fresh reading of the
# source. Like `checked_at`, only a person changes it; a later date is a review.
REVERIFY_FIELD = "reverify_by"
UPSTREAM_FIELD = "source_last_modified"
DIGEST_KIND_FIELD = "content_hash_covers"
PENDING_FIELD = "pending_review"
REVIEW_REQUIRED_FIELD = "review_required_since"
REVIEWED_FIELD = "reviewed_content"  # Human-owned binding; never written by a sweep.
MACHINE_FIELDS = (
    DIGEST_FIELD,
    DIGEST_KIND_FIELD,
    CONTENT_URL_FIELD,
    FETCHED_FIELD,
    FINAL_URL_FIELD,
    STATUS_FIELD,
    UPSTREAM_FIELD,
)

# An unchanged result needs persisted content and destination baselines.
# Missing baselines require review and an explicit write.
#
# The three failure outcomes are kept apart because they ask for three
# different things. `missing` is a defect in this repository: the indexed URL
# no longer resolves and the record has to be repointed. `blocked` is the
# host's policy and will not change on a retry, so those sources can only ever
# be reviewed by hand. `unreachable` is everything else and may well succeed on
# the next sweep.
UNCHANGED = "unchanged"
CHANGED = "changed"
RECORDED = "recorded"
BASELINE_REQUIRED = "baseline-required"
MISSING = "missing"
BLOCKED = "blocked"
UNREACHABLE = "unreachable"
# The source answered but this script could not read it. That is a defect
# here, not a finding about the source, and it must never be stored as a
# digest: an empty digest compares equal on every later sweep.
UNREADABLE = "unreadable"
# A source on a manual-review schedule is not fetched. `scheduled` counts those not yet due;
# `review-due` is one whose next review date has passed, or any record whose `reverify_by`
# date has passed, which asks a person for a review.
SCHEDULED = "scheduled"
REVIEW_DUE = "review-due"
NEEDS_ATTENTION = (CHANGED, MISSING, BLOCKED, UNREACHABLE, UNREADABLE, REVIEW_DUE, BASELINE_REQUIRED)
# What `--check` fails on, which is narrower than what it reports.
#
# A changed, missing or unreadable source means something here is wrong and
# a person can put it right. Blocked and unreachable are facts about the
# network: legislation.nsw.gov.au refuses automated retrieval to every user
# agent, and no edit in this repository will change that. Failing on them
# would leave the scheduled issue permanently open, and an alert that can
# never be cleared is one nobody reads. They stay in every report instead,
# and coverage.json counts them per skill.
ACTIONABLE = (CHANGED, MISSING, UNREADABLE, REVIEW_DUE, BASELINE_REQUIRED)
REPORTED_OUTCOMES = (
    CHANGED, MISSING, BLOCKED, UNREACHABLE, UNREADABLE, REVIEW_DUE, BASELINE_REQUIRED,
    SCHEDULED, RECORDED, UNCHANGED,
)

# Status codes that settle the question rather than inviting a retry.
GONE_STATUSES = frozenset({404, 410})
REFUSED_STATUSES = frozenset({401, 403, 429, 451})

# Elements whose text is markup plumbing rather than page content.
#
# `head` is deliberately absent. Its closing tag is optional in HTML5, and
# HTMLParser does not synthesise one, so skipping it meant that on a page which
# omits `</head>` the skip stayed open for the whole document and the digest
# covered an empty string. Every sweep would then have reported that page
# unchanged no matter what it said. The only text `head` yields is the title,
# because script and style are skipped on their own account, and a retitled
# page is worth seeing anyway.
SKIPPED_ELEMENTS = frozenset({"script", "style", "noscript", "template", "svg"})

# Content types whose readable text is worth extracting. Anything else is
# hashed whole.
MARKUP_TYPES = frozenset({"text/html", "application/xhtml+xml"})
HTML_KIND = "html"
BYTES_KIND = "bytes"

# Three upstream modification signals, each observed on a host in this index on
# 16 September 2026: ato.gov.au publishes JSON-LD `dateModified`,
# revenue.nsw.gov.au publishes a DCTERMS.modified meta tag, and
# standards.aasb.gov.au sets the HTTP Last-Modified header. legislation.gov.au
# publishes none of them, so its records carry no upstream date and rely on the
# digest alone.
JSONLD_MODIFIED = re.compile(rb'"dateModified"\s*:\s*"([^"]{4,40})"', re.IGNORECASE)
META_MODIFIED = re.compile(
    rb"""<meta[^>]*?(?:name|property)\s*=\s*["']"""
    rb"""(?:DCTERMS\.modified|article:modified_time|og:updated_time)["']"""
    rb"""[^>]*?content\s*=\s*["']([^"']{4,40})["']""",
    re.IGNORECASE,
)
META_MODIFIED_REVERSED = re.compile(
    rb"""<meta[^>]*?content\s*=\s*["']([^"']{4,40})["'][^>]*?(?:name|property)\s*=\s*["']"""
    rb"""(?:DCTERMS\.modified|article:modified_time|og:updated_time)["']""",
    re.IGNORECASE,
)


class _ReadableText(HTMLParser):
    """Collect a page's readable text, preferring its ``<main>`` region.

    Hashing a whole page makes a footer or navigation edit look like a rule
    change on every source that shares the template. When a page marks its
    content region with ``<main>``, that region is the honest subject of the
    digest; ato.gov.au marks none, so its pages are hashed whole.

    Only the element counts, not a ``role="main"`` attribute on some other
    tag. No page in the index does that, and honouring it would mean opening
    the region on a ``<div>`` and never closing it, which silently swallows
    the rest of the document including the footer the region was meant to
    exclude.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._whole: list[str] = []
        self._main: list[str] = []
        self._skip_depth = 0
        self._main_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs  # the element name is the only marker this reads
        if tag in SKIPPED_ELEMENTS:
            self._skip_depth += 1
        elif tag == "main":
            self._main_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in SKIPPED_ELEMENTS:
            self._skip_depth = max(0, self._skip_depth - 1)
        elif tag == "main":
            self._main_depth = max(0, self._main_depth - 1)

    def handle_data(self, data: str) -> None:
        if self._skip_depth:
            return
        self._whole.append(data)
        if self._main_depth:
            self._main.append(data)

    def text(self) -> str:
        chosen = self._main or self._whole
        # NFC first: the same character can arrive composed or decomposed from
        # one request to the next, and two spellings must not read as a change.
        collapsed = " ".join("".join(chosen).split())
        return unicodedata.normalize("NFC", collapsed)


def readable_text(body: bytes, charset: str | None) -> str:
    """Decode and reduce a response body to the text a digest should cover."""
    markup = body.decode(charset or "utf-8", errors="replace")
    parser = _ReadableText()
    parser.feed(markup)
    parser.close()
    return parser.text()


def content_digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def iso_day(value: str) -> str:
    """Reduce a published date to YYYY-MM-DD, or return an empty string.

    The three signals arrive in three shapes: an ISO instant from ATO's
    JSON-LD, a bare date from a DCTERMS meta tag, and an HTTP-date from a
    Last-Modified header. A single day-precision spelling is what makes the
    field sortable and directly comparable with `checked_at`.
    """
    text = value.strip()
    if not text:
        return ""
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass
    try:
        return parsedate_to_datetime(text).date().isoformat()
    except (TypeError, ValueError):
        return ""


def upstream_last_modified(
    body: bytes, last_modified_header: str | None, response_date: str | None = None
) -> str:
    """Return the page's own modification date, or an empty string.

    A published date in the markup is the page's own claim about its content.
    A Last-Modified header is only that when the resource is static: these
    hosts render most pages per request, so the header then repeats the time
    of the request and would report a content change on every sweep. It is
    accepted only when it predates the response by at least a day.
    """
    for pattern in (JSONLD_MODIFIED, META_MODIFIED, META_MODIFIED_REVERSED):
        match = pattern.search(body)
        if match:
            published = iso_day(match.group(1).decode("utf-8", "replace"))
            if published:
                return published
    header = iso_day(last_modified_header or "")
    served = iso_day(response_date or "")
    if header and (not served or header < served):
        return header
    return ""


def body_digest(body: bytes, content_type: str, charset: str | None) -> tuple[str, str]:
    """Digest a response, and say which reading produced it.

    Markup is reduced to readable text first, because the surrounding page
    furniture changes on every request. A PDF, a JSON document or a plain-text
    file has no such furniture, so it is hashed as served.
    """
    if content_type in MARKUP_TYPES:
        text = readable_text(body, charset)
        if not text:
            return "", HTML_KIND
        return content_digest(text), HTML_KIND
    if not body:
        return "", BYTES_KIND
    return hashlib.sha256(body).hexdigest(), BYTES_KIND


@dataclass
class Fetched:
    """One retrieval attempt, successful or not."""

    status: int
    final_url: str
    digest: str
    kind: str
    content_type: str
    last_modified: str
    error: str
    text: str = ""
    text_truncated: bool = False

    @property
    def reachable(self) -> bool:
        return self.status == 200 and not self.error

    @property
    def readable(self) -> bool:
        return self.reachable and bool(self.digest)


def _open_checked_response(opener, url: str):
    """Validate every redirect before opening it; the caller owns the final response."""
    target = checked_url(url)
    seen = {target}
    for hop in range(MAX_REDIRECTS + 1):
        check_public_resolution(target)
        request = urllib.request.Request(target, headers={
            "User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*",
            "Accept-Encoding": "identity",
        })
        try:
            response = opener.open(request, timeout=TIMEOUT)
            return response, target
        except urllib.error.HTTPError as redirect:
            if redirect.code not in {301, 302, 303, 307, 308}:
                raise
            with redirect:
                location = redirect.headers.get("Location")
                if not location or hop == MAX_REDIRECTS:
                    raise SourcePolicyError("Missing redirect location or redirect ceiling exceeded.")
                following = checked_url(urljoin(target, location))
                hosts = (urlsplit(target).hostname, urlsplit(following).hostname)
                if hosts[0] != hosts[1] and hosts not in APPROVED_REDIRECT_EDGES:
                    raise SourcePolicyError("Cross-host redirect has not been reviewed.")
                if following in seen:
                    raise SourcePolicyError("Redirect loop.")
                seen.add(following)
                target = following


def _interpret_response(response, target: str, include_text: bool) -> Fetched:
    """Close the response after destination validation and bounded interpretation."""
    with response:
        final_url = checked_url(response.geturl())
        if final_url != target:
            raise SourcePolicyError("Unexpected response destination.")
        body = bounded_body(response)
        content_type = (response.headers.get_content_type() or "").lower()
        digest, kind = body_digest(
            body, content_type, response.headers.get_content_charset()
        )
        text = (readable_text(body, response.headers.get_content_charset())
                if include_text and content_type in MARKUP_TYPES else
                body.decode(response.headers.get_content_charset() or "utf-8", errors="replace")
                if include_text and content_type == "text/plain" else "")
        return Fetched(
            status=response.status,
            final_url=final_url,
            digest=digest,
            kind=kind,
            content_type=content_type,
            last_modified=upstream_last_modified(
                body,
                response.headers.get("Last-Modified"),
                response.headers.get("Date"),
            ),
            error="",
            text=text[:32768],
            text_truncated=len(text) > 32768,
        )


def fetch(url: str, *, tries: int = TRIES, delay: float = RETRY_DELAY,
          include_text: bool = False) -> Fetched:
    """Retrieve one source. A blocked or missing page is data, not a failure.

    Several of these hosts refuse automated retrieval outright, so an
    unreachable source has to be recorded and reported rather than raised. The
    sweep's job is to tell a reviewer what to look at, and "this one can no
    longer be checked from CI" is exactly that kind of finding.
    """
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    last_error = ""
    for attempt in range(1, tries + 1):
        try:
            response, target = _open_checked_response(opener, url)
            return _interpret_response(response, target, include_text)
        except SourcePolicyError as error:
            return Fetched(0, url, "", "", "", "", f"Source policy: {error}")
        except urllib.error.HTTPError as error:
            # A refusal is settled; only a transport fault is worth retrying.
            # The error holds the response open until closed; left to the
            # garbage collector it closes late, with a ResourceWarning.
            with error:
                return Fetched(
                    status=error.code,
                    final_url=error.geturl() or url,
                    digest="",
                    kind="",
                    content_type="",
                    last_modified="",
                    error=f"HTTP {error.code} {error.reason}",
                )
        except Exception as error:  # noqa: BLE001 - every transport fault is reportable
            last_error = f"{type(error).__name__}: {error}"
            if attempt < tries:
                time.sleep(delay)
    return Fetched(
        status=0, final_url=url, digest="", kind="", content_type="", last_modified="",
        error=last_error,
    )


@dataclass
class Outcome:
    """What the sweep found for one source record."""

    skill: str
    title: str
    url: str
    outcome: str
    detail: str
    checked_at: str
    fetched: Fetched
    next_review: str = ""

    @property
    def needs_attention(self) -> bool:
        return self.outcome in NEEDS_ATTENTION

    @property
    def actionable(self) -> bool:
        return self.outcome in ACTIONABLE


@dataclass
class Report:
    outcomes: list[Outcome] = field(default_factory=list)
    written: list[Path] = field(default_factory=list)

    def by_outcome(self, name: str) -> list[Outcome]:
        return [outcome for outcome in self.outcomes if outcome.outcome == name]

    @property
    def needs_attention(self) -> list[Outcome]:
        return [outcome for outcome in self.outcomes if outcome.needs_attention]

    @property
    def actionable(self) -> list[Outcome]:
        return [outcome for outcome in self.outcomes if outcome.actionable]


def checked_index(path: Path, skills: Path) -> None:
    if path.is_symlink() or path.parent.is_symlink():
        raise ValueError("Linked source index or skill directory is unsupported")
    if not path.resolve().is_relative_to(skills.resolve()):
        raise ValueError("Source index resolves outside the skills tree")


def index_files(skills: Path = SKILLS_DIRECTORY) -> Iterator[Path]:
    for path in sorted(skills.glob("*/sources.json")):
        checked_index(path, skills)
        yield path


def review_date(schedule: dict[str, object]) -> str:
    """The schedule's next review date, or an empty string when it is not a real ISO date.

    A mistyped date such as 2026-99-99 would otherwise sort as a date far ahead and keep the
    source scheduled, unfetched and unreviewed indefinitely, so it counts as due instead.
    """
    due = str(schedule.get("next_review", ""))
    try:
        return due if date.fromisoformat(due).isoformat() == due else ""
    except ValueError:
        return ""


def reverify_passed(record: dict[str, object], today: str) -> str:
    """The record's `reverify_by` date once it has passed, else an empty string.

    The date itself is the last usable day, so a record is due the day after. A
    mistyped date counts as passed, for the reason `review_date` gives.
    """
    if REVERIFY_FIELD not in record:
        return ""
    value = str(record.get(REVERIFY_FIELD, ""))
    usable = review_date({"next_review": value})
    if usable and usable >= today:
        return ""
    return usable or f"{value!r}, not a real date"


def reverify_note(passed: str) -> str:
    return (
        f"The recorded fact passed its reverify_by date ({passed}). Read the source, then "
        "update checked_at, the fact and reverify_by by hand."
    )


def load_index(path: Path, *, skills: Path = SKILLS_DIRECTORY) -> dict[str, object]:
    checked_index(path, skills)
    return json.loads(path.read_text(encoding="utf-8"))


def dump_index(path: Path, payload: dict[str, object], *, skills: Path = SKILLS_DIRECTORY) -> None:
    checked_index(path, skills)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def records(paths: Iterable[Path], *, skills: Path = SKILLS_DIRECTORY
            ) -> Iterator[tuple[Path, dict[str, object], dict[str, object]]]:
    for path in paths:
        payload = load_index(path, skills=skills)
        sources = payload.get("sources")
        if not isinstance(sources, list):
            continue
        for record in sources:
            if isinstance(record, dict):
                yield path, payload, record


def latest_upstream_date(record: dict[str, object], fetched: Fetched) -> str:
    """Latest valid published modification date, including retained evidence."""
    return max(iso_day(fetched.last_modified), iso_day(str(record.get(UPSTREAM_FIELD, ""))))


def classify(record: dict[str, object], fetched: Fetched) -> tuple[str, str]:
    """Name what happened to one record, and say why in one line."""
    if fetched.error.startswith("Source policy:"):
        return UNREADABLE, fetched.error + " Open the source for manual review."
    if fetched.reachable and not fetched.readable:
        return UNREADABLE, (
            f"Retrieved {fetched.content_type or 'the response'} but extracted no content to "
            "digest. This is a fault in scripts/source_refresh.py, not a finding about the "
            "source."
        )
    if not fetched.reachable:
        reason = fetched.error or f"HTTP {fetched.status}"
        if fetched.status in GONE_STATUSES:
            return MISSING, f"{reason}. The indexed URL no longer resolves: repoint the record."
        if fetched.status in REFUSED_STATUSES:
            return BLOCKED, f"{reason}. This host refuses automated retrieval: review by hand."
        return UNREACHABLE, f"{reason}. Open the source by hand before relying on the workflow."
    modified = latest_upstream_date(record, fetched)
    checked = review_date({"next_review": record.get("checked_at", "")})
    if modified and checked and modified > checked:
        return CHANGED, f"Published source modification {modified} is later than human review {checked}."
    previous_url = urldefrag(str(record.get(CONTENT_URL_FIELD, ""))).url
    current_url = urldefrag(fetched.final_url).url
    if previous_url and current_url and previous_url != current_url:
        return CHANGED, f"Source destination changed from {previous_url} to {current_url}."
    stored = str(record.get(DIGEST_FIELD, ""))
    same_reading = str(record.get(DIGEST_KIND_FIELD, "")) == fetched.kind
    if stored and same_reading and stored != fetched.digest:
        return CHANGED, "Readable text changed since the last readable sweep."
    if not stored or not previous_url:
        return BASELINE_REQUIRED, (
            "A readable content or destination baseline is missing. A person must review "
            "the pending candidate and explicitly accept its reviewed baseline by hand."
        )
    if not same_reading:
        return RECORDED, (
            f"The digest covers a different reading of {fetched.content_type or 'this content type'}. "
            "Human acceptance must bind the new reading to its reviewed baseline."
        )
    return UNCHANGED, "Readable text and destination are unchanged since the last readable sweep."


def apply_fetch(record: dict[str, object], fetched: Fetched, today: str) -> None:
    """Write the machine-owned fields. `checked_at` and `fact` stay untouched."""
    record[FINAL_URL_FIELD] = fetched.final_url
    record[STATUS_FIELD] = fetched.status
    record[FETCHED_FIELD] = today
    if fetched.readable:
        outcome, _ = classify(record, fetched)
        record[UPSTREAM_FIELD] = latest_upstream_date(record, fetched)
        if outcome != UNCHANGED or PENDING_FIELD in record:
            # Preserve the reviewed baseline. Only a human can promote this candidate.
            if PENDING_FIELD not in record:
                record[REVIEW_REQUIRED_FIELD] = today
            record[PENDING_FIELD] = {
                DIGEST_FIELD: fetched.digest, DIGEST_KIND_FIELD: fetched.kind,
                CONTENT_URL_FIELD: fetched.final_url, "observed_at": today,
                UPSTREAM_FIELD: record[UPSTREAM_FIELD],
            }
    record.setdefault(DIGEST_FIELD, "")
    record.setdefault(DIGEST_KIND_FIELD, "")
    record.setdefault(CONTENT_URL_FIELD, "")
    record.setdefault(UPSTREAM_FIELD, "")


def refresh(
    *,
    skills: Path = SKILLS_DIRECTORY,
    only_skill: str = "",
    only_url: str = "",
    write: bool = False,
    spacing: float = REQUEST_SPACING,
    today: str = "",
) -> Report:
    """Sweep the index once, fetching each distinct URL a single time."""
    stamp = today or date.today().isoformat()
    report = Report()
    seen: dict[str, Fetched] = {}
    touched: dict[Path, dict[str, object]] = {}

    for path, payload, record in records(index_files(skills), skills=skills):
        skill = str(payload.get("skill", path.parent.name))
        url = str(record.get("url", ""))
        if only_skill and skill != only_skill:
            continue
        if only_url and url != only_url:
            continue
        if not url:
            continue

        passed = reverify_passed(record, stamp)
        schedule = record.get(SCHEDULE_FIELD)
        if isinstance(schedule, dict):
            due = review_date(schedule)
            late = not due or due < stamp
            if late:
                detail = (
                    f"Manual review was due {due or 'with no valid date set'}. Read the "
                    "source, then update checked_at and manual_review.next_review by hand."
                )
                if passed:
                    detail = f"{detail} {reverify_note(passed)}"
            elif passed:
                detail = reverify_note(passed)
            else:
                detail = f"Reviewed by hand {schedule.get('cadence', '')}, next review {due}."
            pending = PENDING_FIELD in record
            if pending:
                detail += " Pending human review: explicitly accept the candidate baseline by hand."
            report.outcomes.append(
                Outcome(
                    skill=skill,
                    title=str(record.get("title", "")),
                    url=url,
                    outcome=REVIEW_DUE if late or passed or pending else SCHEDULED,
                    detail=detail,
                    checked_at=str(record.get("checked_at", "")),
                    fetched=Fetched(0, "", "", "", "", "", "not fetched: reviewed by hand"),
                    next_review=due,
                )
            )
            continue

        # A fragment never reaches the server, so two records pointing at
        # different sections of one Act are one retrieval, not two.
        target = urldefrag(url).url
        if target not in seen:
            if seen and spacing:
                time.sleep(spacing)
            seen[target] = fetch(target)
        fetched = seen[target]

        outcome, detail = classify(record, fetched)
        if write:
            apply_fetch(record, fetched, stamp)
            touched[path] = payload
        if PENDING_FIELD in record:
            if outcome not in (CHANGED, MISSING, UNREADABLE, BASELINE_REQUIRED):
                outcome = REVIEW_DUE
            detail += " Pending human review: a sweep cannot accept a changed or missing baseline."
        if passed:
            # A fetch finding that already asks for an edit keeps its name; an
            # expired fact otherwise outranks an unchanged or unreachable page.
            if outcome in (CHANGED, MISSING, UNREADABLE, BASELINE_REQUIRED):
                detail = f"{detail} {reverify_note(passed)}"
            elif outcome in (BLOCKED, UNREACHABLE):
                outcome, detail = REVIEW_DUE, f"{reverify_note(passed)} Retrieval: {detail}"
            else:
                outcome, detail = REVIEW_DUE, reverify_note(passed)
        report.outcomes.append(
            Outcome(
                skill=skill,
                title=str(record.get("title", "")),
                url=url,
                outcome=outcome,
                detail=detail,
                checked_at=str(record.get("checked_at", "")),
                fetched=fetched,
            )
        )

    for path, payload in touched.items():
        dump_index(path, payload, skills=skills)
        report.written.append(path)
    return report


def render(report: Report, *, write: bool) -> str:
    """Render the sweep as Markdown, usable as an issue body unchanged."""
    counts = {name: len(report.by_outcome(name)) for name in REPORTED_OUTCOMES}
    upcoming = sorted(o.next_review for o in report.by_outcome(SCHEDULED))
    next_review = upcoming[0] if upcoming else "none scheduled"
    swept = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Primary source sweep",
        "",
        f"Swept {len(report.outcomes)} records over "
        f"{len({urldefrag(o.url).url for o in report.outcomes})} distinct pages at {swept}.",
        "",
        f"- changed: {counts[CHANGED]}",
        f"- missing (dead link, repoint the record): {counts[MISSING]}",
        f"- unreadable (a fault in this script): {counts[UNREADABLE]}",
        f"- blocked (host refuses automation, review by hand): {counts[BLOCKED]}",
        f"- unreachable (transport fault, may clear): {counts[UNREACHABLE]}",
        f"- review-due (manual review overdue or reverify_by passed): {counts[REVIEW_DUE]}",
        f"- baseline-required (review and record a readable baseline): {counts[BASELINE_REQUIRED]}",
        f"- scheduled (reviewed by hand, next review {next_review}): {counts[SCHEDULED]}",
        f"- baseline recorded or reading changed: {counts[RECORDED]}",
        f"- unchanged: {counts[UNCHANGED]}",
        "",
    ]
    if report.needs_attention:
        lines += [
            "A blocked or unreachable source is a fact about the network, not a",
            "finding about this repository, so it is listed but does not fail a",
            "--check run. Everything else asks for an edit here.",
            "",
            "A digest change means the page's readable text moved. It does not",
            "mean a rule changed, and it never changes `checked_at`: read the",
            "source and update the review date by hand if the workflow relies",
            "on material that moved.",
            "",
            "| Outcome | Skill | Source | Reviewed | Upstream | Detail |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for outcome in sorted(report.needs_attention, key=lambda o: (o.outcome, o.skill)):
            upstream = outcome.fetched.last_modified or "not published"
            lines.append(
                f"| {outcome.outcome} | `{outcome.skill}` | [{outcome.title}]({outcome.url}) "
                f"| {outcome.checked_at} | {upstream} | {outcome.detail} |"
            )
        lines.append("")
    else:
        lines += ["No actionable or network findings were reported.", ""]
    if write and report.written:
        lines += [f"Updated {len(report.written)} index files.", ""]
    return "\n".join(lines)


def _review_binding_matches(record: dict[str, object], checked: str) -> bool:
    since = review_date({"next_review": record[REVIEW_REQUIRED_FIELD]})
    binding = record.get(REVIEWED_FIELD)
    return not (not since or checked < since or not isinstance(binding, dict)
                or any(binding.get(key) != record.get(key)
                       for key in (DIGEST_FIELD, DIGEST_KIND_FIELD, CONTENT_URL_FIELD, "checked_at"))
                or binding.get(UPSTREAM_FIELD) != record.get(UPSTREAM_FIELD, ""))


def _human_review_readiness(record: dict[str, object], today: str) -> tuple[str, str]:
    """Return the human check date and its first blocking problem."""
    checked = ""
    if PENDING_FIELD in record:
        return checked, "Pending human review: explicitly accept the candidate baseline by hand."
    checked = review_date({"next_review": record.get("checked_at", "")})
    if not checked or checked > today:
        return checked, "Missing, malformed or future human check date."
    if not isinstance(record.get("fact"), str) or not str(record["fact"]).strip():
        return checked, "The human review does not record a fact."
    if REVIEW_REQUIRED_FIELD in record:
        if not _review_binding_matches(record, checked):
            return checked, "Human acceptance must bind the digest, reading, destination, published date and current review date."
    passed = reverify_passed(record, today)
    if passed or (record.get("volatile") and REVERIFY_FIELD not in record):
        return checked, "The fact needs a current reverify_by date."
    if record.get("volatile"):
        due = review_date({"next_review": record.get(REVERIFY_FIELD, "")})
        if (date.fromisoformat(due) - date.fromisoformat(checked)).days > 400:
            return checked, "The volatile fact exceeds the existing 400-day review bound."
    status = str(record.get("verification_status", ""))
    if status == "indexed-source-discovery-only":
        return checked, "The record is discovery-only; a schedule does not establish human review."
    return checked, ""


def source_readiness(record: dict[str, object], outcome: Outcome, today: str) -> tuple[bool, str]:
    """Assess one record independently of weekly sweep health."""
    checked, problem = _human_review_readiness(record, today)
    if problem:
        return False, problem
    status = str(record.get("verification_status", ""))
    modified = latest_upstream_date(record, outcome.fetched)
    if modified and modified > checked:
        return False, "The source changed after the recorded human review."
    schedule = record.get(SCHEDULE_FIELD)
    if isinstance(schedule, dict) and outcome.outcome == REVIEW_DUE:
        due = review_date(schedule)
        return False, (f"Manual review was due {due or 'with no valid date set'}; "
                       "complete the human review and update its schedule by hand.")
    if outcome.outcome in (CHANGED, MISSING, UNREADABLE, BASELINE_REQUIRED, RECORDED, REVIEW_DUE):
        return False, f"Retrieval requires review: {outcome.outcome}."
    if schedule is not None:
        if not isinstance(schedule, dict):
            return False, "Malformed manual review schedule."
        due = review_date(schedule)
        if (not due or due < today or not isinstance(schedule.get("cadence"), str)
                or not str(schedule["cadence"]).strip()):
            return False, "Manual review is overdue or its schedule is malformed."
        warning = " Retrieval remains unavailable." if outcome.outcome in (BLOCKED, UNREACHABLE) else ""
        return True, f"READY_MANUAL: human review {checked}, next review {due}.{warning}"
    if status.startswith("unavailable"):
        return False, "The record is explicitly unverified."
    if outcome.outcome != UNCHANGED:
        return False, f"Retrieval requires review: {outcome.outcome}."
    return True, f"READY: human review {checked}; retrieval and destination unchanged."


def preflight(skill: str, *, skills: Path = SKILLS_DIRECTORY, today: str = "",
              spacing: float = REQUEST_SPACING) -> tuple[str, int]:
    """Read-only check of every indexed source for one exact skill."""
    stamp = today or date.today().isoformat()
    heading = f"# Skill source preflight: {skill}\n\nEvaluated: {stamp}\n"
    boundary = ("\nReadiness concerns recorded source evidence. Verify the exact fact and its "
                "effective period at use time; this is not legal, tax or professional approval.\n")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", skill):
        return heading + "\nInvalid exact skill name.\n" + boundary, 1
    directory = skills / skill
    if not directory.resolve().is_relative_to(skills.resolve()) or not (directory / "SKILL.md").is_file():
        return heading + "\nNo matching skill.\n" + boundary, 1
    index = directory / "sources.json"
    if not index.is_file():
        if (directory / "sources.exempt.json").is_file():
            return heading + "\nUNAVAILABLE: source exemption requires live manual verification.\n" + boundary, 2
        return heading + "\nNo source index.\n" + boundary, 1
    if index.is_symlink():
        return heading + "\nLinked source index is unsupported.\n" + boundary, 1
    try:
        payload = load_index(index, skills=skills)
        entries = payload.get("sources")
        if (payload.get("skill") != skill or not isinstance(entries, list) or not entries
                or any(not isinstance(item, dict) or not isinstance(item.get("url"), str)
                       or not str(item["url"]).strip() for item in entries)):
            return heading + "\nIncomplete or mismatched source index.\n" + boundary, 1
        report = refresh(skills=skills, only_skill=skill, spacing=spacing, today=stamp)
    except (OSError, UnicodeError, ValueError, AttributeError) as exc:
        return heading + f"\nInvalid source index: {exc}.\n" + boundary, 1
    if len(report.outcomes) != len(entries):
        return heading + "\nSource inventory changed or was incomplete.\n" + boundary, 1
    lines = [heading]
    ready = True
    for record, outcome in zip(entries, report.outcomes):
        usable, detail = source_readiness(record, outcome, stamp)
        ready = ready and usable
        lines.append(f"\n- {outcome.url}: {detail}")
        manual = isinstance(record.get(SCHEDULE_FIELD), dict)
        retrieval = "not attempted: explicit manual review" if manual else outcome.outcome
        lines.append(f"  Human check: {record.get('checked_at', 'unknown')}; "
                     f"retrieval: {retrieval}; reverify by: {record.get(REVERIFY_FIELD, 'not applicable')}.")
        if manual and str(record.get("verification_status", "")).startswith("unavailable"):
            lines.append("  Recorded automatic retrieval remains unavailable; it was not retried by this preflight.")
    return "\n".join(lines) + boundary, 0 if ready else 2


def _argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python scripts/source_refresh.py",
        description="Re-fetch the indexed primary sources and report which ones moved.",
    )
    parser.add_argument("--skill", default="", help="Limit the sweep to one skill directory name.")
    parser.add_argument("--url", default="", help="Limit the sweep to one indexed URL.")
    parser.add_argument("--preflight", action="store_true",
                        help="Read-only source readiness check for one --skill; separate from weekly sweep health.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Record pending digest candidates and the fetch date. Never accepts a baseline or touches checked_at.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit 2 when source text or destination changes, a source goes missing or is "
        "unreadable, a readable baseline is missing, or a manual review is overdue. "
        "Blocked and unreachable sources are "
        "reported without failing the run.",
    )
    parser.add_argument("--report", default="", help="Also write the Markdown report to this path.")
    parser.add_argument(
        "--spacing",
        type=float,
        default=REQUEST_SPACING,
        help=f"Seconds between requests (default {REQUEST_SPACING}).",
    )
    return parser


def main(argv: Sequence[str] | None = None, *, skills: Path = SKILLS_DIRECTORY) -> int:
    parser = _argument_parser()
    arguments = parser.parse_args(argv)

    if arguments.preflight:
        if not arguments.skill or arguments.write or arguments.check or arguments.url:
            parser.error("--preflight requires --skill and cannot use --write, --check or --url")
        rendered, exit_code = preflight(arguments.skill, skills=skills, spacing=arguments.spacing)
        print(rendered)
        if arguments.report:
            # The local CLI intentionally replaces the operator-selected report.
            Path(arguments.report).write_text(rendered, encoding="utf-8")  # NOSONAR
        return exit_code

    try:
        report = refresh(
            skills=skills,
            only_skill=arguments.skill,
            only_url=arguments.url,
            write=arguments.write,
            spacing=arguments.spacing,
        )
    except (OSError, UnicodeError, ValueError, AttributeError) as exc:
        print(f"Invalid source index: {exc}.", file=sys.stderr)
        return 1
    if not report.outcomes:
        print("No source records matched.", file=sys.stderr)
        return 1

    rendered = render(report, write=arguments.write)
    print(rendered)
    if arguments.report:
        # The local CLI intentionally replaces the operator-selected report.
        Path(arguments.report).write_text(rendered, encoding="utf-8")  # NOSONAR
    if arguments.check and report.actionable:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
