from __future__ import annotations

import argparse
import json
from collections.abc import Callable, Mapping, Sequence
import subprocess
import time
from urllib.parse import urlparse


class ReleaseLookupError(RuntimeError):
    """Raised when the release created by GitHub cannot be safely identified."""


class IneligibleReleaseError(ReleaseLookupError):
    """Raised when the matched release is no longer a publishable draft."""


class UnexpectedReleaseTagError(ReleaseLookupError):
    """Raised when the matched release settles on an unexpected tag."""


def _is_transient_listing_error(error: Exception) -> bool:
    """Return whether a release-listing failure can safely be retried."""
    if isinstance(error, json.JSONDecodeError):
        return True
    if not isinstance(error, subprocess.CalledProcessError):
        return False

    output = "\n".join(
        str(value)
        for value in (error.stdout, error.stderr)
        if value is not None
    ).casefold()
    transient_statuses = (
        "http 408",
        "http 429",
        "http 500",
        "http 502",
        "http 503",
        "http 504",
    )
    transient_messages = (
        "connection reset",
        "network is unreachable",
        "temporarily unavailable",
        "temporary failure",
        "timed out",
        "timeout",
    )
    return any(status in output for status in transient_statuses) or any(
        message in output for message in transient_messages
    )


def _release_id_in_url(created_url: str) -> str | None:
    path_parts = [part for part in urlparse(created_url).path.split("/") if part]
    if len(path_parts) >= 2 and path_parts[-2] == "releases" and path_parts[-1].isdigit():
        return path_parts[-1]
    return None


def select_created_draft_release_id(
    releases: Sequence[Mapping[str, object]],
    created_url: str,
) -> str:
    """Return the ID of the exact eligible draft identified by create output."""
    normalized_url = created_url.strip()
    if not normalized_url:
        raise ReleaseLookupError("gh release create did not return a release URL")

    created_id = _release_id_in_url(normalized_url)
    matches = [
        release
        for release in releases
        if (
            str(release.get("id", "")) == created_id
            if created_id is not None
            else normalized_url
            in {str(release.get("url", "")), str(release.get("html_url", ""))}
        )
    ]
    if not matches:
        raise ReleaseLookupError("created release is not visible in the paginated release listing")
    if len(matches) != 1:
        raise ReleaseLookupError("created release URL matched more than one release")

    release = matches[0]
    if release.get("draft") is not True or release.get("prerelease") is not False:
        raise IneligibleReleaseError("created release is not an eligible draft")

    release_id = str(release.get("id", ""))
    if not release_id.isdigit():
        raise ReleaseLookupError("created release did not contain a numeric ID")
    return release_id


def _release_with_id(
    releases: Sequence[Mapping[str, object]],
    release_id: str,
) -> Mapping[str, object]:
    matches = [
        release
        for release in releases
        if str(release.get("id", "")) == release_id
    ]
    if not matches:
        raise ReleaseLookupError("created release ID is not visible in the paginated release listing")
    if len(matches) != 1:
        raise ReleaseLookupError("created release ID matched more than one release")

    release = matches[0]
    if release.get("draft") is not True or release.get("prerelease") is not False:
        raise IneligibleReleaseError("created release is not an eligible draft")
    return release


def find_created_draft_release_id(
    list_releases: Callable[[], Sequence[Mapping[str, object]]],
    created_url: str,
    *,
    expected_tag: str,
    attempts: int,
    delay_seconds: float,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Retry listings until the exact created draft settles on the expected tag."""
    if attempts < 1:
        raise ValueError("attempts must be at least one")

    release_id: str | None = None
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            releases = list_releases()
            if release_id is None:
                release_id = select_created_draft_release_id(releases, created_url)

            release = _release_with_id(releases, release_id)
            actual_tag = release.get("tag_name")
            if actual_tag == expected_tag:
                return release_id
            if isinstance(actual_tag, str) and actual_tag.startswith("untagged-"):
                raise ReleaseLookupError("created release tag has not settled")
            raise UnexpectedReleaseTagError(
                f"created release has unexpected tag {actual_tag!r}; expected {expected_tag!r}",
            )
        except (
            ReleaseLookupError,
            json.JSONDecodeError,
            subprocess.CalledProcessError,
        ) as error:
            if isinstance(error, (IneligibleReleaseError, UnexpectedReleaseTagError)):
                raise
            if (
                not isinstance(error, ReleaseLookupError)
                and not _is_transient_listing_error(error)
            ):
                raise
            last_error = error
        if attempt < attempts - 1:
            sleep(delay_seconds)

    raise ReleaseLookupError(
        f"could not identify the draft created by gh release create after {attempts} attempts: {last_error}",
    )


def _list_paginated_releases(repository: str) -> list[Mapping[str, object]]:
    result = subprocess.run(
        [
            "gh",
            "api",
            "--paginate",
            "--slurp",
            "-H",
            "X-GitHub-Api-Version: 2026-03-10",
            f"repos/{repository}/releases?per_page=100",
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    pages = json.loads(result.stdout)
    if not isinstance(pages, list) or not all(isinstance(page, list) for page in pages):
        raise ReleaseLookupError("GitHub returned an invalid paginated release response")
    return [release for page in pages for release in page if isinstance(release, dict)]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Find the exact draft release identified by gh release create output.",
    )
    parser.add_argument("--repository", required=True)
    parser.add_argument("--created-url", required=True)
    parser.add_argument("--expected-tag", required=True)
    parser.add_argument("--attempts", type=int, default=5)
    parser.add_argument("--delay-seconds", type=float, default=5)
    arguments = parser.parse_args()

    release_id = find_created_draft_release_id(
        lambda: _list_paginated_releases(arguments.repository),
        arguments.created_url,
        expected_tag=arguments.expected_tag,
        attempts=arguments.attempts,
        delay_seconds=arguments.delay_seconds,
    )
    print(release_id)


if __name__ == "__main__":
    main()
