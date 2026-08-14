from __future__ import annotations

import hashlib
import os
from pathlib import Path
import sys
import tarfile
from tempfile import TemporaryDirectory
import unittest
from unittest import mock
import zipfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_release_archives as release_archives  # noqa: E402


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _zip_files(path: Path) -> dict[str, bytes]:
    with zipfile.ZipFile(path) as archive:
        return {
            item.filename: archive.read(item.filename)
            for item in archive.infolist()
            if not item.is_dir()
        }


def _tar_files(path: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    with tarfile.open(path, "r:gz") as archive:
        for item in archive.getmembers():
            if item.isfile():
                stream = archive.extractfile(item)
                if stream is None:
                    raise AssertionError(f"could not read {item.name}")
                files[item.name] = stream.read()
    return files


class ReleaseArchiveTests(unittest.TestCase):
    def test_builder_pins_git_conversion_and_timezone(self) -> None:
        with TemporaryDirectory() as temporary, mock.patch.object(
            release_archives.subprocess,
            "run",
        ) as run:
            outputs = release_archives.build_release_archives(
                commit="deadbeef",
                prefix="example-1.0.0/",
                output_base=Path(temporary) / "dist" / "example-1.0.0",
                cwd=ROOT,
            )

        self.assertEqual(2, run.call_count)
        self.assertEqual(
            ("example-1.0.0.zip", "example-1.0.0.tar.gz"),
            tuple(path.name for path in outputs),
        )
        for call in run.call_args_list:
            command = call.args[0]
            self.assertEqual(
                (
                    "git",
                    "-c",
                    "core.autocrlf=false",
                    "-c",
                    "core.eol=lf",
                    "archive",
                ),
                command[:6],
            )
            self.assertEqual("UTC", call.kwargs["env"]["TZ"])
            self.assertEqual(ROOT, call.kwargs["cwd"])
            self.assertTrue(call.kwargs["check"])

    def test_repeated_archives_are_identical_and_formats_agree(self) -> None:
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            with mock.patch.dict(os.environ, {"TZ": "Australia/Sydney"}):
                first = release_archives.build_release_archives(
                    commit="HEAD",
                    prefix="release-test/",
                    output_base=root / "first" / "release-test",
                    cwd=ROOT,
                )
            with mock.patch.dict(os.environ, {"TZ": "Pacific/Auckland"}):
                second = release_archives.build_release_archives(
                    commit="HEAD",
                    prefix="release-test/",
                    output_base=root / "second" / "release-test",
                    cwd=ROOT,
                )

            self.assertEqual(
                tuple(_sha256(path) for path in first),
                tuple(_sha256(path) for path in second),
            )
            self.assertEqual(_zip_files(first[0]), _tar_files(first[1]))

    def test_release_workflow_uses_the_portable_builder(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8",
        )
        self.assertIn("TZ: UTC", workflow)
        self.assertIn("python tools/build_release_archives.py", workflow)
        self.assertNotIn("\n          git archive ", workflow)

    def test_release_workflow_is_draft_aware_and_race_safe(self) -> None:
        workflow_path = ROOT / ".github" / "workflows" / "release.yml"
        workflow = workflow_path.read_text(encoding="utf-8")

        self.assertNotIn("gh release view", workflow)
        self.assertNotIn("gh release edit", workflow)
        self.assertIn("releases?per_page=100", workflow)
        self.assertIn(".tag_name == \\\"$tag\\\" and .draft == true", workflow)
        self.assertGreaterEqual(workflow.count("git/ref/heads/main"), 2)
        self.assertIn('refs/tags/$tag^{}', workflow)
        self.assertIn("repos/$GITHUB_REPOSITORY/releases/$release_id", workflow)
        self.assertIn("-F draft=false", workflow)

        loaded = yaml.safe_load(workflow)
        for step in loaded["jobs"]["release"]["steps"]:
            run = step.get("run", "")
            if "gh " in run:
                with self.subTest(step=step["name"]):
                    self.assertEqual(
                        "${{ github.token }}",
                        step.get("env", {}).get("GH_TOKEN"),
                    )

    def test_release_workflow_verifies_exact_assets_and_attestations(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8",
        )

        self.assertIn("Unexpected release asset inventory.", workflow)
        self.assertIn("/tmp/expected-digests", workflow)
        self.assertIn(".immutable == true", workflow)
        self.assertIn(".isLatest == true", workflow)
        self.assertIn('gh release verify "$tag"', workflow)
        self.assertIn('gh release verify-asset "$tag" "$file"', workflow)
        self.assertIn("--source-digest", workflow)
        self.assertIn("--source-ref", workflow)
        self.assertIn(
            '"dist/australian-accounting-skills-${{ steps.release.outputs.version }}.zip"',
            workflow,
        )
        self.assertIn(
            '"dist/australian-accounting-skills-${{ steps.release.outputs.version }}.tar.gz"',
            workflow,
        )
        self.assertEqual(
            1,
            workflow.count("--predicate-type https://spdx.dev/Document/v2.3"),
        )

    def test_release_pins_exact_skills_cli_inventory(self) -> None:
        workflow = (ROOT / ".github" / "workflows" / "release.yml").read_text(
            encoding="utf-8",
        )
        verifier = (ROOT / "tests" / "verify_skills_cli.py").read_text(
            encoding="utf-8",
        )

        self.assertIn("python tests/verify_skills_cli.py", workflow)
        self.assertIn('SKILLS_CLI_VERSION = "1.5.22"', verifier)
        self.assertIn("reported_count != len(EXPECTED_SKILLS)", verifier)
        self.assertIn("discovered != EXPECTED_SKILLS", verifier)

    def test_builder_refuses_unsafe_prefixes(self) -> None:
        with TemporaryDirectory() as temporary:
            output = Path(temporary) / "archive"
            for prefix in ("absolute", "/absolute/", "../escape/"):
                with self.subTest(prefix=prefix), self.assertRaises(ValueError):
                    release_archives.build_release_archives(
                        commit="HEAD",
                        prefix=prefix,
                        output_base=output,
                        cwd=ROOT,
                    )


if __name__ == "__main__":
    unittest.main()
