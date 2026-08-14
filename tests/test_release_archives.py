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
