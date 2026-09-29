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
URL. ``content_url`` accompanies the last readable digest and survives failed
attempts. Older records establish
that destination baseline on their next reviewed write. Until then, read-only
checks report the missing baseline and existing comparable digests still
detect content changes.

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
from urllib.parse import urldefrag

REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS_DIRECTORY = REPOSITORY / ".claude" / "skills"

TIMEOUT = 30
TRIES = 3
RETRY_DELAY = 6.0
# Spacing between requests to the same run. These are public-sector sites
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

    @property
    def reachable(self) -> bool:
        return self.status == 200 and not self.error

    @property
    def readable(self) -> bool:
        return self.reachable and bool(self.digest)


def fetch(url: str, *, tries: int = TRIES, delay: float = RETRY_DELAY) -> Fetched:
    """Retrieve one source. A blocked or missing page is data, not a failure.

    Several of these hosts refuse automated retrieval outright, so an
    unreachable source has to be recorded and reported rather than raised. The
    sweep's job is to tell a reviewer what to look at, and "this one can no
    longer be checked from CI" is exactly that kind of finding.
    """
    request = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml,*/*"}
    )
    last_error = ""
    for attempt in range(1, tries + 1):
        try:
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                body = response.read()
                content_type = (response.headers.get_content_type() or "").lower()
                digest, kind = body_digest(
                    body, content_type, response.headers.get_content_charset()
                )
                return Fetched(
                    status=response.status,
                    final_url=response.geturl(),
                    digest=digest,
                    kind=kind,
                    content_type=content_type,
                    last_modified=upstream_last_modified(
                        body,
                        response.headers.get("Last-Modified"),
                        response.headers.get("Date"),
                    ),
                    error="",
                )
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


def index_files(skills: Path = SKILLS_DIRECTORY) -> Iterator[Path]:
    yield from sorted(skills.glob("*/sources.json"))


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


def load_index(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def dump_index(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def records(paths: Iterable[Path]) -> Iterator[tuple[Path, dict[str, object], dict[str, object]]]:
    for path in paths:
        payload = load_index(path)
        sources = payload.get("sources")
        if not isinstance(sources, list):
            continue
        for record in sources:
            if isinstance(record, dict):
                yield path, payload, record


def classify(record: dict[str, object], fetched: Fetched) -> tuple[str, str]:
    """Name what happened to one record, and say why in one line."""
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
            "the source, then run python scripts/source_refresh.py --write to record it."
        )
    if not same_reading:
        return RECORDED, (
            f"The digest covers a different reading of {fetched.content_type or 'this content type'}. "
            "A reviewed write can update the baseline."
        )
    return UNCHANGED, "Readable text and destination are unchanged since the last readable sweep."


def apply_fetch(record: dict[str, object], fetched: Fetched, today: str) -> None:
    """Write the machine-owned fields. `checked_at` and `fact` stay untouched."""
    record[FINAL_URL_FIELD] = fetched.final_url
    record[STATUS_FIELD] = fetched.status
    record[FETCHED_FIELD] = today
    if fetched.readable:
        record[DIGEST_FIELD] = fetched.digest
        record[DIGEST_KIND_FIELD] = fetched.kind
        record[CONTENT_URL_FIELD] = fetched.final_url
        record[UPSTREAM_FIELD] = fetched.last_modified
    else:
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

    for path, payload, record in records(index_files(skills)):
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
            report.outcomes.append(
                Outcome(
                    skill=skill,
                    title=str(record.get("title", "")),
                    url=url,
                    outcome=REVIEW_DUE if late or passed else SCHEDULED,
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
            if outcome == BASELINE_REQUIRED:
                outcome = RECORDED
                detail = "Readable content and destination baseline recorded."
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
        dump_index(path, payload)
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


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python scripts/source_refresh.py",
        description="Re-fetch the indexed primary sources and report which ones moved.",
    )
    parser.add_argument("--skill", default="", help="Limit the sweep to one skill directory name.")
    parser.add_argument("--url", default="", help="Limit the sweep to one indexed URL.")
    parser.add_argument(
        "--write",
        action="store_true",
        help="Record the digest and fetch date in sources.json. Never touches checked_at.",
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
    arguments = parser.parse_args(argv)

    report = refresh(
        only_skill=arguments.skill,
        only_url=arguments.url,
        write=arguments.write,
        spacing=arguments.spacing,
    )
    if not report.outcomes:
        print("No source records matched.", file=sys.stderr)
        return 1

    rendered = render(report, write=arguments.write)
    print(rendered)
    if arguments.report:
        Path(arguments.report).write_text(rendered, encoding="utf-8")
    if arguments.check and report.actionable:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
