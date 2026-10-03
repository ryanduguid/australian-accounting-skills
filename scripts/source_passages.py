"""Capture and compare bounded passages from one indexed public source."""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urldefrag

import source_refresh
from source_fetch_policy import checked_url

MAX_TEXT_CHARS = 32768
MAX_DIFF_LINES = 60
MAX_LINE_CHARS = 240
MAX_TEXT_LINES = 400


def indexed_url(url: str) -> str:
    target = checked_url(url)
    indexed = {urldefrag(str(record["url"])).url for _, _, record in
               source_refresh.records(source_refresh.index_files())}
    if target not in indexed:
        raise ValueError("Only exact URLs already present in the public index may be captured.")
    return target


def snapshot(url: str) -> dict:
    target = indexed_url(url)
    fetched = source_refresh.fetch(target, include_text=True)
    return {"url": target, "final_url": fetched.final_url, "http_status": fetched.status,
            "available": fetched.readable and bool(fetched.text), "error": fetched.error,
            "source_digest": fetched.digest, "digest_kind": fetched.kind,
            "text": fetched.text, "text_truncated": fetched.text_truncated,
            "text_sha256": hashlib.sha256(fetched.text.encode()).hexdigest(),
            "boundary": "Bounded source text only; no verification of current applicability or human review."}


def load_snapshot(path: Path) -> dict:
    if path.stat().st_size > 1024 * 1024:
        raise ValueError("Snapshot file exceeds 1 MiB.")
    # The local CLI accepts an operator-selected snapshot and checks its size and contents.
    value = json.loads(path.read_text(encoding="utf-8"))  # NOSONAR
    if not isinstance(value, dict) or not isinstance(value.get("text"), str):
        raise ValueError("Malformed passage snapshot.")
    if len(value["text"]) > MAX_TEXT_CHARS or hashlib.sha256(value["text"].encode()).hexdigest() != value.get("text_sha256"):
        raise ValueError("Snapshot text is oversized or does not agree with its digest.")
    if not isinstance(value.get("url"), str) or not isinstance(value.get("final_url"), str):
        raise ValueError("Malformed snapshot URL.")
    indexed_url(value["url"])
    # Snapshot flags must be actual booleans, not integers or truthy values.
    if (type(value.get("available")) is not bool or type(value.get("text_truncated")) is not bool  # pylint: disable=unidiomatic-typecheck
            or not isinstance(value.get("source_digest"), str)
            or (value["available"] and not re.fullmatch(r"[0-9a-f]{64}", value["source_digest"]))):
        raise ValueError("Malformed snapshot availability or source digest.")
    checked_url(value.get("final_url", ""))
    return value


def compare(before: dict, after: dict) -> dict:
    boundary = "Text comparison only. A person must assess any legal, tax or accounting implication."
    if before.get("url") != after.get("url") or not before.get("available") or not after.get("available"):
        return {"status": "unavailable", "reason": "Both readable snapshots of the same indexed URL are required.",
                "boundary": boundary}
    same = (before["source_digest"] == after["source_digest"] and before["final_url"] == after["final_url"]
            and before["text"] == after["text"])
    old_lines, new_lines = before["text"].splitlines(), after["text"].splitlines()
    diff = list(difflib.unified_diff(old_lines[:MAX_TEXT_LINES], new_lines[:MAX_TEXT_LINES],
                                    fromfile="before", tofile="after", lineterm="", n=2))
    bounded = [line[:MAX_LINE_CHARS] for line in diff[:MAX_DIFF_LINES]]
    return {"status": "same" if same else "different", "url": after["url"],
            "before_digest": before["source_digest"], "after_digest": after["source_digest"],
            "before_final_url": before["final_url"], "after_final_url": after["final_url"],
            "passage_diff": bounded,
            "comparison_truncated": before["text_truncated"] or after["text_truncated"]
            or len(old_lines) > MAX_TEXT_LINES or len(new_lines) > MAX_TEXT_LINES
            or len(diff) > MAX_DIFF_LINES or any(len(line) > MAX_LINE_CHARS for line in diff),
            "boundary": boundary}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="mode", required=True)
    capture = commands.add_parser("snapshot")
    capture.add_argument("--url", required=True)
    comparison = commands.add_parser("compare")
    comparison.add_argument("--before", type=Path, required=True)
    comparison.add_argument("--after", type=Path, required=True)
    for command in (capture, comparison):
        command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    output = args.output.resolve()
    if output.is_relative_to(source_refresh.REPOSITORY) or output.exists():
        parser.error("Choose a new output file outside the repository.")
    try:
        result = snapshot(args.url) if args.mode == "snapshot" else compare(
            load_snapshot(args.before), load_snapshot(args.after))
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(result, indent=2, ensure_ascii=True) + "\n")
        return 2 if result.get("status") == "unavailable" or result.get("available") is False else 0
    except (OSError, ValueError, UnicodeError) as error:
        print(json.dumps({"status": "unavailable", "error": str(error)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
