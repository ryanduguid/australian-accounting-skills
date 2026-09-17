"""Decide what a source sweep run actually established.

`source_refresh.py --check --report sweep.md` exits 0 when every actionable
source came back clean, 2 when at least one needs an edit here, and 1 when it
could not sweep at all: no records matched, or an exception before the report
was written. argparse also exits 2, before any report exists. The workflow used
to treat everything up to 2 as a success and then branch on 0 or 2, so an exit
1 passed the job silently and an exit 2 with no report counted as findings.

This script is the one place that turns an exit status and a report file into
an outcome. Only two outcomes exist, `clean` and `findings`, and each requires
a report that was written during this run and agrees with the status. Anything
else is a failed run, not a quiet one.
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

HEADER = "# Primary source sweep"
SWEPT = re.compile(
    r"^Swept (?P<records>\d+) records over (?P<pages>\d+) distinct pages at "
    r"(?P<stamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC\.$",
    re.M,
)
COUNT = re.compile(r"^- (?P<name>changed|missing|unreadable|blocked|unreachable)[^:]*: (?P<count>\d+)$", re.M)
STAMP_FORMAT = "%Y-%m-%d %H:%M"
# What `--check` fails on: the same three outcomes `source_refresh.ACTIONABLE`
# names. The counts come from the report, so a report that disagrees with the
# exit status is caught here rather than trusted.
ACTIONABLE = ("changed", "missing", "unreadable")
UNCHECKED = ("blocked", "unreachable")


class SweepError(Exception):
    """The run established nothing the workflow may act on."""


@dataclass(frozen=True)
class Outcome:
    name: str
    comment: str

    def lines(self) -> list[str]:
        return [f"outcome={self.name}", f"comment={self.comment}"]


def parse_report(text: str, started: datetime) -> dict[str, int]:
    """Counts from a report written by this run; anything less is an error."""
    if not text.startswith(HEADER + "\n"):
        raise SweepError("the report does not start with the sweep header")
    swept = SWEPT.search(text)
    if swept is None:
        raise SweepError("the report has no 'Swept N records' line")
    stamp = datetime.strptime(swept.group("stamp"), STAMP_FORMAT).replace(tzinfo=timezone.utc)
    if stamp < started.replace(second=0, microsecond=0):
        raise SweepError(f"the report was written at {swept.group('stamp')} UTC, before this run started")
    counts = {match.group("name"): int(match.group("count")) for match in COUNT.finditer(text)}
    missing = [name for name in ACTIONABLE + UNCHECKED if name not in counts]
    if missing:
        raise SweepError(f"the report has no count for {', '.join(missing)}")
    counts["records"] = int(swept.group("records"))
    if counts["records"] == 0:
        raise SweepError("the report covers no records")
    return counts


def decide(status: int, counts: dict[str, int]) -> Outcome:
    """Match the exit status against what the report says, and name the result."""
    actionable = sum(counts[name] for name in ACTIONABLE)
    if status == 2:
        if actionable == 0:
            raise SweepError("exit 2 with a report that lists nothing actionable")
        return Outcome("findings", f"{actionable} sources need an edit here.")
    if status != 0:
        raise SweepError(f"source_refresh.py exited {status}")
    if actionable:
        raise SweepError(f"exit 0 with a report that lists {actionable} actionable sources")
    unchecked = {name: counts[name] for name in UNCHECKED if counts[name]}
    if not unchecked:
        return Outcome("clean", "Every indexed source was retrieved and none had moved.")
    listed = " and ".join(f"{count} {name}" for name, count in unchecked.items())
    return Outcome(
        "clean",
        f"No indexed source needs an edit here. {listed} sources could not be checked "
        "and are listed in the report.",
    )


def outcome(status: int, report: Path, started: datetime) -> Outcome:
    if status not in (0, 2):
        raise SweepError(f"source_refresh.py exited {status}")
    if not report.is_file():
        raise SweepError(f"source_refresh.py exited {status} but wrote no report at {report}")
    return decide(status, parse_report(report.read_text(encoding="utf-8"), started))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--status", type=int, required=True, help="Exit status of source_refresh.py.")
    parser.add_argument("--report", type=Path, required=True, help="Report path given to --report.")
    parser.add_argument(
        "--started",
        required=True,
        help="UTC time the sweep step started, as YYYY-MM-DDTHH:MM:SSZ from `date -u`.",
    )
    arguments = parser.parse_args(argv)
    try:
        started = datetime.strptime(arguments.started, "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=timezone.utc
        )
        result = outcome(arguments.status, arguments.report, started)
    except (SweepError, ValueError, OSError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    for line in result.lines():
        print(line)
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write("\n".join(result.lines()) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
