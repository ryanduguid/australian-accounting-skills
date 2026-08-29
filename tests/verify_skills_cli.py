"""Verify that the documented Skills CLI consumer discovers every skill."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
SKILLS_CLI_VERSION = "1.5.22"
EXPECTED_SKILLS = {
    "bas-preparation",
    "cashflow-forecast-13week",
    "coal-lsl-levy",
    "contract-cost-tracking",
    "contracting-exports",
    "contractor-super-tpar",
    "div7a-compliance",
    "fbt-annual-workflow",
    "fuel-tax-credits",
    "month-end-close",
    "payroll-tax-contractors",
    "plant-and-equipment-costing",
    "progress-claim-preparation",
    "retention-schedule",
    "stp-finalisation",
    "workpaper-tie-out",
    "wip-over-under-billing",
    "xero-exports",
    "year-end-workpapers",
}
ANSI_ESCAPE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
SKILL_LINE = re.compile(r"^[|│]\s{2,}([a-z0-9][a-z0-9-]*)\s*$")


def main() -> int:
    npx = shutil.which("npx")
    if npx is None:
        print("npx is required for the Skills CLI discovery check", file=sys.stderr)
        return 1

    environment = os.environ.copy()
    environment.update(
        {
            "CI": "1",
            "DISABLE_TELEMETRY": "1",
            "DO_NOT_TRACK": "1",
            "FORCE_COLOR": "0",
            "NO_COLOR": "1",
        }
    )
    result = subprocess.run(
        [
            npx,
            "--yes",
            f"skills@{SKILLS_CLI_VERSION}",
            "add",
            ".",
            "--list",
        ],
        cwd=REPOSITORY,
        env=environment,
        capture_output=True,
        check=False,
        encoding="utf-8",
        errors="replace",
        text=True,
    )
    output = ANSI_ESCAPE.sub("", f"{result.stdout}\n{result.stderr}").replace("\r", "")
    discovered = {
        match.group(1)
        for line in output.splitlines()
        if (match := SKILL_LINE.fullmatch(line.strip())) is not None
    }
    count_match = re.search(r"\bFound\s+(\d+)\s+skills?\b", output)
    reported_count = int(count_match.group(1)) if count_match else None

    if result.returncode != 0 or reported_count != len(EXPECTED_SKILLS) or discovered != EXPECTED_SKILLS:
        print(output, file=sys.stderr)
        print(
            "Skills CLI discovery mismatch: "
            f"exit={result.returncode}, reported={reported_count}, "
            f"expected={sorted(EXPECTED_SKILLS)}, discovered={sorted(discovered)}",
            file=sys.stderr,
        )
        return 1

    print(
        f"skills@{SKILLS_CLI_VERSION} discovered all "
        f"{len(EXPECTED_SKILLS)} expected skills"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
