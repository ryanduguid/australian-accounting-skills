# Copyright 2026 Ryan Duguid. SPDX-License-Identifier: FSL-1.1-ALv2
"""Unit paths of the validation checker that the fixture-repository tests do not reach."""

from __future__ import annotations

import copy
import importlib.util
import io
import json
import os
import tempfile
import types
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

REPOSITORY = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY / "scripts" / "validate_validation.py"
SPEC = importlib.util.spec_from_file_location("validate_validation_helpers", SCRIPT)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"cannot load {SCRIPT}")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)

SCHEMA = json.loads((REPOSITORY / "validation" / "results.schema.json").read_text(encoding="utf-8"))


class TemporaryRoot(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)


class PathCheckTests(TemporaryRoot):
    def test_missing_paths_are_refused_without_reading(self) -> None:
        missing = self.root / "missing.md"
        with self.assertRaisesRegex(validator.ValidationError, "cannot read"):
            validator.read_utf8(missing)
        with self.assertRaisesRegex(validator.ValidationError, "cannot inspect"):
            validator.is_reparse_point(missing)
        with self.assertRaisesRegex(validator.ValidationError, "unsafe or missing expected path"):
            validator.check_expected_path(missing, self.root)

    def test_an_expected_path_must_be_a_regular_file_without_links(self) -> None:
        directory = self.root / "folder"
        directory.mkdir()
        with self.assertRaisesRegex(validator.ValidationError, "expected regular file"):
            validator.check_expected_path(directory, self.root)
        target = self.root / "real.md"
        target.write_text("x", encoding="utf-8")
        link = self.root / "link.md"
        try:
            os.symlink(target, link)
        except OSError as error:
            self.skipTest(f"file links are unavailable: {error}")
        with self.assertRaisesRegex(validator.ValidationError, "symlink or reparse point is not permitted"):
            validator.check_expected_path(link, self.root)

    def test_the_validation_tree_must_be_an_inspectable_directory_of_files(self) -> None:
        (self.root / "validation").write_text("a file, not a directory", encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "validation must be a real directory"):
            validator.inventory_validation_tree(self.root)
        (self.root / "validation").unlink()
        (self.root / "validation").mkdir()
        (self.root / "validation" / "odd").write_text("x", encoding="utf-8")
        with mock.patch.object(validator.os, "scandir", side_effect=OSError("denied")):
            with self.assertRaisesRegex(validator.ValidationError, "cannot inspect"):
                validator.inventory_validation_tree(self.root)

        class _Special:
            path = str(self.root / "validation" / "odd")

            def is_symlink(self) -> bool:
                return False

            def is_dir(self, *, follow_symlinks: bool) -> bool:
                return False

            def is_file(self, *, follow_symlinks: bool) -> bool:
                return False

        with mock.patch.object(validator.os, "scandir", return_value=[_Special()]):
            with self.assertRaisesRegex(validator.ValidationError, "non-regular entry: validation/odd"):
                validator.inventory_validation_tree(self.root)


class FrontMatterTests(unittest.TestCase):
    def test_front_matter_shape_refusals(self) -> None:
        for text, message in (
            ("no front matter\n", "front matter must be the first document block"),
            ("---\nid: [unclosed\n---\n", "front matter must be valid YAML"),
            ("---\n- id\n---\n", "front matter must be a YAML mapping"),
            ("---\nid: " + "[" * 3000 + "]" * 3000 + "\n---\n",
             "front matter is nested too deeply to read"),
            ("---\nid: card\nsynthetic: true\ntarget_skills:\n  - Not_A_Slug\n---\n",
             "every target skill must be a lowercase hyphenated slug"),
        ):
            with self.subTest(message=message):
                with self.assertRaisesRegex(validator.ValidationError, message):
                    validator.parse_front_matter(text, "card.md")


class GitInventoryTests(unittest.TestCase):
    def completed(self, returncode: int = 0, stdout: bytes = b"", stderr: bytes = b"") -> types.SimpleNamespace:
        # The checker reads only these 3 fields of the Git result.
        return types.SimpleNamespace(returncode=returncode, stdout=stdout, stderr=stderr)

    def test_git_inventory_fails_closed(self) -> None:
        with mock.patch.object(validator.subprocess, "run", side_effect=OSError("no git")):
            with self.assertRaisesRegex(validator.ValidationError, "cannot run Git inventory"):
                validator.git_entries(["a"])
        for stdout, message in (
            (b"no tab here\0", "undecodable inventory entry"),
            (b"100644 abc 0\tbad\xff\0", "undecodable inventory entry"),
            (b"100644 abc 0\ta.md\x00100644 abc 0\ta.md\x00", "duplicate Git inventory entry: a.md"),
        ):
            with self.subTest(message=message):
                with mock.patch.object(validator.subprocess, "run", return_value=self.completed(stdout=stdout)):
                    with self.assertRaisesRegex(validator.ValidationError, message):
                        validator.git_entries(["a.md"])

    def test_check_ignore_refuses_ignored_sources_and_git_failures(self) -> None:
        with mock.patch.object(validator.subprocess, "run", return_value=self.completed(0)):
            with self.assertRaisesRegex(validator.ValidationError, "ignored by .gitignore"):
                validator.check_ignored("a.md")
        with mock.patch.object(validator.subprocess, "run",
                               return_value=self.completed(128, stderr=b"fatal: broken")):
            with self.assertRaisesRegex(validator.ValidationError, "git check-ignore failed for a.md: fatal: broken"):
                validator.check_ignored("a.md")


def _schema_with(change) -> str:
    schema = copy.deepcopy(SCHEMA)
    change(schema)
    return json.dumps(schema)


class ResultsSchemaTests(unittest.TestCase):
    def check(self, text: str) -> None:
        validator.check_results_schema(text, frozenset(SCHEMA["properties"]["results"]["propertyNames"]["enum"]))

    def test_the_recorded_schema_passes(self) -> None:
        self.check(json.dumps(SCHEMA))

    def test_a_schema_that_is_not_an_object_is_refused(self) -> None:
        with self.assertRaisesRegex(validator.ValidationError, "does not declare the case and verdict enums"):
            self.check("[]")

    def test_every_version_2_contract_change_is_refused(self) -> None:
        def provenance(schema):
            return schema["properties"]["provenance"]

        def evidence(schema):
            return provenance(schema)["additionalProperties"]

        def rules(schema):
            return schema["allOf"][0]

        changes = {
            "extra property": lambda s: s["properties"].update(extra={}),
            "schema_version": lambda s: s["properties"].update(schema_version={"const": 3, "type": "integer"}),
            "status enum": lambda s: s["properties"]["status"].update(enum=["confirmed"]),
            "input mode enum": lambda s: s["properties"]["input_mode"].update(enum=["other"]),
            "open root": lambda s: s.update(additionalProperties=True),
            "required": lambda s: s.update(required=[]),
            "open evidence": lambda s: evidence(s).update(additionalProperties=True),
            "empty provenance": lambda s: provenance(s).update(minProperties=0),
            "provenance names": lambda s: provenance(s).update(propertyNames={}),
            "evidence required": lambda s: evidence(s).update(required=[]),
            "evidence properties": lambda s: evidence(s)["properties"].update(extra={}),
            "if rule": lambda s: rules(s).update({"if": {}}),
            "then required": lambda s: rules(s)["then"].update(required=[]),
            "output rule": lambda s: rules(s)["then"]["allOf"][1].update({"if": {}}),
            "else rule": lambda s: rules(s).update({"else": {}}),
        }
        for name, change in changes.items():
            with self.subTest(change=name):
                with self.assertRaisesRegex(validator.ValidationError, "provenance contract has changed"):
                    self.check(_schema_with(change))


class PublishedInventoryTests(TemporaryRoot):
    def test_a_marketplace_that_is_not_an_object_is_refused(self) -> None:
        marketplace = self.root / validator.MARKETPLACE
        marketplace.parent.mkdir(parents=True)
        marketplace.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(validator.ValidationError, "does not declare one plugin and its skill list"):
            validator.check_published_inventories(set(), self.root)


class RunTests(unittest.TestCase):
    def test_run_returns_main_status_and_fails_closed(self) -> None:
        with mock.patch.object(validator, "main", return_value=0):
            self.assertEqual(validator.run(), 0)
        stderr = io.StringIO()
        with mock.patch.object(validator, "main", side_effect=KeyboardInterrupt), redirect_stderr(stderr):
            self.assertEqual(validator.run(), 130)
        self.assertEqual(stderr.getvalue(), "ERROR: validation interrupted\n")
        stdout = io.StringIO()
        with mock.patch.object(validator, "main", side_effect=RuntimeError("boom")), redirect_stdout(stdout):
            self.assertEqual(validator.run(), 1)
        self.assertEqual(stdout.getvalue(), "ERROR: unexpected validation failure: RuntimeError: boom\n")


if __name__ == "__main__":
    unittest.main()
