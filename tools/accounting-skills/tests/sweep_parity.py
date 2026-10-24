"""Replay original sweep test objects and compare fabricated report outcomes."""
import argparse
import importlib
import itertools
import json
import os
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--probe", type=Path, required=True)
    parser.add_argument("--record", type=Path, required=True)
    args = parser.parse_args()
    root, binary = args.root.resolve(), args.binary.resolve()
    sys.path.insert(0, str(root))
    sys.path.insert(0, str(root / "scripts"))
    original = importlib.import_module("sweep_outcome")
    tests = importlib.import_module("tests.test_sweep_outcome")
    originals = original.outcome, original.main
    child = subprocess.Popen([str(args.probe.resolve())], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
    calls = 0
    cli_calls = 0
    test_records = []

    def native(status, report, started, *, within=None):
        nonlocal calls
        request = {"status": status, "report": str(report), "started": started.strftime("%Y-%m-%dT%H:%M:%SZ"),
                   "within": str(within if within is not None else Path.cwd())}
        assert child.stdin and child.stdout
        child.stdin.write(json.dumps(request) + "\n")
        child.stdin.flush()
        response = json.loads(child.stdout.readline())
        calls += 1
        if "error" in response:
            raise original.SweepError(response["error"])
        return original.Outcome(**response["outcome"])

    # Windows cannot start a process from an empty environment block, which an
    # original test's cleared environment leaves under shells without hidden
    # drive variables, such as Git Bash. Only SYSTEMROOT is restored.
    system_root = {"SYSTEMROOT": os.environ["SYSTEMROOT"]} if os.name == "nt" else {}

    def native_main(argv):
        nonlocal cli_calls
        cli_calls += 1
        result = subprocess.run([str(binary), "sweep-outcome", *argv], cwd=Path.cwd(),
                                env={**os.environ, **system_root},
                                capture_output=True, timeout=10, encoding="utf-8")
        print(result.stdout, end="")
        print(result.stderr, file=sys.stderr, end="")
        return result.returncode

    try:
        original.outcome, original.main = native, native_main
        class RecordingResult(unittest.TextTestResult):
            def startTest(self, test):
                self.before = calls, cli_calls
                super().startTest(test)

            def stopTest(self, test):
                test_records.append({"test": test.id(), "native_outcome_calls": calls - self.before[0],
                                     "native_cli_calls": cli_calls - self.before[1]})
                super().stopTest(test)

        suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
        result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(suite)
        assert result.wasSuccessful() and not result.skipped
        original.outcome, original.main = originals
        comparisons = 0
        with tempfile.TemporaryDirectory(prefix="sweep-parity-") as directory:
            base = Path(directory)
            report = base / "report.md"
            started = datetime(2026, 9, 20, 19, 0, 5, tzinfo=timezone.utc)

            def compare(text, status):
                nonlocal comparisons
                report.write_text(text, encoding="utf-8")
                try:
                    expected = originals[0](status, report, started, within=base)
                except (original.SweepError, ValueError) as error:
                    try:
                        native(status, report, started, within=base)
                    except original.SweepError as actual:
                        # Timestamp/codec errors deliberately use native diagnostics.
                        if isinstance(error, original.SweepError):
                            assert str(actual) == str(error), (text, status, str(actual), str(error))
                    else:
                        raise AssertionError(("native passed a refused report", text, status))
                else:
                    actual = native(status, report, started, within=base)
                    assert actual == expected, (text, status, actual, expected)
                comparisons += 1

            for values in itertools.product(range(3), repeat=5):
                outcomes = dict(zip(("changed", "review-due", "baseline-required", "blocked", "unreachable"), values))
                text = tests.report_text({"unchanged": 1, **outcomes}, started)
                for status in (-1, 0, 1, 2, 3):
                    compare(text, status)
            ordinary = tests.report_text({"unchanged": 1}, started)
            for mutation in ("", "bad header\n", ordinary.replace("- blocked", "- other"),
                             ordinary + "- changed: 0\n", ordinary.replace("Swept 1", "Swept 0"),
                             ordinary.replace("2026-09-20", "2026-02-30"),
                             tests.report_text({"unchanged": 1}, started - timedelta(minutes=1))):
                for status in (0, 2):
                    compare(mutation, status)
            for value in ("2", "0002", "٢", "２", "𝟚", "9" * 120):
                for newline in ("\n", "\r\n", "\r"):
                    compare(ordinary.replace("- changed: 0", "- changed: " + value).replace("\n", newline), 2)
            unicode_digits = [chr(point) for point in range(0x110000) if chr(point).isdecimal()]
            for digit in unicode_digits:
                compare(ordinary.replace("- changed: 0", "- changed: " + digit), 2)
            compare(tests.report_text({"unchanged": 2000, "changed": 1}, started), 2)
            cli = []
            for flags in (["--status", "0"], ["--status", "2"]):
                report.write_text(ordinary, encoding="utf-8")
                argv = [*flags, "--report", str(report), "--started", "2026-09-20T19:00:05Z"]
                expected = subprocess.run([sys.executable, "-I", "-X", "utf8", str(root / "scripts/sweep_outcome.py"), *argv], cwd=base, capture_output=True, timeout=10)
                actual = subprocess.run([str(binary), "sweep-outcome", *argv], cwd=base, capture_output=True, timeout=10)
                assert (actual.returncode, actual.stdout, actual.stderr) == (expected.returncode, expected.stdout, expected.stderr), (argv, actual, expected)
                cli.append({"status": flags[-1], "exit": actual.returncode})
            (base / "--report.md").write_text(ordinary, encoding="utf-8")
            equals = ["--status=0", "--report=--report.md", "--started=2026-09-20T19:00:05Z"]
            actual = subprocess.run([str(binary), "sweep-outcome", *equals], cwd=base, capture_output=True, timeout=10)
            expected = subprocess.run([sys.executable, "-I", "-X", "utf8", str(root / "scripts/sweep_outcome.py"), *equals], cwd=base, capture_output=True, timeout=10)
            assert (actual.returncode, actual.stdout, actual.stderr) == (expected.returncode, expected.stdout, expected.stderr)
            cli.append({"equals_operands": True, "dash_prefixed_report": True, "exit": actual.returncode})
        args.record.write_text(json.dumps({"original_tests": result.testsRun, "skips": result.skipped,
            "native_outcome_calls": calls, "native_cli_calls": cli_calls,
            "test_records": test_records, "fabricated_comparisons": comparisons, "direct_cli": cli,
            "unicode_version": unicodedata.unidata_version, "all_original_unicode_decimal_digits": len(unicode_digits),
            "original_helpers_restored": original.outcome is originals[0] and original.main is originals[1]}, indent=2) + "\n")
    finally:
        original.outcome, original.main = originals
        child.terminate()
        child.communicate(timeout=10)


if __name__ == "__main__":
    main()
