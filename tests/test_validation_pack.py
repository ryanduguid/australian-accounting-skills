"""Adverse tests for the fabricated validation-pack trust boundary."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY / "scripts" / "validate_validation.py"
SPEC = importlib.util.spec_from_file_location("validate_validation", SCRIPT)
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError(f"cannot load {SCRIPT}")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


def card(front_matter: str, title: str = "test-card") -> str:
    return f"---\n{front_matter}\n---\n\n# {title}\n"


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

    def test_safe_validation_link_is_normalised(self) -> None:
        self.assertEqual(
            validator.resolve_local_link(
                "validation/README.md",
                "cases/bas-g10-g11.md",
            ),
            "validation/cases/bas-g10-g11.md",
        )

    def test_remote_and_fragment_links_are_not_treated_as_files(self) -> None:
        for target in ("https://example.invalid/source", "#section"):
            with self.subTest(target=target):
                self.assertIsNone(
                    validator.resolve_local_link("validation/README.md", target)
                )

    def test_traversal_absolute_scheme_query_and_obfuscation_are_rejected(self) -> None:
        cases = (
            "../README.md",
            "%2e%2e/README.md",
            "%252e%252e/README.md",
            "cases\\bas-g10-g11.md",
            "/validation/cases/bas-g10-g11.md",
            "C:/validation/cases/bas-g10-g11.md",
            "//server/share.md",
            "javascript:alert(1)",
            "https://user:password@example.invalid/source",
            "http:../../README.md",
            "https:/../README.md",
            "https:///../README.md",
            "http:example.invalid/source",
            "http://",
            "http://../README.md",
            "https://example.invalid/%20outside",
            "https://example.invalid/%0Aoutside",
            "cases/bas-g10-g11.md?raw=1",
            "cases/unknown.md",
        )
        for target in cases:
            with self.subTest(target=target):
                with self.assertRaises(validator.ValidationError):
                    validator.resolve_local_link("validation/README.md", target)

    def test_reference_links_are_checked_and_raw_html_links_are_rejected(self) -> None:
        self.assertEqual(
            validator.markdown_targets(
                "[safe][card]\n\n[card]: cases/bas-g10-g11.md\n"
            ),
            ["cases/bas-g10-g11.md"],
        )
        self.assertEqual(
            validator.markdown_targets("[safe](<cases/bas-g10-g11.md>)"),
            ["<cases/bas-g10-g11.md>"],
        )
        target = validator.markdown_targets("[outside]: %2e%2e/README.md")[0]
        with self.assertRaises(validator.ValidationError):
            validator.resolve_local_link("validation/README.md", target)
        adverse = (
            '<a href="../README.md">outside</a>',
            '<embed src="../README.md">',
            '<script src="../outside.js"></script>',
            '<video src="../outside.mp4"></video>',
            '<link rel="stylesheet" href="../outside.css">',
            '<file:///C:/Users/Public/outside.md>',
            '<https://user:password@example.invalid/source>',
            '&lt;iframe src="../README.md"&gt;',
        )
        for content in adverse:
            with self.subTest(content=content):
                with self.assertRaisesRegex(
                    validator.ValidationError,
                    "raw HTML or autolinks",
                ):
                    validator.markdown_targets(content)

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
                self.assertIn("do not change `.gitignore`", text.lower())
                self.assertIn("authorised human", text)
                self.assertIn("assurance", text.lower())

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


if __name__ == "__main__":
    unittest.main()
