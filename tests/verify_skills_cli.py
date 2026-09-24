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
# A registry download and a skill listing take seconds; 5 minutes is a stall.
NPX_TIMEOUT_SECONDS = 300
EXPECTED_SKILLS = {
    "au-ato-penalties-interest",
    "au-bookkeeping",
    "au-business-formation",
    "au-capital-gains",
    "au-company-tax",
    "au-crypto-tax",
    "au-deceased-estates",
    "au-division-293",
    "au-division-296",
    "au-etp-redundancy",
    "au-financial-statements",
    "au-foreign-income",
    "au-forex-review",
    "au-gst-property",
    "au-gst-registration-review",
    "au-individual-return",
    "au-land-tax",
    "au-medicare-review",
    "au-nonresident-cgt",
    "au-not-for-profit",
    "au-partnership-tax",
    "au-payg-instalment-variation",
    "au-payroll-review",
    "au-psi-review",
    "au-rd-incentive",
    "au-rental-property",
    "au-return-amendment",
    "au-small-business-cgt",
    "au-smsf-year-end",
    "au-sole-trader",
    "au-super-contribution-caps",
    "au-tax-planning-review",
    "au-tax-rates-verification",
    "au-tax-residency",
    "au-transfer-duty",
    "au-transfer-pricing",
    "au-trust-distributions",
    "au-wfh-deductions",
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
    "tax-invoice-review",
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
    try:
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
            # This downloads the CLI from the npm registry. Without a bound, a stalled
            # registry or a CLI waiting on input blocks until the workflow timeout.
            timeout=NPX_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        print(
            f"Skills CLI discovery timed out after {NPX_TIMEOUT_SECONDS}s: the npm "
            "registry stalled or the CLI waited on input",
            file=sys.stderr,
        )
        return 1
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
