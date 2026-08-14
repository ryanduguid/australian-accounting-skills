"""Build release archives with explicit cross-platform Git settings."""

from __future__ import annotations

import argparse
import os
from pathlib import Path, PurePosixPath
import subprocess
from typing import Sequence

_ARCHIVE_FORMATS = (("zip", ".zip"), ("tar.gz", ".tar.gz"))
_GIT_CONFIG = (
    "-c",
    "core.autocrlf=false",
    "-c",
    "core.eol=lf",
)


def build_release_archives(
    *,
    commit: str,
    prefix: str,
    output_base: Path,
    cwd: Path | None = None,
) -> tuple[Path, Path]:
    """Build ZIP and tar.gz archives with stable text and time metadata."""

    prefix_parts = PurePosixPath(prefix).parts
    if (
        not prefix.endswith("/")
        or prefix.startswith("/")
        or ".." in prefix_parts
    ):
        raise ValueError("prefix must be a safe relative POSIX path ending in '/'")

    output_base = Path(output_base)
    outputs = tuple(Path(f"{output_base}{suffix}") for _, suffix in _ARCHIVE_FORMATS)
    for output in outputs:
        if output.exists():
            raise FileExistsError(f"refusing to overwrite existing archive: {output}")
    output_base.parent.mkdir(parents=True, exist_ok=True)

    environment = os.environ.copy()
    environment["TZ"] = "UTC"
    repository = Path.cwd() if cwd is None else Path(cwd)

    for (archive_format, _), output in zip(_ARCHIVE_FORMATS, outputs, strict=True):
        subprocess.run(
            (
                "git",
                *_GIT_CONFIG,
                "archive",
                f"--format={archive_format}",
                f"--prefix={prefix}",
                f"--output={output.resolve()}",
                commit,
            ),
            cwd=repository,
            env=environment,
            check=True,
        )

    return outputs


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build reproducible Git source archives.",
    )
    parser.add_argument("--commit", required=True)
    parser.add_argument("--prefix", required=True)
    parser.add_argument("--output-base", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    build_release_archives(
        commit=args.commit,
        prefix=args.prefix,
        output_base=args.output_base,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
