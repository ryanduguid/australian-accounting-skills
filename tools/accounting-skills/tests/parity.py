"""Compare the native coverage builder with the unchanged original on fabricated trees."""
import argparse
import importlib.util
import itertools
import json
import os
import subprocess
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("original_coverage", args.root / "scripts/build_coverage.py")
    assert spec and spec.loader
    original = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(original)
    binary = args.binary.resolve()
    count = 0

    def compare(root):
        nonlocal count
        original.SKILLS_DIRECTORY = root / ".claude/skills"
        original.CASES_DIRECTORY = root / "validation/cases"
        original.TESTS_DIRECTORY = root / "tests"
        expected = original.rendered(original.build())
        actual = subprocess.run([str(binary), "build-coverage", "--root", str(root)], capture_output=True, timeout=10)
        assert actual.returncode == 0 and actual.stderr == b"", (actual.returncode, actual.stderr)
        assert actual.stdout == expected.replace("\n", os.linesep).encode(), (root, count)
        count += 1

    compare(args.root)
    with tempfile.TemporaryDirectory(prefix="coverage-parity-") as directory:
        root = Path(directory)
        compare(root)
        for skill in ("alpha", "béta", "zulu"):
            folder = root / ".claude/skills" / skill
            folder.mkdir(parents=True)
            (folder / "SKILL.md").write_text("not parsed", encoding="utf-8")
        cases = root / "validation/cases"
        cases.mkdir(parents=True)
        tests = root / "tests"
        tests.mkdir()
        (tests / "Z.py").write_text("'alpha\" and 'béta'", encoding="utf-8")
        (tests / "a.py").write_text("\"zulu'", encoding="utf-8")
        (tests / ".py").write_text("'alpha'", encoding="utf-8")
        (cases / ".md").write_text("---\n- alpha\n---\n", encoding="utf-8")
        for separator in ("\n", "\r\n", "\r", "\x85", "\u2028", "\u2029", "\x1c"):
            for whitespace in ("", " ", "\t", "\x1f", "\u2003"):
                (cases / "alpha-missing-evidence.md").write_bytes(
                    separator.join(("---", "target_skills:", whitespace + "-" + whitespace + "alpha", "- alpha", "---", "body")).encode())
                compare(root)
        (root / ".claude/skills/zulu/sources.exempt.json").write_text("{}", encoding="utf-8")
        index = root / ".claude/skills/alpha/sources.json"
        statuses = (None, 200, 200.0, 404, "200", False)
        for status, manual, checked, modified in itertools.product(
            statuses, (None, {}, "yes"), ("", "2025-01-01"), ("", "2024-01-01", "2026-01-01")
        ):
            records = [None, "ignored", {"checked_at": checked, "fetched_at": "2026-10-22",
                       "source_last_modified": modified, "url": "https://example.invalid/évidence",
                       "http_status": status, "manual_review": manual},
                       {"checked_at": "2024-10-01", "fetched_at": "2026-10-21"}]
            index.write_text(json.dumps({"sources": records}, ensure_ascii=False), encoding="utf-8")
            compare(root)
        index.unlink()
        cli = []
        oracle = "import importlib.util,sys;from pathlib import Path;s=importlib.util.spec_from_file_location('oracle',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);r=Path(sys.argv[2]);m.REPOSITORY=r;m.SKILLS_DIRECTORY=r/'.claude/skills';m.CASES_DIRECTORY=r/'validation/cases';m.TESTS_DIRECTORY=r/'tests';m.COVERAGE_FILE=r/'coverage.json';sys.exit(m.main(sys.argv[3:]))"
        for mode in ([], ["--check"], ["--write"], ["--check"], ["--check", "--write"]):
            before = (root / "coverage.json").read_bytes() if (root / "coverage.json").exists() else None
            expected = subprocess.run([os.sys.executable, "-I", "-X", "utf8", "-c", oracle, str(args.root / "scripts/build_coverage.py"), str(root), *mode], capture_output=True, timeout=10)
            payload = (root / "coverage.json").read_bytes() if (root / "coverage.json").exists() else None
            if before is None:
                (root / "coverage.json").unlink(missing_ok=True)
            else:
                (root / "coverage.json").write_bytes(before)
            actual = subprocess.run([str(binary), "build-coverage", "--root", str(root), *mode], capture_output=True, timeout=10)
            assert (actual.returncode, actual.stdout, actual.stderr) == (expected.returncode, expected.stdout, expected.stderr), mode
            assert ((root / "coverage.json").read_bytes() if (root / "coverage.json").exists() else None) == payload
            cli.append({"flags": mode, "exit": actual.returncode})
        (root / "coverage.json").write_text("stale", encoding="utf-8")
        actual = subprocess.run([str(binary), "build-coverage", "--root", str(root), "--check"], capture_output=True, timeout=10)
        assert actual.returncode == 2
        for card in ("bad\n---\n", "---\nmissing end\n"):
            (cases / "bad.md").write_text(card, encoding="utf-8")
            try:
                original.build()
            except ValueError:
                pass
            else:
                raise AssertionError("original accepted malformed frontmatter")
            actual = subprocess.run([str(binary), "build-coverage", "--root", str(root)], capture_output=True, timeout=10)
            assert actual.returncode == 1 and not actual.stdout
    args.record.write_text(json.dumps({"matrix_byte_comparisons": count, "cli": cli,
        "stale_output_exit": 2, "malformed_frontmatter_refusals": 2,
        "intentional_adaptations": ["explicit/current-directory root", "generic exit-1 processing/argument diagnostics",
            "non-string source date/URL fields and non-array source collections refused", "non-Unicode filenames refused",
            "native stdout is UTF-8; CLI byte comparison uses Python -X utf8"]}, indent=2) + "\n")


if __name__ == "__main__":
    main()
