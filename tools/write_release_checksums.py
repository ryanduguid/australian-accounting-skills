"""Create and verify a release checksum manifest after an exact preflight."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import sys
from typing import Sequence


CHECKSUM_FILENAME = "SHA256SUMS"


class ReleaseAssetError(ValueError):
    """Raised when the candidate release asset set is unsafe or unexpected."""


def _asset_names(names: Sequence[str]) -> tuple[str, ...]:
    if not names:
        raise ReleaseAssetError("at least one release asset is required")

    ordered = tuple(sorted(names))
    if len(ordered) != len(set(ordered)):
        raise ReleaseAssetError("release asset names must be unique")
    for name in ordered:
        if (
            not name
            or name in {".", "..", CHECKSUM_FILENAME}
            or "/" in name
            or "\\" in name
            or Path(name).name != name
        ):
            raise ReleaseAssetError(f"unsafe release asset name: {name!r}")
    return ordered


def _inventory(directory: Path) -> tuple[str, ...]:
    if not directory.is_dir():
        raise ReleaseAssetError(f"release directory does not exist: {directory}")

    names: list[str] = []
    for entry in directory.iterdir():
        if entry.is_symlink() or not entry.is_file():
            raise ReleaseAssetError(
                f"release inventory contains a non-file: {entry.name}"
            )
        names.append(entry.name)
    return tuple(sorted(names))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for block in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(block)
    except OSError as error:
        raise ReleaseAssetError(
            f"cannot hash release asset {path.name}: {error}"
        ) from error
    return digest.hexdigest()


def _inventory_error(
    stage: str,
    expected: Sequence[str],
    actual: Sequence[str],
) -> ReleaseAssetError:
    return ReleaseAssetError(
        f"Unexpected {stage} release asset inventory. "
        f"Expected={list(expected)!r}; actual={list(actual)!r}"
    )


def verify_release_checksums(directory: Path, assets: Sequence[str]) -> None:
    """Verify the exact manifest text and every recorded asset digest."""

    directory = Path(directory)
    names = _asset_names(assets)
    manifest = directory / CHECKSUM_FILENAME
    expected_text = "".join(f"{_sha256(directory / name)}  {name}\n" for name in names)
    try:
        actual_text = manifest.read_bytes().decode("ascii")
    except (OSError, UnicodeError) as error:
        raise ReleaseAssetError(f"cannot read {CHECKSUM_FILENAME}: {error}") from error
    if actual_text != expected_text:
        raise ReleaseAssetError(
            f"{CHECKSUM_FILENAME} does not match the release assets"
        )


def write_release_checksums(directory: Path, assets: Sequence[str]) -> Path:
    """Validate assets, create the manifest once, then validate the final set."""

    directory = Path(directory)
    names = _asset_names(assets)
    before = _inventory(directory)
    if before != names:
        raise _inventory_error("pre-checksum", names, before)

    manifest = directory / CHECKSUM_FILENAME
    manifest_text = "".join(f"{_sha256(directory / name)}  {name}\n" for name in names)
    try:
        with manifest.open("x", encoding="ascii", newline="\n") as stream:
            stream.write(manifest_text)
    except FileExistsError as error:
        raise ReleaseAssetError(f"refusing to overwrite {CHECKSUM_FILENAME}") from error
    except OSError as error:
        raise ReleaseAssetError(
            f"cannot create {CHECKSUM_FILENAME}: {error}"
        ) from error

    expected_final = tuple(sorted((*names, CHECKSUM_FILENAME)))
    after = _inventory(directory)
    if after != expected_final:
        raise _inventory_error("post-checksum", expected_final, after)
    verify_release_checksums(directory, names)
    return manifest


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create SHA256SUMS after validating the exact release asset set.",
    )
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--asset", action="append", required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = write_release_checksums(args.directory, args.asset)
    except ReleaseAssetError as error:
        print(f"release asset validation failed: {error}", file=sys.stderr)
        return 1
    print(f"created and verified {manifest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
