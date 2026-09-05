#!/usr/bin/env python3
"""Fail-closed checks for the fixed, fabricated Markdown regression pack."""

from __future__ import annotations

import html
import importlib.util
import json
import os
import re
import stat
import subprocess
import sys
import unicodedata
from pathlib import Path, PurePosixPath

import yaml
from yaml.tokens import AliasToken, AnchorToken, TagToken


ROOT = Path(__file__).resolve().parents[1]
VALIDATION = ROOT / "validation"
EXPECTED_CASE_NAMES = {
    "bas-export-manifest-rounding.md",
    "bas-g10-g11.md",
    "bas-stp-w3-w4.md",
    "cashflow-super-regime-transition.md",
    "coal-lsl-levy-unverified-rate.md",
    "contract-cost-unallocated-plant.md",
    "div7a-upe-review.md",
    "export-manifest-rounding.md",
    "fbt-carparking-missing-declaration.md",
    "fuel-tax-credits-missing-docket.md",
    "payroll-tax-contractor-characterisation.md",
    "post-journal-provenance-tie-out.md",
    "progress-claim-missing-reference-date.md",
    "retention-release-missing-deed.md",
    "standalone-skill-safety-boundary.md",
    "stp-current-vs-overdue-sg.md",
    "wip-cost-to-complete-gap.md",
}
EXPECTED_VALIDATION = {
    "validation/README.md",
    "validation/results.schema.json",
    *(f"validation/cases/{name}" for name in EXPECTED_CASE_NAMES),
}
EXPECTED_SUPPORT = {
    "CLAUDE.md",
    ".claude/rules/accounting-safety.md",
    "scripts/strict_yaml.py",
    "scripts/validate_validation.py",
    "tests/test_validation_pack.py",
}
# A recorded run: YYYY-MM-DD-<slug>.json under validation/results/. Any number
# may exist; each must be tracked and must hold only a pass or fail per card.
RESULT_FILE_RE = re.compile(r"^validation/results/(\d{4}-\d{2}-\d{2})-[a-z0-9]+(?:-[a-z0-9]+)*\.json$")
RESULT_KEYS = ("model", "run_date", "skills_version", "runner", "results")
RESULT_VERDICTS = ("pass", "fail")
CASE_IDS = frozenset(name.removesuffix(".md") for name in EXPECTED_CASE_NAMES)
REQUIRED_SECTIONS = (
    "## Scenario",
    "## Task",
    "## Synthetic inputs",
    "## Deliberately unavailable evidence",
    "## Required checks",
    "## Must not do",
    "## Source-verification and reviewer boundary",
)
ALLOWED_METADATA = {"id", "synthetic", "target_skills"}
SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\Z")
HTML_MARKUP = re.compile(r"<!--.*?-->|<[^>]*>", re.S)
INLINE_MARKDOWN_LINK = re.compile(
    r"!?\[(?P<label>[^\]\r\n]*)\]\((?:<[^>\r\n]+>|[^)\r\n]+)\)"
)
REFERENCE_MARKDOWN_LINK = re.compile(
    r"!?\[(?P<label>[^\]\r\n]*)\]\[[^\]\r\n]*\]"
)
MARKDOWN_FORMATTING = str.maketrans("", "", "\\`*~[]()")
MARKDOWN_FORMATTING_WITH_UNDERSCORE = str.maketrans("", "", "\\`*_~[]()")
SENSITIVE_PATTERNS = {
    "email address": re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
    "labelled Australian identifier": re.compile(
        r"\b(?:A\s*B\s*N|A\s*C\s*N|T\s*F\s*N)\s*"
        r"(?:number|no\.?|[:#-])?\s*\d",
        re.I,
    ),
    "unlabelled long numeric identifier": re.compile(
        r"(?<![\d,.])\d(?:[ -]?\d){7,10}(?![\d,.])"
    ),
    "BSB or bank account": re.compile(
        r"\b(?:BSB|bank\s+account)\s*(?:number|no\.?|[:#-])?\s*\d", re.I
    ),
    "phone number": re.compile(r"\b(?:phone|mobile)\s*(?:number|no\.?|[:#-])?\s*\+?\d", re.I),
    "private key": re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----"),
    "bearer credential": re.compile(r"\bBearer\s+[A-Za-z0-9._~-]{12,}\b", re.I),
    "API credential": re.compile(r"\b(?:sk|pk|api)[_-][A-Za-z0-9_-]{12,}\b", re.I),
    "JWT-like credential": re.compile(
        r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
    ),
    "realistic entity suffix": re.compile(r"\b(?:Pty\s+Ltd|Limited)\b", re.I),
}
DATED_RULE = re.compile(
    r"\b(?:from|effective|due(?:\s+by)?|deadline)\s+"
    r"(?:\d{1,2}\s+[A-Z][a-z]+\s+20\d{2}|\d+(?:\.\d+)?%)\b",
    re.I,
)


class ValidationError(ValueError):
    """Expected validation failure with a user-actionable message."""


_STRICT_YAML = ROOT / "scripts" / "strict_yaml.py"
_STRICT_YAML_SPEC = importlib.util.spec_from_file_location("strict_yaml", _STRICT_YAML)
if _STRICT_YAML_SPEC is None or _STRICT_YAML_SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError(f"cannot load {_STRICT_YAML}")
strict_yaml = importlib.util.module_from_spec(_STRICT_YAML_SPEC)
_STRICT_YAML_SPEC.loader.exec_module(strict_yaml)

UniqueKeySafeLoader = strict_yaml.unique_key_safe_loader(
    ValidationError,
    field_noun="YAML field",
    keys_noun="YAML mapping keys",
)


def relative(path: Path, root: Path = ROOT) -> str:
    return path.relative_to(root).as_posix()


def read_utf8(path: Path) -> str:
    """Read one expected source strictly; never replace undecodable bytes."""
    try:
        payload = path.read_bytes()
    except OSError as error:
        raise ValidationError(f"cannot read {path}: {error}") from error
    try:
        text = payload.decode("utf-8", errors="strict")
    except UnicodeDecodeError as error:
        raise ValidationError(f"{path} is not strict UTF-8: {error}") from error
    if "\x00" in text:
        raise ValidationError(f"{path} contains a NUL byte")
    text = text.replace("\r\n", "\n")
    if "\r" in text:
        raise ValidationError(f"{path} contains a bare carriage return")
    for character in text:
        if character not in {"\n", "\t"} and unicodedata.category(character) in {
            "Cc",
            "Cf",
        }:
            raise ValidationError(
                f"{path} contains a Unicode control/format character "
                f"U+{ord(character):04X}"
            )
    return text


def is_reparse_point(path: Path) -> bool:
    """Detect symlinks and Windows junction/reparse points without following."""
    try:
        info = path.lstat()
    except OSError as error:
        raise ValidationError(f"cannot inspect {path}: {error}") from error
    attributes = getattr(info, "st_file_attributes", 0)
    reparse = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return path.is_symlink() or bool(attributes & reparse)


def check_expected_path(path: Path, root: Path = ROOT) -> None:
    """Require a regular in-repository file with no reparse component."""
    try:
        path.resolve(strict=True).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise ValidationError(f"unsafe or missing expected path: {path}") from error

    current = path
    while current != root:
        if is_reparse_point(current):
            raise ValidationError(f"symlink or reparse point is not permitted: {current}")
        current = current.parent
    if not path.is_file():
        raise ValidationError(f"expected regular file: {path}")


def inventory_validation_tree(root: Path = ROOT) -> set[str]:
    """List validation names without reading unexpected file contents."""
    base = root / "validation"
    if is_reparse_point(base) or not base.is_dir():
        raise ValidationError("validation must be a real directory")

    found: set[str] = set()
    pending = [base]
    while pending:
        directory = pending.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as error:
            raise ValidationError(f"cannot inspect {directory}: {error}") from error
        for entry in entries:
            path = Path(entry.path)
            rel = relative(path, root)
            if entry.is_symlink() or is_reparse_point(path):
                raise ValidationError(f"validation contains a symlink/reparse point: {rel}")
            if entry.is_dir(follow_symlinks=False):
                pending.append(path)
            elif entry.is_file(follow_symlinks=False):
                found.add(rel)
            else:
                raise ValidationError(f"validation contains a non-regular entry: {rel}")
    return found


def parse_front_matter(text: str, card_name: str) -> tuple[dict[str, object], str]:
    """Parse the deliberately small card schema as strict, unique-key YAML."""
    match = re.match(r"\A---\r?\n(?P<yaml>.*?)\r?\n---\r?\n", text, re.S)
    if not match:
        raise ValidationError("front matter must be the first document block")
    raw = match.group("yaml")
    try:
        for token in yaml.scan(raw):
            if isinstance(token, (AliasToken, AnchorToken, TagToken)):
                raise ValidationError("YAML aliases, anchors and tags are not permitted")
        loaded = yaml.load(raw, Loader=UniqueKeySafeLoader)
    except ValidationError:
        raise
    except yaml.YAMLError as error:
        raise ValidationError(f"front matter must be valid YAML: {error}") from error

    if not isinstance(loaded, dict):
        raise ValidationError("front matter must be a YAML mapping")
    keys = set(loaded)
    if keys != ALLOWED_METADATA:
        missing = sorted(ALLOWED_METADATA - keys)
        unknown = sorted(str(key) for key in keys - ALLOWED_METADATA)
        raise ValidationError(
            f"front-matter fields must be exact; missing={missing}, unknown={unknown}"
        )

    card_id = loaded["id"]
    if not isinstance(card_id, str) or SLUG.fullmatch(card_id) is None:
        raise ValidationError("id must be a lowercase hyphenated slug")
    if card_id != Path(card_name).stem:
        raise ValidationError(f"id must match filename stem: {Path(card_name).stem}")
    if loaded["synthetic"] is not True or not re.search(
        r"(?m)^synthetic: true$", raw
    ):
        raise ValidationError("synthetic must be the literal boolean true")

    skills = loaded["target_skills"]
    if not isinstance(skills, list) or not skills:
        raise ValidationError("target_skills must be a non-empty YAML list")
    if any(not isinstance(skill, str) or SLUG.fullmatch(skill) is None for skill in skills):
        raise ValidationError("every target skill must be a lowercase hyphenated slug")
    if len(skills) != len(set(skills)):
        raise ValidationError("target_skills contains a duplicate")
    return loaded, text[match.end() :]


def normalise_for_sensitive_scan(text: str) -> str:
    """Expose common rendered-Markdown/entity obfuscation to safety patterns."""
    decoded = unicodedata.normalize("NFKC", html.unescape(text))
    decoded = "".join(
        character
        for character in decoded
        if unicodedata.category(character) != "Cf"
    )
    visible = HTML_MARKUP.sub("", decoded)
    visible = INLINE_MARKDOWN_LINK.sub(lambda match: match.group("label"), visible)
    visible = REFERENCE_MARKDOWN_LINK.sub(lambda match: match.group("label"), visible)
    return "\n::scan-variant-boundary::\n".join(
        (
            decoded,
            decoded.translate(MARKDOWN_FORMATTING),
            decoded.translate(MARKDOWN_FORMATTING_WITH_UNDERSCORE),
            visible.translate(MARKDOWN_FORMATTING),
            visible.translate(MARKDOWN_FORMATTING_WITH_UNDERSCORE),
        )
    )


def check_sensitive_content(text: str) -> None:
    """Reject common private-data, credential and stale-rule fixture content."""
    scan_text = normalise_for_sensitive_scan(text)
    for label, pattern in SENSITIVE_PATTERNS.items():
        if pattern.search(scan_text):
            raise ValidationError(f"possible {label}")
    if DATED_RULE.search(scan_text):
        raise ValidationError("embeds a dated/rate rule instead of a live-source check")


def git_entries(paths: list[str], root: Path = ROOT) -> dict[str, str]:
    """Return staged/tracked path modes, failing closed on any Git error."""
    command = ["git", "ls-files", "--stage", "-z", "--", *paths]
    try:
        result = subprocess.run(command, cwd=root, capture_output=True, check=False)
    except OSError as error:
        raise ValidationError(f"cannot run Git inventory: {error}") from error
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValidationError(f"Git inventory failed: {detail or result.returncode}")

    entries: dict[str, str] = {}
    for raw_entry in result.stdout.split(b"\0"):
        if not raw_entry:
            continue
        try:
            metadata, raw_path = raw_entry.split(b"\t", 1)
            mode = metadata.split(b" ", 1)[0].decode("ascii", errors="strict")
            path = raw_path.decode("utf-8", errors="strict")
        except (ValueError, UnicodeDecodeError) as error:
            raise ValidationError("Git returned an undecodable inventory entry") from error
        if path in entries:
            raise ValidationError(f"duplicate Git inventory entry: {path}")
        entries[path] = mode
    return entries


def git_check(command: list[str], label: str, root: Path = ROOT) -> None:
    try:
        result = subprocess.run(
            command,
            cwd=root,
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            check=False,
        )
    except OSError as error:
        raise ValidationError(f"cannot run {label}: {error}") from error
    if result.returncode != 0:
        detail = result.stdout.strip() or result.stderr.strip() or str(result.returncode)
        raise ValidationError(f"{label} failed: {detail}")


def check_ignored(path: str, root: Path = ROOT) -> None:
    result = subprocess.run(
        ["git", "check-ignore", "--no-index", "--quiet", "--", path],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if result.returncode == 0:
        raise ValidationError(f"tracked source is ignored by .gitignore: {path}")
    if result.returncode != 1:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValidationError(f"git check-ignore failed for {path}: {detail}")


def _strict_json(text: str, label: str) -> object:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        mapping: dict[str, object] = {}
        for key, value in pairs:
            if key in mapping:
                raise ValidationError(f"{label}: duplicate JSON key {key!r}")
            mapping[key] = value
        return mapping

    try:
        return json.loads(text, object_pairs_hook=reject_duplicates)
    except ValueError as error:
        raise ValidationError(f"{label}: not valid JSON ({error})") from error


def split_result_files(names: set[str]) -> tuple[set[str], set[str]]:
    """Separate recorded runs from the fixed inventory."""
    results = {name for name in names if RESULT_FILE_RE.match(name)}
    return names - results, results


def check_results_schema(text: str) -> None:
    """The published schema must name exactly the cards the checker knows."""
    schema = _strict_json(text, "validation/results.schema.json")
    try:
        assert isinstance(schema, dict)
        enum = schema["properties"]["results"]["items"]["properties"]["case"]["enum"]
        assert isinstance(enum, list)
    except (AssertionError, KeyError, TypeError) as error:
        raise ValidationError("results schema does not declare the case enum") from error
    if sorted(enum) != sorted(CASE_IDS) or len(enum) != len(CASE_IDS):
        raise ValidationError(
            "results schema case enum does not match the card inventory: "
            f"missing={sorted(CASE_IDS - set(enum))}, unknown={sorted(set(enum) - CASE_IDS)}"
        )


def check_result_file(rel: str, text: str) -> None:
    """A run records a pass or fail per card and nothing else."""
    match = RESULT_FILE_RE.match(rel)
    if match is None:
        raise ValidationError("result file name must be YYYY-MM-DD-<slug>.json")
    data = _strict_json(text, rel)
    if not isinstance(data, dict) or sorted(data) != sorted(RESULT_KEYS):
        raise ValidationError(
            f"result keys must be exactly {', '.join(RESULT_KEYS)}; "
            "prompts, outputs and transcripts do not belong in a result file"
        )
    for key in ("model", "run_date", "skills_version", "runner"):
        if not isinstance(data[key], str) or not data[key].strip():
            raise ValidationError(f"{key} must be a non-empty string")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", data["run_date"]) or data["run_date"] != match.group(1):
        raise ValidationError("run_date must be YYYY-MM-DD and match the file name")
    results = data["results"]
    if not isinstance(results, list) or not results:
        raise ValidationError("results must be a non-empty list")
    seen: set[str] = set()
    for entry in results:
        if not isinstance(entry, dict) or sorted(entry) != ["case", "verdict"]:
            raise ValidationError("each result must hold exactly case and verdict")
        if entry["case"] not in CASE_IDS:
            raise ValidationError(f"unknown case: {entry['case']!r}")
        if entry["case"] in seen:
            raise ValidationError(f"duplicate case: {entry['case']}")
        seen.add(entry["case"])
        if entry["verdict"] not in RESULT_VERDICTS:
            raise ValidationError(f"{entry['case']}: verdict must be pass or fail")
    # The date is the one long numeric string a run legitimately carries; the
    # free-text fields are where an identifier or a pasted output would land.
    for key in ("model", "skills_version", "runner"):
        check_sensitive_content(data[key])


def check_text(relative_path: str, text: str) -> None:
    for line_number, line in enumerate(text.splitlines(), start=1):
        if line.rstrip(" \t") != line:
            raise ValidationError(f"{relative_path}:{line_number} has trailing whitespace")


def main() -> int:
    errors: list[str] = []
    discovered_skills: set[str] = set()

    result_files: set[str] = set()
    try:
        actual, result_files = split_result_files(inventory_validation_tree())
        if actual != EXPECTED_VALIDATION:
            errors.append(
                "validation inventory mismatch: "
                f"missing={sorted(EXPECTED_VALIDATION - actual)}, "
                f"unexpected={sorted(actual - EXPECTED_VALIDATION)}"
            )
    except ValidationError as error:
        errors.append(str(error))

    expected_all = EXPECTED_VALIDATION | EXPECTED_SUPPORT | result_files
    try:
        tracked = git_entries(sorted(expected_all))
        if set(tracked) != expected_all:
            errors.append(
                "tracked inventory mismatch: "
                f"missing={sorted(expected_all - set(tracked))}, "
                f"unexpected={sorted(set(tracked) - expected_all)}"
            )
        for path, mode in sorted(tracked.items()):
            if mode not in {"100644", "100755"}:
                errors.append(f"tracked source has unsafe Git mode {mode}: {path}")
    except ValidationError as error:
        errors.append(str(error))

    skill_root = ROOT / ".claude" / "skills"
    try:
        for directory in skill_root.iterdir():
            if directory.is_dir() and not is_reparse_point(directory):
                if (directory / "SKILL.md").is_file():
                    discovered_skills.add(directory.name)
    except (OSError, ValidationError) as error:
        errors.append(f"cannot inventory target skills: {error}")

    read_sources: dict[str, str] = {}
    for rel in sorted(expected_all):
        path = ROOT / PurePosixPath(rel)
        try:
            check_expected_path(path)
            check_ignored(rel)
            text = read_utf8(path)
            check_text(rel, text)
            read_sources[rel] = text
        except (OSError, ValidationError) as error:
            errors.append(f"{rel}: {error}")

    covered_skills: set[str] = set()
    for name in sorted(EXPECTED_CASE_NAMES):
        rel = f"validation/cases/{name}"
        text = read_sources.get(rel)
        if text is None:
            continue
        try:
            metadata, body = parse_front_matter(text, name)
            skills = metadata["target_skills"]
            assert isinstance(skills, list)
            missing_skills = sorted(set(skills) - discovered_skills)
            if missing_skills:
                raise ValidationError(f"unknown target skills: {missing_skills}")
            covered_skills.update(skills)

            heading_positions: list[int] = []
            for heading in REQUIRED_SECTIONS:
                matches = list(re.finditer(rf"(?m)^{re.escape(heading)}$", body))
                if len(matches) != 1:
                    raise ValidationError(f"section must appear exactly once: {heading}")
                heading_positions.append(matches[0].start())
            if heading_positions != sorted(heading_positions):
                raise ValidationError("required sections are out of order")
            if len(re.findall(r"(?m)^# (?!#)", body)) != 1:
                raise ValidationError("card must contain exactly one level-one title")
            if "Synthetic" not in body:
                raise ValidationError("card must use an explicit Synthetic placeholder")

            check_sensitive_content(body)
        except (AssertionError, OSError, ValidationError) as error:
            errors.append(f"{rel}: {error}")

    if covered_skills != discovered_skills:
        errors.append(
            "card coverage does not exactly match skill inventory: "
            f"missing={sorted(discovered_skills - covered_skills)}, "
            f"unknown={sorted(covered_skills - discovered_skills)}"
        )

    schema_text = read_sources.get("validation/results.schema.json")
    if schema_text is not None:
        try:
            check_results_schema(schema_text)
        except ValidationError as error:
            errors.append(f"validation/results.schema.json: {error}")
    for rel in sorted(result_files):
        text = read_sources.get(rel)
        if text is None:
            continue
        try:
            check_result_file(rel, text)
        except ValidationError as error:
            errors.append(f"{rel}: {error}")

    validation_readme = read_sources.get("validation/README.md", "")
    try:
        check_sensitive_content(validation_readme)
    except ValidationError as error:
        errors.append(f"validation/README.md: {error}")

    for command, label in (
        (["git", "diff", "--check"], "unstaged whitespace check"),
        (["git", "diff", "--cached", "--check"], "staged whitespace check"),
    ):
        try:
            git_check(command, label)
        except ValidationError as error:
            errors.append(str(error))

    for error in errors:
        print(f"ERROR: {error}")
    if errors:
        print(f"Validation failed with {len(errors)} error(s).")
        return 1
    print(
        "Validation pack checks passed: "
        f"{len(EXPECTED_CASE_NAMES)} fabricated cards, "
        f"{len(discovered_skills)} skills, {len(result_files)} recorded runs, "
        "exact tracked inventory."
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("ERROR: validation interrupted", file=sys.stderr)
        raise SystemExit(130)
    except Exception as error:  # Fail closed even for an unforeseen parser/runtime error.
        print(f"ERROR: unexpected validation failure: {type(error).__name__}: {error}")
        raise SystemExit(1)
