"""Adverse tests for the fabricated validation-pack trust boundary."""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

REPOSITORY = Path(__file__).resolve().parents[1]
# The not-advice sentence has to travel with a single copied skill folder, so a
# link back to the repository root does not count as one.
INLINE_NOT_ADVICE = re.compile(r"not (?:tax|legal)[^.\n]*advice", re.IGNORECASE)
# Ignore coverage is not a safeguard for client output. The entry is a
# convention the next commit can waive, and it does nothing about the copy
# already sitting in the working tree. These are the shapes that offer it as
# one, as distinct from the many legitimate "do not change `.gitignore`" lines.
IGNORE_AS_SAFEGUARD = re.compile(
    r"`?\.gitignore`?\s+(?:blocks|covers|excludes|catches)"
    r"|(?:already )?(?:excluded from|ignored by) version control"
    r"|confirm[^.\n]*(?:is|are) ignored",
    re.IGNORECASE,
)
CHECKOUT_ADJACENT = "beside a checkout"
OUTSIDE_EVERY_CHECKOUT = "outside every version-control checkout"
# "Keep it out of version control" is the shorthand an ignore entry appears to
# satisfy, so it reopens the hole the phrase above closes. Every skill states
# the location policy twice, once in its steps and once in the Client data
# boundary, and the boundary is the copy that travels when the folder is
# installed on its own.
# Every inflection, because the passive "output kept out of version control" is
# the form the consolidation record itself uses for the wording this replaces,
# and a boundary rewritten that way would otherwise pass.
OUT_OF_VERSION_CONTROL = re.compile(
    r"\bkeep(?:s|ing)?\b[^.\n]*\bout of version control\b"
    r"|\bkept\b[^.\n]*\bout of version control\b",
    re.IGNORECASE,
)
SCRIPT = REPOSITORY / "scripts" / "validate_validation.py"
SPEC = importlib.util.spec_from_file_location("validate_validation", SCRIPT)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError(f"cannot load {SCRIPT}")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def card(front_matter: str, title: str = "test-card") -> str:
    return f"---\n{front_matter}\n---\n\n# {title}\n"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    return result.stdout.strip()


def build_fixture(root: Path, cards: int = 6) -> None:
    """A small repository the validator accepts, built from real cards.

    Everything else is generated to match those cards, so the fixture stays
    correct when the pack grows and a mutated copy isolates one rejection.
    """
    chosen = sorted((REPOSITORY / "validation" / "cases").glob("*.md"))[:cards]
    skills: set[str] = set()
    for source in chosen:
        text = validator.read_utf8(source)
        metadata, _ = validator.parse_front_matter(text, source.name)
        targets = metadata["target_skills"]
        assert isinstance(targets, list)
        skills.update(str(skill) for skill in targets)
        write(root / "validation" / "cases" / source.name, text)
    for name in sorted(skills):
        write(root / ".claude" / "skills" / name / "SKILL.md", f"# {name}\n")

    identifiers = sorted(path.stem for path in chosen)
    write(root / "validation" / "README.md", "# Fixture validation pack\n")
    write(
        root / "validation" / "results.schema.json",
        json.dumps(
            {
                "properties": {
                    "results": {
                        "propertyNames": {"enum": identifiers},
                        "additionalProperties": {
                            "enum": list(validator.RESULT_VERDICTS)
                        },
                    }
                }
            },
            indent=2,
        )
        + "\n",
    )
    write(
        root / "validation" / "results" / "2026-01-31-fixture.json",
        json.dumps(
            {
                "model": "fixture-model",
                "run_date": "2026-01-31",
                "skills_version": "fixture",
                "runner": "A Person",
                "results": {identifiers[0]: "pass"},
            },
            indent=2,
        )
        + "\n",
    )
    for relative_path in sorted(validator.EXPECTED_SUPPORT):
        write(root / relative_path, "fixture support file\n")
    write(
        root / validator.MARKETPLACE,
        json.dumps(
            {"plugins": [{"skills": [f"./.claude/skills/{n}" for n in sorted(skills)]}]},
            indent=2,
        )
        + "\n",
    )
    write(
        root / validator.CATALOGUE,
        "# Fixture skills\n\n| Skill | Use it for |\n| --- | --- |\n"
        + "".join(f"| `{name}` | Fixture |\n" for name in sorted(skills)),
    )
    git(root, "init", "-q")
    git(root, "add", "-A")


class FrontMatterTests(unittest.TestCase):
    def test_accepts_exact_schema(self) -> None:
        text = card(
            "id: test-card\n"
            "synthetic: true\n"
            "target_skills:\n"
            "  - bas-preparation"
        )
        metadata, body = validator.parse_front_matter(text, "test-card.md")
        self.assertEqual(
            metadata,
            {
                "id": "test-card",
                "synthetic": True,
                "target_skills": ["bas-preparation"],
            },
        )
        self.assertIn("# test-card", body)

    def test_rejects_duplicate_unknown_missing_and_wrong_typed_fields(self) -> None:
        cases = {
            "duplicate": (
                "id: test-card\nid: second\nsynthetic: true\n"
                "target_skills:\n  - bas-preparation",
                "duplicate YAML field",
            ),
            "unknown": (
                "id: test-card\nsynthetic: true\ntools: shell\n"
                "target_skills:\n  - bas-preparation",
                "fields must be exact",
            ),
            "missing": (
                "id: test-card\nsynthetic: true",
                "fields must be exact",
            ),
            "string-bool": (
                "id: test-card\nsynthetic: 'true'\n"
                "target_skills:\n  - bas-preparation",
                "literal boolean true",
            ),
            "yaml-bool-alias": (
                "id: test-card\nsynthetic: yes\n"
                "target_skills:\n  - bas-preparation",
                "literal boolean true",
            ),
            "mapping-skills": (
                "id: test-card\nsynthetic: true\n"
                "target_skills:\n  bas-preparation: true",
                "non-empty YAML list",
            ),
            "duplicate-skill": (
                "id: test-card\nsynthetic: true\n"
                "target_skills:\n  - bas-preparation\n  - bas-preparation",
                "contains a duplicate",
            ),
        }
        for label, (front_matter, error) in cases.items():
            with self.subTest(case=label):
                with self.assertRaisesRegex(validator.ValidationError, error):
                    validator.parse_front_matter(card(front_matter), "test-card.md")

    def test_rejects_yaml_alias_anchor_and_tag(self) -> None:
        cases = {
            "anchor": (
                "id: &card test-card\nsynthetic: true\n"
                "target_skills:\n  - bas-preparation"
            ),
            "alias": (
                "id: test-card\nsynthetic: true\n"
                "target_skills: &skills\n  - bas-preparation\ncopy: *skills"
            ),
            "tag": (
                "id: !!str test-card\nsynthetic: true\n"
                "target_skills:\n  - bas-preparation"
            ),
        }
        for label, front_matter in cases.items():
            with self.subTest(case=label):
                with self.assertRaisesRegex(
                    validator.ValidationError,
                    "aliases, anchors and tags",
                ):
                    validator.parse_front_matter(card(front_matter), "test-card.md")

    def test_rejects_filename_mismatch_and_non_slug(self) -> None:
        base = "synthetic: true\ntarget_skills:\n  - bas-preparation"
        with self.assertRaisesRegex(validator.ValidationError, "match filename"):
            validator.parse_front_matter(card(f"id: other\n{base}"), "test-card.md")
        with self.assertRaisesRegex(validator.ValidationError, "hyphenated slug"):
            validator.parse_front_matter(card(f"id: Test_Card\n{base}"), "test-card.md")


class DecodeAndPathTests(unittest.TestCase):
    def test_invalid_utf8_and_nul_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.md"
            path.write_bytes(b"\xff\xfe")
            with self.assertRaisesRegex(validator.ValidationError, "strict UTF-8"):
                validator.read_utf8(path)
            path.write_bytes(b"valid\x00payload")
            with self.assertRaisesRegex(validator.ValidationError, "NUL"):
                validator.read_utf8(path)

    def test_unicode_control_and_format_characters_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.md"
            for content in ("hidden\u200btext", "reordered\u202etext", "control\x1ftext"):
                with self.subTest(content=ascii(content)):
                    path.write_text(content, encoding="utf-8")
                    with self.assertRaisesRegex(
                        validator.ValidationError,
                        "Unicode control/format character",
                    ):
                        validator.read_utf8(path)

    def test_crlf_is_normalised_and_bare_carriage_return_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "fixture.md"
            path.write_bytes(b"line one\r\nline two\r\n")
            self.assertEqual(validator.read_utf8(path), "line one\nline two\n")
            path.write_bytes(b"line one\rline two")
            with self.assertRaisesRegex(validator.ValidationError, "bare carriage"):
                validator.read_utf8(path)

    def test_validation_inventory_does_not_read_unexpected_content(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = root / "validation" / "cases"
            cases.mkdir(parents=True)
            unreadable = cases / "unexpected.bin"
            unreadable.write_bytes(b"\xff\xfe\x00")
            self.assertEqual(
                validator.inventory_validation_tree(root),
                {"validation/cases/unexpected.bin"},
            )

    def test_validation_inventory_rejects_symlink_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            validation = root / "validation"
            validation.mkdir()
            target = root / "target.md"
            target.write_text("synthetic", encoding="utf-8")
            link = validation / "link.md"
            try:
                link.symlink_to(target)
            except OSError:
                self.skipTest("symlink creation is unavailable in this environment")
            with self.assertRaisesRegex(validator.ValidationError, "symlink/reparse"):
                validator.inventory_validation_tree(root)


class SafetyControlTests(unittest.TestCase):
    def test_every_skill_keeps_output_and_human_action_boundary(self) -> None:
        skill_files = sorted((REPOSITORY / ".claude" / "skills").glob("*/SKILL.md"))
        for path in skill_files:
            with self.subTest(skill=path.parent.name):
                text = path.read_text(encoding="utf-8")
                lower = text.lower()
                self.assertTrue(
                    "do not change `.gitignore`" in lower
                    or "do not edit `.gitignore`" in lower
                )
                self.assertIn("authorised human", text)
                self.assertTrue(
                    "assurance" in lower
                    or "legal, tax and accounting judgement belongs to the authorised reviewer"
                    in lower
                )
                self.assertTrue(
                    INLINE_NOT_ADVICE.search(text) is not None
                    or "## Portable safety boundary" in text,
                    "the not-advice boundary must survive copying this folder out "
                    "of the repository, so a DISCLAIMER.md link alone is not enough",
                )

    def test_no_instruction_offers_ignore_coverage_as_the_output_safeguard(self) -> None:
        instructions = sorted(
            (REPOSITORY / ".claude" / "skills").glob("*/SKILL.md")
        ) + [REPOSITORY / ".claude" / "rules" / "accounting-safety.md"]
        for path in instructions:
            with self.subTest(instructions=path.parent.name):
                match = IGNORE_AS_SAFEGUARD.search(path.read_text(encoding="utf-8"))
                if match is not None:
                    self.fail(
                        f"{path.relative_to(REPOSITORY)} offers ignore coverage as "
                        f"the safeguard for client output ({match.group(0)!r}). An "
                        "ignore entry is a convention the next commit can waive, "
                        "and it does nothing about the copy already sitting in the "
                        "working tree, so require a path outside every "
                        "version-control checkout instead."
                    )

    def test_no_instruction_keeps_client_output_merely_out_of_version_control(
        self,
    ) -> None:
        instructions = sorted(
            (REPOSITORY / ".claude" / "skills").glob("*/SKILL.md")
        ) + [REPOSITORY / ".claude" / "rules" / "accounting-safety.md"]
        for path in instructions:
            with self.subTest(instructions=path.parent.name):
                match = OUT_OF_VERSION_CONTROL.search(
                    " ".join(path.read_text(encoding="utf-8").split())
                )
                if match is not None:
                    self.fail(
                        f"{path.relative_to(REPOSITORY)} asks only that client "
                        f"output be kept out of version control ({match.group(0)!r}). "
                        "An ignored path inside a checkout reads as satisfying "
                        "that, and Monthly Close Controls refuses such a path "
                        "outright, so require one outside every version-control "
                        "checkout instead."
                    )

    def test_a_path_beside_a_checkout_must_be_outside_every_checkout(self) -> None:
        # The shared rule carries the same phrase and is where the requirement
        # is defined, so scanning only the skills would let the canonical text
        # lose it while every copy still passed. Both phrases are matched on
        # whitespace-collapsed text, because the rule wraps the requirement
        # across 2 lines and a line break must not hide a sentence that is
        # there.
        instructions = sorted(
            (REPOSITORY / ".claude" / "skills").glob("*/SKILL.md")
        ) + [REPOSITORY / ".claude" / "rules" / "accounting-safety.md"]
        unwrapped = {
            path: " ".join(path.read_text(encoding="utf-8").split())
            for path in instructions
        }
        candidates = [
            path for path, text in unwrapped.items() if CHECKOUT_ADJACENT in text
        ]
        self.assertTrue(
            candidates,
            "no instruction discusses a client-output path beside a checkout",
        )
        for path in candidates:
            with self.subTest(instructions=path.parent.name):
                self.assertIn(OUTSIDE_EVERY_CHECKOUT, unwrapped[path])

    def test_shared_rule_keeps_consequential_actions_human_only(self) -> None:
        text = (
            REPOSITORY / ".claude" / "rules" / "accounting-safety.md"
        ).read_text(encoding="utf-8")
        for boundary in (
            "Do not lodge",
            "make declarations",
            "communicate with a regulator or client",
            "execute a payment",
            "post a journal",
            "lock financial records",
            "authorised human action",
        ):
            with self.subTest(boundary=boundary):
                self.assertIn(boundary, text)

    def test_export_manifest_and_cash_roll_forward_cannot_silently_regress(self) -> None:
        exports = (
            REPOSITORY / ".claude" / "skills" / "xero-exports" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("## Export manifest", exports)
        self.assertIn("generated timestamp", exports)
        self.assertIn("tracking/entity filters", exports)

        cashflow = (
            REPOSITORY
            / ".claude"
            / "skills"
            / "cashflow-forecast-13week"
            / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("closing cash = opening cash + receipts − payments", cashflow)
        self.assertIn("next week's opening cash must equal the prior closing cash", cashflow)

    def test_liability_roll_forwards_and_post_journal_gate_cannot_regress(self) -> None:
        fbt = (
            REPOSITORY / ".claude" / "skills" / "fbt-annual-workflow" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn(
            "opening payable + calculated liability and supported adjustments",
            fbt,
        )
        self.assertIn("tax-account evidence", fbt)

        stp = (
            REPOSITORY / ".claude" / "skills" / "stp-finalisation" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("opening PAYG/SG payable + current-year payroll liability", stp)
        self.assertIn("Do not compare annual PAYG withheld or SG expense", stp)

        close = (
            REPOSITORY / ".claude" / "skills" / "month-end-close" / "SKILL.md"
        ).read_text(encoding="utf-8")
        self.assertIn("Source manifest: report/version", close)
        self.assertIn("re-export affected trial balances", close)
        self.assertIn("period-lock action is recorded as pending or complete", close)

    def test_sensitive_and_dated_rule_heuristics_cover_adverse_examples(self) -> None:
        adverse = {
            "email address": "Contact worker@example.test",
            "labelled Australian identifier": "ABN: 12345678901",
            "unlabelled long numeric identifier": "12345678901",
            "BSB or bank account": "BSB 123-456",
            "private key": "-----BEGIN PRIVATE KEY-----",
            "bearer credential": "Bearer abcdefghijklmnop",
            "realistic entity suffix": "Example Trading Pty Ltd",
        }
        for label, content in adverse.items():
            with self.subTest(label=label):
                scan_text = validator.normalise_for_sensitive_scan(content)
                self.assertIsNotNone(
                    validator.SENSITIVE_PATTERNS[label].search(scan_text)
                )
        self.assertIsNotNone(
            validator.DATED_RULE.search(
                validator.normalise_for_sensitive_scan("effective 1 July 2026")
            )
        )

    def test_sensitive_scan_exposes_rendered_markdown_and_entity_obfuscation(self) -> None:
        adverse = {
            "labelled Australian identifier": (
                "A**B**N: 12 345 678 901",
                "T`F`N 123 456 789",
                "A[B](#fragment)N 12 345 678 901",
                "A\u200bBN: 12 345 678 901",
            ),
            "unlabelled long numeric identifier": ("12 345 678 901",),
            "email address": ("worker&#64;example.test",),
            "BSB or bank account": ("B<!-- -->SB 123-456",),
            "realistic entity suffix": ("Acme Pty **Ltd**",),
            "API credential": ("sk_abcdef**ghijkl**mnop",),
        }
        for label, contents in adverse.items():
            for content in contents:
                with self.subTest(label=label, content=content):
                    scan_text = validator.normalise_for_sensitive_scan(content)
                    self.assertIsNotNone(
                        validator.SENSITIVE_PATTERNS[label].search(scan_text)
                    )
                    with self.assertRaisesRegex(
                        validator.ValidationError,
                        f"possible {label}",
                    ):
                        validator.check_sensitive_content(content)

        self.assertIsNotNone(
            validator.DATED_RULE.search(
                validator.normalise_for_sensitive_scan(
                    "effective 1 **July** 2026"
                )
            )
        )
        with self.assertRaisesRegex(validator.ValidationError, "dated/rate rule"):
            validator.check_sensitive_content("effective 1 **July** 2026")


class PublishedInventoryTests(unittest.TestCase):
    """Every published skill list is checked against the directory itself."""

    def skills(self) -> set[str]:
        return {
            path.parent.name
            for path in (REPOSITORY / ".claude" / "skills").glob("*/SKILL.md")
        }

    def elsewhere(self, marketplace: str, catalogue: str) -> Path:
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, directory, True)
        for relative_path, text in (
            (validator.MARKETPLACE, marketplace),
            (validator.CATALOGUE, catalogue),
        ):
            path = directory / relative_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8", newline="\n")
        return directory

    def published(self) -> tuple[str, str]:
        return (
            validator.read_utf8(REPOSITORY / validator.MARKETPLACE),
            validator.read_utf8(REPOSITORY / validator.CATALOGUE),
        )

    def test_accepts_the_committed_inventories(self) -> None:
        validator.check_published_inventories(self.skills())

    def test_card_and_skill_sets_come_from_the_directories(self) -> None:
        cases = REPOSITORY / "validation" / "cases"
        self.assertEqual(
            validator.EXPECTED_CASE_NAMES,
            {path.name for path in cases.iterdir()},
        )
        self.assertEqual(
            validator.CASE_IDS,
            frozenset(path.stem for path in cases.glob("*.md")),
        )

    def test_rejects_a_marketplace_that_drifts_from_the_directory(self) -> None:
        with self.assertRaisesRegex(
            validator.ValidationError,
            f"{re.escape(validator.MARKETPLACE)} does not match the skill directory",
        ):
            validator.check_published_inventories(self.skills() | {"made-up-skill"})

    def test_rejects_a_catalogue_that_drifts_from_the_directory(self) -> None:
        marketplace, catalogue = self.published()
        dropped = "\n".join(
            line
            for line in catalogue.splitlines()
            if not line.startswith("| `bas-preparation`")
        )
        root = self.elsewhere(marketplace, dropped)
        with self.assertRaisesRegex(
            validator.ValidationError,
            f"{re.escape(validator.CATALOGUE)} does not match the skill directory",
        ):
            validator.check_published_inventories(self.skills(), root)

    def test_rejects_a_repeated_entry_and_a_malformed_marketplace(self) -> None:
        marketplace, catalogue = self.published()
        repeated = marketplace.replace(
            '"./.claude/skills/bas-preparation",',
            '"./.claude/skills/bas-preparation",\n        "./other/bas-preparation",',
        )
        with self.assertRaisesRegex(validator.ValidationError, "names a skill twice"):
            validator.check_published_inventories(
                self.skills(), self.elsewhere(repeated, catalogue)
            )
        for label, broken in (
            ("no plugin", '{"plugins": []}\n'),
            ("plugins is a mapping", '{"plugins": {"name": "one"}}\n'),
            ("skills is a string", '{"plugins": [{"skills": "all of them"}]}\n'),
            ("no skills key", marketplace.replace('"skills": [', '"other": [')),
        ):
            with self.subTest(label):
                with self.assertRaisesRegex(
                    validator.ValidationError, "does not declare one plugin"
                ):
                    validator.check_published_inventories(
                        self.skills(), self.elsewhere(broken, catalogue)
                    )


class RecordedRunTests(unittest.TestCase):
    """A recorded run is a pass or fail per card and nothing else."""

    GOOD = (
        '{"model": "example-model", "run_date": "2026-01-31", "skills_version": "v0.2.0", '
        '"runner": "A Person", "results": {"bas-g10-g11": "pass"}}'
    )
    NAME = "validation/results/2026-01-31-example-model.json"

    def test_accepts_a_minimal_run(self) -> None:
        validator.check_result_file(self.NAME, self.GOOD)

    def test_rejects_shape_drift(self) -> None:
        for label, name, text in (
            ("transcript key", self.NAME, self.GOOD.replace('"runner"', '"transcript": "x", "runner"')),
            ("unknown case", self.NAME, self.GOOD.replace("bas-g10-g11", "made-up")),
            ("bad verdict", self.NAME, self.GOOD.replace('"pass"', '"PASS"')),
            ("duplicate case", self.NAME, self.GOOD.replace(
                '"bas-g10-g11": "pass"', '"bas-g10-g11": "pass", "bas-g10-g11": "fail"')),
            ("date mismatch", "validation/results/2026-02-01-example-model.json", self.GOOD),
            ("bad name", "validation/results/notes.json", self.GOOD),
            ("duplicate key", self.NAME, self.GOOD.replace('"runner"', '"model": "x", "runner"')),
            ("empty model", self.NAME, self.GOOD.replace('"example-model"', '" "')),
            ("no results", self.NAME, self.GOOD.replace('{"bas-g10-g11": "pass"}', "{}")),
            ("list of entries", self.NAME, self.GOOD.replace(
                '{"bas-g10-g11": "pass"}', '[{"case": "bas-g10-g11", "verdict": "pass"}]')),
            ("note as verdict", self.NAME, self.GOOD.replace(
                '"pass"', '{"verdict": "pass", "note": "why"}')),
            ("impossible date", "validation/results/2026-99-99-example-model.json",
             self.GOOD.replace("2026-01-31", "2026-99-99")),
            ("multi-line runner", self.NAME, self.GOOD.replace('"A Person"', '"Model output:\\nx"')),
            ("long runner", self.NAME, self.GOOD.replace('"A Person"', '"' + "x" * 121 + '"')),
            ("identifier in runner", self.NAME, self.GOOD.replace('"A Person"', '"123456789"')),
        ):
            with self.subTest(label), self.assertRaises(validator.ValidationError):
                validator.check_result_file(name, text)

    def test_rejection_reasons_are_the_documented_ones(self) -> None:
        with self.assertRaisesRegex(validator.ValidationError, "match the file name"):
            validator.check_result_file(
                "validation/results/2026-02-01-example-model.json", self.GOOD)
        with self.assertRaisesRegex(validator.ValidationError, "transcripts do not belong"):
            validator.check_result_file(
                self.NAME, self.GOOD.replace('"runner"', '"transcript": "x", "runner"'))
        with self.assertRaisesRegex(validator.ValidationError, "one line of at most"):
            validator.check_result_file(
                self.NAME, self.GOOD.replace('"A Person"', '"' + "x" * 121 + '"'))

    def test_schema_enum_must_match_the_card_inventory(self) -> None:
        schema = validator.read_utf8(REPOSITORY / "validation" / "results.schema.json")
        validator.check_results_schema(schema)
        with self.assertRaisesRegex(validator.ValidationError, "missing="):
            validator.check_results_schema(schema.replace('"bas-g10-g11",\n', ""))
        with self.assertRaisesRegex(validator.ValidationError, "unknown=\\['made-up'\\]"):
            validator.check_results_schema(schema.replace('"bas-g10-g11",\n', '"bas-g10-g11",\n"made-up",\n'))
        with self.assertRaisesRegex(validator.ValidationError, "does not declare"):
            validator.check_results_schema(schema.replace('"bas-g10-g11",\n', '5,\n'))
        with self.assertRaisesRegex(validator.ValidationError, "verdict enum"):
            validator.check_results_schema(schema.replace('"pass",', '"PASS",'))

    def test_inventory_splits_runs_from_the_fixed_set(self) -> None:
        fixed, runs = validator.split_result_files({
            "validation/README.md",
            "validation/results/2026-01-31-example-model.json",
            "validation/results/notes.json",
        })
        self.assertEqual(runs, {"validation/results/2026-01-31-example-model.json"})
        self.assertEqual(fixed, {"validation/README.md", "validation/results/notes.json"})


class FullRunTests(unittest.TestCase):
    """Every refusal `main` can reach, exercised against a mutated repository.

    The whole run is the fail-closed behaviour: one drifted inventory, one
    unreadable source or one unsafe Git mode has to stop the check, and the
    message has to name what failed. `main` collects every error before it
    returns, so one mutated copy can carry several independent defects.
    """

    fixture: Path
    _directory: tempfile.TemporaryDirectory[str]

    @classmethod
    def setUpClass(cls) -> None:
        # Git leaves read-only objects behind, which Windows refuses to remove.
        cls._directory = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        cls.fixture = Path(cls._directory.name) / "fixture"
        build_fixture(cls.fixture)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._directory.cleanup()

    def copy(self) -> Path:
        directory = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, directory, True)
        root = directory / "repository"
        shutil.copytree(self.fixture, root)
        return root

    def run_main(self, root: Path) -> tuple[int, str]:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            status = validator.main(root)
        return status, output.getvalue()

    def cards(self, root: Path) -> list[Path]:
        return sorted((root / "validation" / "cases").glob("*.md"))

    def assert_refused(self, root: Path, *expected: str) -> None:
        status, output = self.run_main(root)
        self.assertEqual(status, 1, output)
        for message in expected:
            with self.subTest(message=message):
                self.assertIn(message, output)

    def test_accepts_the_generated_fixture(self) -> None:
        status, output = self.run_main(self.copy())
        self.assertEqual(status, 0, output)
        self.assertIn("Validation pack checks passed", output)

    def test_extra_skill_directory_entries_are_not_skills(self) -> None:
        """A loose file or a folder without SKILL.md is skipped, not installed."""
        root = self.copy()
        write(root / ".claude" / "skills" / "notes.md", "not a skill\n")
        (root / ".claude" / "skills" / "drafts").mkdir()
        status, output = self.run_main(root)
        self.assertEqual(status, 0, output)

    def test_inventory_tracking_and_git_failures_are_refused(self) -> None:
        root = self.copy()
        first, second = self.cards(root)[0], self.cards(root)[1]
        write(root / "validation" / "stray.json", "{}\n")
        git(root, "rm", "--quiet", "--cached", f"validation/cases/{second.name}")
        blob = git(root, "rev-parse", ":CLAUDE.md")
        git(root, "update-index", "--add", "--cacheinfo", f"120000,{blob},CLAUDE.md")
        schema = root / "validation" / "results.schema.json"
        write(schema, validator.read_utf8(schema).replace(f'"{first.stem}"', '"made-up"'))
        run = root / "validation" / "results" / "2026-01-31-fixture.json"
        write(run, validator.read_utf8(run).replace("2026-01-31", "2026-02-01"))
        skill = sorted((root / ".claude" / "skills").glob("*/SKILL.md"))[0]
        write(skill, validator.read_utf8(skill) + "trailing   \n")
        self.assert_refused(
            root,
            "validation inventory mismatch",
            "tracked inventory mismatch",
            "tracked source has unsafe Git mode 120000",
            "results schema case enum does not match the card inventory",
            "run_date must match the file name",
        )

    def targets(self, path: Path) -> set[str]:
        metadata, _ = validator.parse_front_matter(validator.read_utf8(path), path.name)
        skills = metadata["target_skills"]
        assert isinstance(skills, list)
        return {str(skill) for skill in skills}

    def test_card_content_failures_are_refused(self) -> None:
        root = self.copy()
        cards = self.cards(root)
        # Front matter is rejected before the card can claim coverage, so
        # orphaning a skill means breaking every card that names it.
        orphaned = self.targets(cards[0])
        rejected = [path for path in cards if self.targets(path) & orphaned]
        intact = [path for path in cards if path not in rejected]
        self.assertGreaterEqual(len(intact), 3, "the fixture needs three usable cards")
        for path in rejected:
            write(
                path,
                validator.read_utf8(path).replace(
                    "target_skills:", "target_skills:\n  - no-such-skill", 1
                ),
            )
        second, third, fourth = intact[:3]
        write(second, validator.read_utf8(second) + "\n## Task\n")
        reordered = validator.read_utf8(third)
        reordered = reordered.replace("## Scenario", "## Placeholder", 1)
        reordered = reordered.replace("## Task", "## Scenario", 1)
        write(third, reordered.replace("## Placeholder", "## Task", 1))
        write(fourth, validator.read_utf8(fourth) + "\n# Second title\n")
        self.assert_refused(
            root,
            "unknown target skills: ['no-such-skill']",
            "section must appear exactly once: ## Task",
            "required sections are out of order",
            "card must contain exactly one level-one title",
            "card coverage does not exactly match skill inventory",
        )

    def test_unreadable_and_unsafe_sources_are_refused(self) -> None:
        """An undecodable source is skipped by every later check, not trusted."""
        root = self.copy()
        for relative_path in (
            f"validation/cases/{self.cards(root)[0].name}",
            "validation/results.schema.json",
            "validation/results/2026-01-31-fixture.json",
        ):
            (root / relative_path).write_bytes(b"\xff\xfe not utf-8\n")
        readme = root / "validation" / "README.md"
        write(readme, validator.read_utf8(readme) + "\nExample Trading Pty Ltd\n")
        support = root / "CLAUDE.md"
        write(support, validator.read_utf8(support) + "trailing   \n")
        self.assert_refused(
            root,
            "is not strict UTF-8",
            "validation/README.md: possible realistic entity suffix",
            "CLAUDE.md:2 has trailing whitespace",
        )

    def test_an_unreadable_git_index_is_refused(self) -> None:
        """No Git inventory means no proof the sources are the tracked ones."""
        root = self.copy()
        (root / ".git" / "index").write_bytes(b"not an index")
        self.assert_refused(
            root,
            "Git inventory failed",
        )

    def test_a_missing_card_directory_is_refused(self) -> None:
        root = self.copy()
        shutil.rmtree(root / "validation" / "cases")
        self.assert_refused(root, "cannot inventory validation cases")

    def test_a_missing_skill_directory_is_refused(self) -> None:
        root = self.copy()
        shutil.rmtree(root / ".claude" / "skills")
        self.assert_refused(
            root,
            "cannot inventory target skills",
            f"{validator.MARKETPLACE} does not match the skill directory",
        )


if __name__ == "__main__":
    unittest.main()
