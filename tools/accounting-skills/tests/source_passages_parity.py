"""Offline command qualification against the unchanged Python passage module."""

import argparse
import dataclasses
import difflib
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

parser = argparse.ArgumentParser()
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--probe", type=Path, required=True)
parser.add_argument("--binary", type=Path, required=True)
parser.add_argument("--record", type=Path, required=True)
args = parser.parse_args()
R = args.root.resolve()
sys.path.insert(0, str(R / "scripts"))
reference = R / "tools/accounting-skills/tests/reference_difflib_3148.py.fixture"
assert hashlib.sha256(reference.read_bytes()).hexdigest() == (
    "dcf149dea54bce852505d29a195a179402197cef77ac31b467027a2a56265af5"
), "difflib reference drift"
loader = importlib.machinery.SourceFileLoader("passages_reference_difflib3148", str(reference))
spec = importlib.util.spec_from_loader(loader.name, loader)
oracle = importlib.util.module_from_spec(spec)
loader.exec_module(oracle)
runtime_difflib = difflib
sys.modules["difflib"] = oracle
try:
    import source_passages as p
finally:
    sys.modules["difflib"] = runtime_difflib
import source_refresh as s  # noqa: E402

original = {name: getattr(p, name) for name in ["indexed_url", "snapshot", "load_snapshot", "compare", "main"]}
skills = R / ".claude/skills"
url = next(str(record["url"]) for _, _, record in s.records(s.index_files()))
child = subprocess.Popen([str(args.probe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         encoding="utf-8", text=True)
active = "differential"
calls = {}
counts = {}
cli_cases = []


def rpc(op, **kw):
    tally = calls.setdefault(active, {})
    tally[op] = tally.get(op, 0) + 1
    child.stdin.write(json.dumps({"op": op, "skills": str(skills), **kw}) + "\n")
    child.stdin.flush()
    while True:
        line = child.stdout.readline()
        assert line, f"probe ended: {child.poll()}"
        reply = json.loads(line)
        if "event" not in reply:
            break
        assert reply["event"] == "fetch" and reply["include_text"] is True
        fetched = s.fetch(reply["url"], include_text=True)
        child.stdin.write(json.dumps(dataclasses.asdict(fetched)) + "\n")
        child.stdin.flush()
    if "error" in reply:
        raise ValueError(reply["error"])
    return reply["ok"]


def native_main(argv=None):
    tally = calls.setdefault(active, {})
    tally["cli"] = tally.get("cli", 0) + 1
    result = subprocess.run([str(args.binary), "source-passages", *argv, "--root", str(R)],
                            capture_output=True, text=True, encoding="utf-8", timeout=20)
    print(result.stdout, end="")
    print(result.stderr, file=sys.stderr, end="")
    if result.returncode == 2 and result.stderr:
        raise SystemExit(2)
    return result.returncode


class RecordedResult(unittest.TextTestResult):
    def startTest(self, test):
        global active
        active = test.id()
        super().startTest(test)


def replay():
    suite = unittest.TestSuite()
    for filename, cls in [("test_source_passages.py", "SourcePassageTests"),
                          ("test_script_entry_points.py", "SourcePassagesTests")]:
        spec = importlib.util.spec_from_file_location(filename[:-3], R / "tests" / filename)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(getattr(module, cls)))
    with mock.patch.multiple(p,
                             indexed_url=lambda url: rpc("indexed", url=url),
                             snapshot=lambda url: rpc("snapshot", url=url),
                             load_snapshot=lambda path: rpc("load", path=str(path)),
                             compare=lambda before, after: rpc("compare", before=before, after=after),
                             main=native_main):
        result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(suite)
    assert result.testsRun == 6
    assert result.wasSuccessful()
    return {"objects": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)}


def sample(text="", **kw):
    return {"url": url, "final_url": url, "available": True, "text_truncated": False,
            "source_digest": "a" * 64, "text": text,
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(), **kw}


def equal(op, expected, **kw):
    counts[op] = counts.get(op, 0) + 1
    actual = rpc(op, **kw)
    assert actual == expected, {"op": op, "args": kw, "python": expected, "native": actual}


def compare(old, new):
    equal("compare", original["compare"](old, new), before=old, after=new)


def differential():
    global active
    active = "differential"
    rng = random.Random(2026102301)
    separators = ["\n", "\r", "\r\n", "\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"]
    units = ["", "a", "b", "c", "a", "a", "é", "e\u0301", "𝄞", "\x1f", "\x00", "\x7f"]
    for separator in separators:
        for old in ["", separator, "a" + separator, separator + "b", "a" + separator * 2 + "b"]:
            for new in [old, "new" + separator, old + "tail", old.replace("a", "b")]:
                compare(sample(old), sample(new))
    for size in [0, 1, 2, 3, 4, 5, 59, 60, 61, 199, 200, 201, 399, 400, 401]:
        old = [str(i) for i in range(size)]
        for new in [old[::-1], ["x"] * size, ["prefix", *old], [*old, "suffix"],
                    ["x" if i % 8 == 0 else line for i, line in enumerate(old)]]:
            compare(sample("\n".join(old)), sample("\n".join(new)))
    for _ in range(5000):
        size = rng.choice([rng.randrange(0, 45), rng.randrange(195, 205), rng.randrange(390, 410)])
        old = rng.choices(units, k=size)
        new = old.copy()
        for _ in range(rng.randrange(0, 12)):
            i = rng.randrange(len(new) + 1)
            end = min(len(new), i + rng.randrange(0, 8))
            new[i:end] = rng.choices(units, k=rng.randrange(0, 8))
        sep = rng.choice(separators)
        compare(sample(sep.join(old)), sample(sep.join(new), text_truncated=rng.choice([True, False])))
    for length in [238, 239, 240, 241, 1000, 32768]:
        for ch in ["a", "𝄞", "é"]:
            compare(sample("old"), sample(ch * length))
    for change in [{"source_digest": "b" * 64}, {"final_url": url + "?q=1"},
                   {"available": False}, {"url": url + "#x"}, {"text_truncated": True}]:
        compare(sample("same"), sample("same", **change))
    for fetched in [s.Fetched(200, url, "digest", "readable", "text/plain", "", "", text="fabricated𝄞"),
                    s.Fetched(200, url, "", "", "", "", ""),
                    s.Fetched(404, url, "", "", "", "", "missing"),
                    s.Fetched(None, url, "", "", "", "", "Source policy: fabricated refusal")]:
        with mock.patch.object(s, "fetch", return_value=fetched):
            equal("snapshot", original["snapshot"](url), url=url)
    for text in ["", "é\x7f𝄞\x00\b\f\n\r\t", "\\\"/"]:
        value = {"text": text, "nested": [True, False, None, 1, {"x": "雪"}]}
        equal("render", json.dumps(value, indent=2, ensure_ascii=True) + "\n", value=value)


def file_and_cli_cases():
    global active
    active = "file-and-cli"
    with tempfile.TemporaryDirectory(prefix="passages-offline-") as temporary:
        directory = Path(temporary)
        path = directory / "snapshot.json"
        cases = [sample(""), sample("𝄞" * 32768), sample("a", available=False, source_digest=""),
                 sample("a", url=url + "#fragment", extra={"b": 2, "a": 1})]
        invalid = [[], None, {"text": 1}, sample("a", text_sha256="x"), sample("a" * 32769),
                   sample("a", url=1), sample("a", final_url=1), sample("a", url=url + "/unindexed-fixture"),
                   sample("a", final_url="http://127.0.0.1/"), sample("a", source_digest="A" * 64)]
        for flag in [0, 1, "true", None, [], {}]:
            for key in ["available", "text_truncated"]:
                invalid.append(sample("a", **{key: flag}))
        for value in cases + invalid:
            path.write_text(json.dumps(value), encoding="utf-8")
            try:
                expected = original["load_snapshot"](path)
            except ValueError as error:
                try:
                    rpc("load", path=str(path))
                except ValueError as native:
                    assert str(native) == str(error), (str(error), str(native))
                else:
                    raise AssertionError("native accepted malformed snapshot")
                counts["load-refusal"] = counts.get("load-refusal", 0) + 1
            else:
                equal("load", expected, path=str(path))
        path.write_bytes(b"x" * (1024 * 1024 + 1))
        for function in [original["load_snapshot"], lambda path: rpc("load", path=str(path))]:
            try:
                function(path)
            except ValueError as error:
                assert "1 MiB" in str(error)
            else:
                raise AssertionError("oversized file accepted")
        before = directory / "before.json"
        after = directory / "after.json"
        before.write_text(json.dumps(sample("old𝄞\n")), encoding="utf-8")
        after.write_text(json.dumps(sample("newé\n")), encoding="utf-8")

        def cli(name, argv, code, output=None, expected=None):
            completed = subprocess.run([str(args.binary), "source-passages", *map(str, argv), "--root", str(R)],
                                       capture_output=True, timeout=20)
            assert completed.returncode == code, (name, completed)
            if expected is not None:
                assert output.read_bytes() == (json.dumps(expected, indent=2, ensure_ascii=True) + "\n").replace("\n", os.linesep).encode()
            cli_cases.append({"name": name, "exit": code, "stdout": completed.stdout.decode(),
                              "stderr": completed.stderr.decode(), "output_checked": expected is not None})

        output = directory / "nested" / "report.json"
        command = ["compare", "--before", before, "--after", after, "--output", output]
        expected = original["compare"](sample("old𝄞\n"), sample("newé\n"))
        cli("comparison-bytes", command, 0, output, expected)
        content = output.read_bytes()
        cli("overwrite", command, 2)
        assert output.read_bytes() == content
        cli("repository-output", [*command[:-1], R / "forbidden-passages.json"], 2)
        assert not (R / "forbidden-passages.json").exists()
        after.write_text(json.dumps(sample("", available=False)), encoding="utf-8")
        unavailable = directory / "unavailable.json"
        expected = original["compare"](sample("old𝄞\n"), sample("", available=False))
        cli("unavailable-comparison", [*command[:-1], unavailable], 2, unavailable, expected)
        after.write_text("{broken", encoding="utf-8")
        cli("broken-json", [*command[:-1], directory / "broken-output.json"], 1)
        cli("missing-input", ["compare", "--before", directory / "missing", "--after", after,
                              "--output", directory / "missing-output.json"], 1)
        cli("unindexed-capture-no-fetch", ["snapshot", "--url", "https://www.ato.gov.au/unindexed-offline-fixture",
                                          "--output", directory / "capture.json"], 1)
        for argv in [[], ["other"], ["compare"], ["snapshot", "--output", directory / "none"],
                     ["compare", "--url", url, "--output", directory / "none"]]:
            cli("usage-" + str(len(cli_cases)), argv, 2)


hashes = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in s.index_files()}
try:
    replay_result = replay()
    differential()
    file_and_cli_cases()
    assert hashes == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in s.index_files()}
    args.record.write_text(json.dumps({"reference_difflib_sha256": hashlib.sha256(reference.read_bytes()).hexdigest(),
                                      "original": replay_result, "calls": calls, "comparisons": counts,
                                      "cli_cases": cli_cases, "indexes_unchanged": True}, indent=2) + "\n")
    print(json.dumps({"original": replay_result, "comparisons": counts, "cli_cases": len(cli_cases)}))
finally:
    child.stdin.close()
    try:
        child.wait(timeout=10)
    except subprocess.TimeoutExpired:
        child.kill()
        child.wait(timeout=10)
