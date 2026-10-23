"""Offline exact-byte qualification of the complete trial-preparation command."""

import argparse
import hashlib
import importlib.util
import json
import random
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--root", type=Path, required=True)
parser.add_argument("--probe", type=Path, required=True)
parser.add_argument("--binary", type=Path, required=True)
parser.add_argument("--record", type=Path, required=True)
args = parser.parse_args()
R = args.root.resolve()
sys.path.insert(0, str(R / "scripts"))
import prepare_trial as p  # noqa: E402

probe = subprocess.Popen([str(args.probe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         text=True, encoding="utf-8")
calls = {}
counts = {}
active = "differential"
cli_cases = []


def rpc(op, **values):
    tally = calls.setdefault(active, {})
    tally[op] = tally.get(op, 0) + 1
    probe.stdin.write(json.dumps({"op": op, **values}) + "\n")
    probe.stdin.flush()
    while True:
        line = probe.stdout.readline()
        assert line, f"probe exited: {probe.poll()}"
        reply = json.loads(line)
        if "event" not in reply:
            break
        assert reply["event"] == "link"
        # Prefix spelling differs after Windows canonicalize. Keep the original
        # mock's Path identity whilst probing the same actual filesystem entry.
        spelling = reply["path"]
        if spelling.startswith("\\\\?\\"):
            spelling = spelling[4:]
        linked = Path(spelling).is_symlink()
        probe.stdin.write(json.dumps(linked) + "\n")
        probe.stdin.flush()
    if "error" in reply:
        raise ValueError(reply["error"])
    return reply["ok"]


def task_input(card, name):
    value = rpc("input", bytes=list(card), name=name)
    return bytes(value["bytes"]), value["skills"]


def prepare(case_id, destination, model, runtime, root=p.ROOT):
    return rpc("prepare", case=case_id, destination=str(destination), model=model,
               runtime=runtime, root=str(root))


def native_main():
    tally = calls.setdefault(active, {})
    tally["cli"] = tally.get("cli", 0) + 1
    result = subprocess.run([str(args.binary), "prepare-trial", *sys.argv[1:], "--root", str(R)],
                            capture_output=True, timeout=20)
    assert result.returncode == 0, result


class RecordedResult(unittest.TextTestResult):
    def startTest(self, test):
        global active
        active = test.id()
        super().startTest(test)


def replay():
    spec = importlib.util.spec_from_file_location("test_prepare_trial", R / "tests/test_prepare_trial.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.task_input = task_input
    module.prepare = prepare
    module.digest = lambda data: rpc("hash", bytes=list(data))
    module.main = native_main
    result = unittest.TextTestRunner(verbosity=2, resultclass=RecordedResult).run(
        unittest.defaultTestLoader.loadTestsFromModule(module))
    assert result.testsRun == 8 and result.wasSuccessful()
    return {"objects": result.testsRun, "failures": len(result.failures), "errors": len(result.errors)}


def check_input(card, name="example.md"):
    counts["input"] = counts.get("input", 0) + 1
    try:
        expected = p.task_input(card, name)
    except ValueError as error:
        try:
            task_input(card, name)
        except ValueError as native:
            assert str(error) == str(native), (str(error), str(native))
        else:
            raise AssertionError("native accepted malformed task card")
        counts["input_refusals"] = counts.get("input_refusals", 0) + 1
    else:
        assert task_input(card, name) == expected


def card(body):
    return ("---\nid: example\nsynthetic: true\ntarget_skills: [example]\n---\n" + body).encode()


def body(sections):
    return "\n".join("## " + heading + "\n\n" + text for heading, text in sections)


def differential():
    global active
    active = "differential"
    rng = random.Random(2026102303)
    sections = list(p.TASK_SECTIONS)
    texts = ["", "  text\n", "\x1c\x1d\x1e\x1ftext\x85\u2028\u2029", "é𝄞", "## Other\nextra", "\n\n", "### Nested\nbody", " # not a heading", "\rtext\r"]
    for _ in range(1500):
        order = sections + ["Required checks", "Must not do", "Source-verification and reviewer boundary"]
        rng.shuffle(order)
        check_input(card(body([(heading, rng.choice(texts)) for heading in order])))
    for missing in sections:
        check_input(card(body([(heading, "fixture") for heading in sections if heading != missing])))
    for duplicate in sections + ["Unknown"]:
        check_input(card(body([(heading, "fixture") for heading in sections + [duplicate, duplicate]])))
    for path in sorted((R / "validation/cases").glob("*.md")):
        check_input(path.read_bytes(), path.name)
    names = [".env", ".ENV", ".env.local", "file.key", "file.KEY", "file.Key", "file.tokenſ", ".key", "..key", "...tokens", "file.tokens.", "file.pem ", "key", "file.tar.KEY", "name.env", ".enVdirectory"]
    # Exhaust all Unicode scalar values for ASCII-producing case folds, then
    # exercise their relevant positions. This avoids trusting web codec rules.
    folded = [chr(n) for n in range(128, 0x110000) if not 0xD800 <= n <= 0xDFFF
              and chr(n).casefold().isascii()]
    for character in folded:
        for literal in [".env", ".pem", ".key", ".token", ".tokens"]:
            for i in range(1, len(literal)):
                names.append("file" + literal[:i] + character + literal[i + 1:])
                names.append(literal[:i] + character + literal[i + 1:])
    for name in names:
        expected = name.casefold().startswith(".env") or Path(name).suffix.casefold() in {".pem", ".key", ".token", ".tokens"}
        assert rpc("credential", name=name) == expected, name
    counts["credential_names"] = len(names)
    counts["non_ascii_ascii_fold_scalars"] = len(folded)


def packets_and_cli():
    global active
    active = "packets-and-cli"
    with tempfile.TemporaryDirectory(prefix="trial-parity-") as temporary:
        base = Path(temporary)
        root = base / "repository"
        cards = root / "validation/cases"
        cards.mkdir(parents=True)
        content = card(body([(heading, "Fabricated𝄞\n") for heading in p.TASK_SECTIONS] + [("Required checks", "Withheld")]))
        (cards / "example.md").write_bytes(content)
        folder = root / ".claude/skills/example"
        for name in ["SKILL.md", "alpha.md", "alpha/child.md", "a-z.txt", "a/child.md", "ref/é.md", "ref/𝄞.txt", ".visible"]:
            path = folder / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(("Synthetic: " + name + "\r\n").encode())
        originals = {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.rglob("*") if path.is_file()}
        for index, (model, runtime) in enumerate([("unselected", "unselected"), ("𝄞é\n\x7f", "runtime\t\"x")]):
            expected = base / f"python-{index}"
            actual = base / f"rust-{index}"
            p.prepare("example", expected, model, runtime, root=root)
            prepare("example", actual, model, runtime, root=root)
            assert sorted(path.name for path in actual.iterdir()) == ["context.json", "input.md", "rubric.md"]
            for name in ["input.md", "rubric.md", "context.json"]:
                assert (actual / name).read_bytes() == (expected / name).read_bytes(), name
                counts["packet_bytes"] = counts.get("packet_bytes", 0) + 1

        def cli(name, argv, code):
            completed = subprocess.run([str(args.binary), "prepare-trial", *map(str, argv), "--root", str(root)], capture_output=True, timeout=20)
            assert completed.returncode == code, (name, completed)
            cli_cases.append({"name": name, "exit": code, "stdout": completed.stdout.decode(), "stderr": completed.stderr.decode()})

        output = base / "cli"
        cli("success", ["example", output, "--model", "test-model", "--runtime", "test-runtime"], 0)
        saved = {path.name: path.read_bytes() for path in output.iterdir()}
        cli("overwrite", ["example", output], 1)
        assert saved == {path.name: path.read_bytes() for path in output.iterdir()}
        cli("repository-output", ["example", root / "trial"], 1)
        cli("path-traversal", ["../example", base / "traversal"], 1)
        cli("missing-card", ["absent", base / "missing"], 1)
        for index, argv in enumerate([[], ["example"], ["example", base / "usage", "--other"], ["example", base / "usage", "--model"]]):
            cli(f"usage-{index}", argv, 2)
        assert originals == {path: hashlib.sha256(path.read_bytes()).hexdigest() for path in root.rglob("*") if path.is_file()}
        assert not (root / "trial").exists()


try:
    original_result = replay()
    differential()
    packets_and_cli()
    args.record.write_text(json.dumps({"original": original_result, "calls": calls, "counts": counts,
                                      "cli": cli_cases, "source_files_unchanged": True,
                                      "adapter": "Windows verbatim path prefix removed only for original link-check mock identity; callback probes original Path.is_symlink. Production uses native reparse-point checks."}, indent=2) + "\n")
    print(json.dumps({"original": original_result, "counts": counts, "cli_cases": len(cli_cases)}))
finally:
    probe.stdin.close()
    try:
        probe.wait(timeout=10)
    except subprocess.TimeoutExpired:
        probe.kill()
        probe.wait(timeout=10)
