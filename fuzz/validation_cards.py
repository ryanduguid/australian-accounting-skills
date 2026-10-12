"""Fuzz the validation card front-matter parser and sensitive-content scan."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import validate_validation as validator  # noqa: E402

CARD_NAME = "fuzz-card.md"


def test_one_input(data: bytes) -> None:
    text = data.decode("utf-8", errors="replace")
    # Every safety pattern must finish on arbitrary text; a pattern that
    # backtracks without bound shows up here as a timeout.
    try:
        validator.check_sensitive_content(text)
    except validator.ValidationError:
        pass

    try:
        metadata, body = validator.parse_front_matter(text, CARD_NAME)
    except validator.ValidationError:
        return
    # Explicit raises, because python -O strips assert statements.
    if set(metadata) != validator.ALLOWED_METADATA:
        raise AssertionError(f"accepted front matter with fields {sorted(map(str, metadata))}")
    if metadata["id"] != Path(CARD_NAME).stem or metadata["synthetic"] is not True:
        raise AssertionError(f"accepted id {metadata['id']!r} or synthetic {metadata['synthetic']!r}")
    if not text.endswith(body):
        raise AssertionError("returned a body that is not the end of the card")


if __name__ == "__main__":
    import atheris

    atheris.instrument_all()
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()
