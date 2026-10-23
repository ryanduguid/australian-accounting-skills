"""Offline behavioural comparison of the complete source-refresh command.

The original HTTPError mock and mocked CLI dispatch tests remain Python.
Native transport ownership/refusal checks live in source_refresh.rs.
"""

import _markupbase
import argparse
import dataclasses
import datetime
import hashlib
import html
import html.entities
import html.parser
import importlib.machinery
import importlib.util
import json
import os
import random
import subprocess
import sys
import unicodedata
import unittest
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--root", required=True, type=Path)
parser.add_argument("--probe", required=True, type=Path)
parser.add_argument("--binary", required=True, type=Path)
parser.add_argument("--record", required=True, type=Path)
arguments = parser.parse_args()
R = arguments.root.resolve()
E = arguments.record.parent
P = R / "tools/accounting-skills"
sys.path.insert(0, str(R / "scripts"))
# The HTML parser changed within Python 3.14. Pin the independent reference,
# including its unchanged dependencies, instead of comparing different parsers.
assert unicodedata.unidata_version == "16.0.0", "qualification requires Python Unicode 16.0"
assert sys.get_int_max_str_digits() == 4300, "qualification requires Python's default digit limit"
reference = P / "tests/reference_html_parser_3148.py.fixture"
oracle_sha = hashlib.sha256(reference.read_bytes()).hexdigest()
assert oracle_sha == "5c5ed245889135564e75dfed9a47aeb6b4d3e5a2e9614d918a986767e3747539"
for module, expected in [
    (html, "923d82d821e75e8d235392c10c145ab8587927b3faf9c952bbd48081eebd8522"),
    (html.entities, "d9c65fb2828dbc1f3e399058a341d51e9375ec5bca95a8e92599c41bd5b78bde"),
    (_markupbase, "01046da4883344a898fb1261a0805a7ab1bae371e95ade31311ac03b43b33c98"),
]:
    assert hashlib.sha256(Path(module.__file__).read_text().encode()).hexdigest() == expected, (
        "HTML oracle dependency drift"
    )
loader = importlib.machinery.SourceFileLoader("refresh_reference_html3148", str(reference))
spec = importlib.util.spec_from_loader(loader.name, loader)
oracle = importlib.util.module_from_spec(spec)
loader.exec_module(oracle)
runtime_parser = sys.modules["html.parser"]
sys.modules["html.parser"] = oracle
try:
    import source_refresh as s
finally:
    sys.modules["html.parser"] = runtime_parser

original = {
    name: getattr(s, name)
    for name in [
        "readable_text",
        "body_digest",
        "content_digest",
        "iso_day",
        "upstream_last_modified",
        "review_date",
        "reverify_passed",
        "reverify_note",
        "latest_upstream_date",
        "classify",
        "apply_fetch",
        "source_readiness",
        "refresh",
        "preflight",
        "render",
    ]
}
binary = str(arguments.probe)
child = subprocess.Popen(
    [binary], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8"
)
calls = {}
active = "differential"


def convert(value):
    if dataclasses.is_dataclass(value):
        return {k: convert(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {k: convert(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [convert(v) for v in value]
    return value


def rpc(op, **args):
    calls.setdefault(active, {})[op] = calls.setdefault(active, {}).get(op, 0) + 1
    child.stdin.write(json.dumps({"op": op, **convert(args)}, ensure_ascii=True) + "\n")
    child.stdin.flush()
    while True:
        line = child.stdout.readline()
        if not line:
            raise RuntimeError(f"native probe exited {child.poll()}")
        reply = json.loads(line)
        if "event" not in reply:
            break
        if reply["event"] == "fetch":
            result = convert(s.fetch(reply["url"]))
        else:
            s.time.sleep(reply["seconds"])
            result = None
        child.stdin.write(json.dumps(result) + "\n")
        child.stdin.flush()
    if "error" in reply:
        raise ValueError(reply["error"])
    return reply["ok"]


def refresh(
    *,
    skills=s.SKILLS_DIRECTORY,
    only_skill="",
    only_url="",
    write=False,
    spacing=s.REQUEST_SPACING,
    today=None,
):
    value = rpc(
        "refresh",
        skills=skills,
        skill=only_skill,
        url=only_url,
        write=write,
        spacing=spacing,
        today=today or datetime.date.today().isoformat(),
    )
    return s.Report(
        [s.Outcome(**{**o, "fetched": s.Fetched(**o["fetched"])}) for o in value["outcomes"]],
        [Path(p) for p in value["written"]],
    )


def install():
    s.readable_text = lambda body, charset: rpc("text", body=list(body), charset=charset)
    s.body_digest = lambda body, content_type, charset: tuple(
        rpc("digest", body=list(body), kind=content_type, charset=charset)
    )
    s.content_digest = lambda text: rpc("hash", text=text)
    s.iso_day = lambda value: rpc("date", text=value)
    s.upstream_last_modified = lambda body, last_modified_header, response_date=None: rpc(
        "upstream", body=list(body), last=last_modified_header, served=response_date
    )
    s.review_date = lambda schedule: rpc("review_date", record=schedule)
    s.reverify_passed = lambda record, today: rpc("reverify", record=record, today=today)
    s.reverify_note = lambda passed: rpc("note", text=passed)
    s.latest_upstream_date = lambda record, fetched: rpc("latest", record=record, fetched=fetched)
    s.classify = lambda record, fetched: tuple(rpc("classify", record=record, fetched=fetched))

    def apply(record, fetched, today):
        value = rpc("apply", record=record, fetched=fetched, today=today)
        record.clear()
        record.update(value)

    s.apply_fetch = apply
    s.source_readiness = lambda record, outcome, today: tuple(
        rpc("readiness", record=record, outcome=outcome, today=today)
    )
    s.refresh = refresh
    s.preflight = (
        lambda skill, *, skills=s.SKILLS_DIRECTORY, today=None, spacing=s.REQUEST_SPACING: tuple(
            rpc(
                "preflight",
                skill=skill,
                skills=skills,
                today=today or datetime.date.today().isoformat(),
                spacing=spacing,
            )
        )
    )
    s.render = lambda report, *, write: rpc(
        "render",
        report=report,
        write=write,
        swept=datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )


class Result(unittest.TextTestResult):
    def startTest(self, test):
        global active
        active = test.id()
        calls.setdefault(active, {})
        super().startTest(test)


def replay():
    calls.clear()
    spec = importlib.util.spec_from_file_location(
        "test_source_refresh", R / "tests/test_source_refresh.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    install()
    result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(
        unittest.defaultTestLoader.loadTestsFromModule(module)
    )
    (E / "original-replay.json").write_text(
        json.dumps(
            {
                "tests": result.testsRun,
                "failures": len(result.failures),
                "errors": len(result.errors),
                "calls": calls,
            },
            indent=2,
        )
        + "\n"
    )
    return result.wasSuccessful()


def differential():
    failures = []
    counts = {}
    refusals = []

    def check(op, args, expected):
        counts[op] = counts.get(op, 0) + 1
        try:
            actual = rpc(op, **args)
        except Exception as exc:
            actual = {"error": str(exc)}
        if (
            isinstance(expected, dict)
            and "error" in expected
            and isinstance(actual, dict)
            and "error" in actual
        ):
            known_entity_limit = (
                op == "text"
                and args == {
                    "body": list(('<a x="&#' + "9" * 4301 + ';">text').encode()),
                    "charset": "utf-8",
                }
                and expected["error"].startswith("Exceeds the limit (4300 digits)")
                and actual["error"] == "decimal HTML entity exceeds Python's 4,300-digit conversion limit"
            )
            if known_entity_limit:
                refusals.append({"op": op, "category": "decimal_entity_limit", "python": expected["error"], "native": actual["error"]})
            else:
                failures.append({"op": op, "unexpected_paired_errors": True, "expected": expected, "actual": actual})
        elif convert(expected) != actual:
            failures.append(
                {"op": op, "args": args, "expected": convert(expected), "actual": actual}
            )

    snippets = [
        "text",
        "&amp; &#x80; &#0; &NotEqualTilde;",
        "e\u0301\x1c x",
        "<",
        "</",
        "<!",
        "<!-->a",
        "<!--->a",
        "<!--a--!>b",
        "<![CDATA[text]]>a",
        "<!doctype html>a",
        "<?x>a",
        '<a x="&amp;">x</a>',
        '<a x="<main>">t</a>',
        "<main></main>tail",
        "<main>&#0;</main>tail",
        "<main>&#x0;</main>tail",
        "<main> </main>tail",
        "<b / / >x",
        '<a x="unfinished',
        "</b unfinished",
        "<a><b>x</b></a>",
        "</123>abc",
        "<script>hidden</script>shown",
        "<script/>shown",
        "<xmp>&amp;<main>literal</xmp>after",
        "<textarea>&amp;<main>literal</textarea>after",
        "<plaintext>a<main>b",
        "<main><svg>x</svg>y</main>tail",
    ]
    rng = random.Random(20261023)
    tags = [
        "main",
        "script",
        "style",
        "noscript",
        "template",
        "svg",
        "div",
        "p",
        "title",
        "textarea",
        "xmp",
        "iframe",
        "noembed",
        "noframes",
        "plaintext",
        "a",
    ]
    units = (
        snippets
        + ["<" + t + ">" for t in tags]
        + ["</" + t + ">" for t in tags]
        + ["<" + t + "/>" for t in tags]
    )
    cases = snippets + ["".join(rng.choices(units, k=rng.randrange(1, 12))) for _ in range(3500)]
    for markup in cases:
        body = markup.encode()
        try:
            expected = original["readable_text"](body, "utf-8")
        except Exception as exc:
            expected = {"error": str(exc)}
        check("text", {"body": list(body), "charset": "utf-8"}, expected)
    for charset in [
        None,
        "",
        "utf-8",
        "ascii",
        "latin-1",
        "iso-8859-1",
        "windows-1252",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "utf-32",
        "utf-8-sig",
        "shift_jis",
        "gb18030",
        "big5",
        "koi8-r",
        "made-up",
    ]:
        for body in [
            b"",
            b"<main>A\x80\xff</main>",
            bytes(range(256)),
            b"\xff\xfeA\x00B\x00",
            b"\xef\xbb\xbfhello",
        ]:
            try:
                expected = original["readable_text"](body, charset)
            except Exception as exc:
                expected = {"error": str(exc)}
            if charset in ["gb18030", "made-up"]:
                try:
                    actual = rpc("text", body=list(body), charset=charset)
                except ValueError as exc:
                    assert str(exc).startswith("Unqualified source charset ")
                    refusals.append({"charset": charset, "bytes": len(body)})
                else:
                    failures.append({"unexpected_charset_acceptance": charset, "actual": actual})
            else:
                check("text", {"body": list(body), "charset": charset}, expected)
    for charset in [
        "utf-8",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "utf-32",
        "utf-32-le",
        "utf-32-be",
    ]:
        for _ in range(700):
            body = rng.randbytes(rng.randrange(0, 90))
            expected = original["readable_text"](body, charset)
            check("text", {"body": list(body), "charset": charset}, expected)
    for markup in [
        "outside<main>&#11;</main>tail",
        "outside<main>&#xB;</main>tail",
        '<a x="&#' + ("9" * 4301) + ';">text',
    ]:
        try:
            expected = original["readable_text"](markup.encode(), "utf-8")
        except Exception as exc:
            expected = {"error": str(exc)}
        check("text", {"body": list(markup.encode()), "charset": "utf-8"}, expected)
    dates = [
        "",
        "2026-06-29T13:18:58Z",
        "Tue, 15 Sep 2026 12:58:04 GMT",
        "Mon, 01 Sep 2026 12:58:04 GMT",
        "2026-1-2",
        "2026-01-02",
        "20260102",
        "2026-W01",
        "2026W01",
        "2026-W01-1",
        "2026W011",
        "2026-02-29",
        "2024-02-29",
    ]
    for date in ["2026-01-02", "20260102", "2026-W01-1", "2026W011"]:
        for sep in ["T", " ", "x", "\u2603"]:
            for time in [
                "12",
                "1230",
                "12:30",
                "12:30:59",
                "123059",
                "12:30:59.123",
                "12:30:59,123",
                "25:00",
                "12:30:60",
                "12.5",
                "12:30+10",
                "12:30:59+10:30",
                "12:30:59+99:00",
            ]:
                dates.append(date + sep + time)
    dates += [
        "1 Jan 26 12:30 GMT",
        "1 Jan 26",
        "Fri Jan 2 12:30:00 2026",
        "15-Sep-2026 12:30 GMT",
        "15 Sep 2026 12.30.20 GMT",
        "15 Sep 2026 12:30 GMT (x)",
    ]
    for text in dates:
        check("date", {"text": text}, original["iso_day"](text))
    edges = [
        "١ Jan ٢٠٢٦ ١٢:٣٠ GMT",
        "1\x1cJan\x1c2026\x1c12:30\x1cGMT",
        "1 Jan 2026 12:30 +999999999999999999999999999",
        "1 Jan 2026,, 12:30 GMT",
        "1 Jan 2026 12:30,, GMT",
        "1 Jan 三 12:30 2026",
        "1 Jan Ⅻ 12:30 2026",
        "1 Jan ² 12:30 2026",
        "1 Jan +2_026 +1_2:3_0 GMT",
        "1 Jan 2026 12:30 +23_00",
    ]
    zeroes = [chr(n) for n in range(0x110000) if unicodedata.decimal(chr(n), None) == 0]
    for zero in zeroes:
        for pattern in [
            "1 Jan 2026 12:30 GMT",
            "1 Jan 2026 12:30 +2300",
            "1 Jan 2026 12:30 +2400",
            "1 Jan 2026 12:30 -0000",
            "1 Jan 2026 12:30 +9999",
        ]:
            edges.append(
                "".join(
                    chr(ord(zero) + int(c)) if c.isascii() and c.isdecimal() else c for c in pattern
                )
            )
    for text in edges:
        try:
            expected = original["iso_day"](text)
        except OverflowError as exc:
            # Python 3.14.4 leaks this exception; 3.14.8 returns an empty date.
            # Record the exact older-runtime difference and require 3.14.8's result.
            assert text == "1 Jan 2026 12:30 +999999999999999999999999999"
            refusals.append(
                {"op": "date", "python_exception": type(exc).__name__, "native": ""}
            )
            expected = ""
        check("date", {"text": text}, expected)
    for digits in [4299, 4300, 4301]:
        number = "0" * (digits - 1) + "1"
        for text in [
            f"{number} Jan 2026 12:30 GMT",
            f"1 Jan {number} 12:30 GMT",
            f"1 Jan 2026 12:30 +{number}",
        ]:
            check("date", {"text": text}, original["iso_day"](text))
    for _ in range(1600):
        year = rng.randrange(0, 10001)
        month = rng.randrange(0, 15)
        day = rng.randrange(0, 35)
        h, m, sec = (rng.randrange(0, 68) for _ in range(3))
        text = f"{year:04}-{month:02}-{day:02}{rng.choice(['T', ' ', 'x'])}{h:02}:{m:02}:{sec:02}{rng.choice(['', 'Z', '+10:30', '+24:00', '.1234567'])}"
        check("date", {"text": text}, original["iso_day"](text))
    # The production Python patterns search bytes before decoding the capture.
    # Wide digits and multibyte whitespace must obey the 40-byte limit.
    published_dates = [
        "".join(
            chr(ord(zero) + int(c)) if c.isascii() and c.isdecimal() else c
            for c in "1 Jan 2026 12:30 GMT"
        )
        for zero in zeroes
    ] + ["2026-01-02" + padding * n for padding in [" ", "\u00a0"] for n in range(32)]
    for date in published_dates:
        for markup in [
            f'"dateModified":"{date}"',
            f'<meta name="DCTERMS.modified" content="{date}">',
            f'<meta content="{date}" name="DCTERMS.modified">',
        ]:
            body = b"\xff" + markup.encode() + b"\x80"
            for last in [None, "2026-01-01"]:
                check(
                    "upstream",
                    {"body": list(body), "last": last, "served": None},
                    original["upstream_last_modified"](body, last, None),
                )
    for key in ["dateModifİed", "dateModıfied", "dateModified"]:
        body = f'<main>Unchanged content</main><script>{{"{key}":"2020-01-01"}}</script>'.encode()
        last, served = "2026-10-20", "2026-10-23"
        expected=original["upstream_last_modified"](body,last,served)
        check("upstream", {"body":list(body),"last":last,"served":served}, expected)
    for date in ["0000-01-01","0001-01-01","9999-12-31","10000-01-01","2026-99-01"," 2026-01-01"]:
        record={"next_review":date}
        check("review_date",{"record":record},original["review_date"](record))
    from urllib.parse import urljoin

    for base in [
        "https://www.ato.gov.au/a/b?x#z",
        "https://www.ato.gov.au",
        "https://www.ato.gov.au/a//b/",
    ]:
        for ref in [
            "",
            "a",
            "../c",
            "./",
            "../../",
            "/x//y",
            "//www.ato.gov.au/a",
            "///x",
            "?a",
            "#a",
            "https:foo",
            "HTTPS://www.ato.gov.au",
            "a//b",
            "a/../b",
            "a;b",
            ";params",
            "\t /x\n",
        ]:
            check("join", {"base": base, "reference": ref}, urljoin(base, ref))
    from email.message import Message

    for kind in [
        "text/html",
        "TEXT/HTML",
        "application/xhtml+xml",
        "text/plain",
        "invalid",
        "",
        "text / html",
        "text/html/invalid",
    ]:
        for params in [
            "",
            ";charset=utf-8",
            '; CHARSET = "utf-8"',
            ';charset="utf-8; x"',
            ";charset=<utf-8>",
            ";charset='utf-8'",
            ';charset="utf-8";charset=ascii',
            ';x="a;b";charset=latin-1',
            ';charset="u\\"tf8"',
            ";charset=é",
            ";charset",
            ';charset="utf-8',
            ';x=";charset=ascii',
            ';charset="utf-8\\\\"',
        ]:
            value = kind + params
            header = Message()
            header["Content-Type"] = value
            check(
                "headers",
                {"text": value},
                (header.get_content_type(), header.get_content_charset()),
            )
    import tempfile

    with tempfile.TemporaryDirectory() as temp:
        skills = Path(temp) / "skills"
        directory = skills / "example"
        directory.mkdir(parents=True)
        path = directory / "sources.json"
        payload = {
            "skill": "example",
            "sources": [
                {
                    "url": "https://example.test/é",
                    "fact": "fixture",
                    "checked_at": "2026-10-01",
                    "z": "𝄞",
                    "nested": {"b": 2, "a": 1},
                }
            ],
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        rpc("dump", path=path, skills=skills, record=payload)
        expected = (
            (json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
            .replace("\n", os.linesep)
            .encode()
        )
        assert path.read_bytes() == expected, (
            "native JSON dump changed insertion order, encoding or newlines"
        )
    (E / "differential.json").write_text(
        json.dumps(
            {"counts": counts, "refusals": refusals, "failures": failures},
            indent=2,
            ensure_ascii=True,
        )
        + "\n"
    )
    print(
        json.dumps(
            {
                "counts": counts,
                "refusals": len(refusals),
                "failures": len(failures),
                "first": [
                    {
                        **x,
                        "args": {
                            k: (v if k != "body" else str(v[:20]))
                            for k, v in x.get("args", {}).items()
                        },
                    }
                    for x in failures[:3]
                ],
            }
        )
    )
    return not failures


def cli_cases():
    import tempfile

    cases = []

    def run(args, expected):
        result = subprocess.run(
            [str(arguments.binary), "source-refresh", *map(str, args)],
            capture_output=True,
            timeout=20,
        )
        assert result.returncode == expected, (args, result.returncode, result.stderr)
        cases.append(
            {
                "args": list(map(str, args)),
                "exit": expected,
                "stdout": result.stdout.decode(),
                "stderr": result.stderr.decode(),
            }
        )
        return result

    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp)
        directory = root / ".claude/skills/example"
        directory.mkdir(parents=True)
        (directory / "SKILL.md").write_text("fixture")
        today = datetime.date.today()
        due = (today + datetime.timedelta(days=1)).isoformat()
        payload = {
            "skill": "example",
            "sources": [
                {
                    "url": "https://example.test/fixture",
                    "title": "Fixture",
                    "checked_at": today.isoformat(),
                    "fact": "Fabricated fact",
                    "manual_review": {"cadence": "monthly", "next_review": due},
                }
            ],
        }
        index = directory / "sources.json"
        index.write_text(json.dumps(payload))
        before = index.read_bytes()
        report = root / "report.md"
        report.write_text("old content")
        result = run(["--root", root, "--skill", "example", "--preflight", "--report", report], 0)
        assert (
            "READY_MANUAL" in result.stdout.decode()
            and report.read_bytes() + os.linesep.encode() == result.stdout
        )
        assert index.read_bytes() == before
        run(["--root", root, "--preflight"], 2)
        run(["--root", root, "--preflight", "--skill", "example", "--write"], 2)
        run(["--root", root, "--skill", "absent"], 1)
        result = run(["--root", root, "--check", "--spacing", "0", "--report", report], 0)
        assert f"- scheduled (reviewed by hand, next review {due}): 1" in result.stdout.decode()
        payload["sources"][0]["manual_review"]["next_review"] = (
            today - datetime.timedelta(days=1)
        ).isoformat()
        index.write_text(json.dumps(payload))
        run(["--root", root, "--check", "--spacing", "0"], 2)
        run(["--root", root, "--spacing", "wrong"], 2)
        run(["--help"], 0)
        payload["sources"][0]["manual_review"]["next_review"] = due
        payload["sources"][0]["checked_at"] = "0000-01-01"
        index.write_text(json.dumps(payload))
        result=run(["--root",root,"--skill","example","--preflight"],2)
        assert "malformed" in result.stdout.decode() and "READY_MANUAL" not in result.stdout.decode()
        payload["sources"][0]["checked_at"]=today.isoformat()
        payload["sources"][0]["review_required_since"]="0000-01-01"
        payload["sources"][0]["reviewed_content"]={"checked_at":today.isoformat(),"source_last_modified":""}
        index.write_text(json.dumps(payload))
        run(["--root",root,"--skill","example","--preflight"],2)
        del payload["sources"][0]["review_required_since"]
        del payload["sources"][0]["reviewed_content"]
        index.write_text(json.dumps(payload))
        before=index.read_bytes()
        bad=root/".claude/skills/z-invalid/sources.json"
        bad.parent.mkdir()
        bad.write_text("[]")
        for args in [["--check"],["--write"],["--skill","example","--preflight"]]:
            run(["--root",root,*args],1)
            assert index.read_bytes()==before
        bad.unlink()
        bad.symlink_to(root/"missing.json")
        run(["--root",root,"--check"],1)
        assert index.read_bytes()==before
    return cases


try:
    E.mkdir(parents=True, exist_ok=True)
    compared = differential()
    replayed = replay()
    cli = cli_cases()
    differential_result = json.loads((E / "differential.json").read_text())
    original_result = json.loads((E / "original-replay.json").read_text())
    arguments.record.write_text(
        json.dumps(
            {
                "differential": differential_result,
                "original_replay": original_result,
                "cli": cli,
                "html_oracle": {
                    "version": "Python 3.14.8",
                    "sha256": oracle_sha,
                    "runtime": sys.version,
                    "dependencies_hash_checked": True,
                },
            },
            indent=2,
        )
        + "\n"
    )
finally:
    child.stdin.close()
    child.wait(timeout=10)
raise SystemExit(0 if compared and replayed else 1)
