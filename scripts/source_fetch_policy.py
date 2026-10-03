"""Bound unauthenticated retrieval to independently reviewed public hosts."""
from __future__ import annotations

import ipaddress
import socket
import urllib.request
from urllib.parse import urldefrag, urlsplit

MAX_RESPONSE_BYTES = 8 * 1024 * 1024
READ_CHUNK_BYTES = 64 * 1024
MAX_REDIRECTS = 3
# Reviewed against the public index on 3 October 2026. An index cannot authorise itself.
APPROVED_HOSTS = frozenset({
    "www.austrac.gov.au", "www.legislation.gov.au", "www.ato.gov.au", "www.asic.gov.au",
    "apesb.org.au", "www.tpb.gov.au", "standards.aasb.gov.au", "www.revenue.nsw.gov.au",
    "community.ato.gov.au", "www.fairwork.gov.au", "www.sro.vic.gov.au", "qro.qld.gov.au",
    "www.wa.gov.au", "revenuesa.sa.gov.au", "www.sro.tas.gov.au", "www.revenue.act.gov.au",
    "treasury.nt.gov.au", "business.gov.au", "www.hcourt.gov.au", "softwaredevelopers.ato.gov.au",
    "coallsl.com.au", "assets.ctfassets.net", "www.cyber.gov.au", "legislation.nsw.gov.au",
    "www.caselaw.nsw.gov.au", "www.legislation.qld.gov.au", "github.com",
})
APPROVED_REDIRECT_EDGES: frozenset[tuple[str, str]] = frozenset()


class SourcePolicyError(ValueError):
    """The source cannot be read under the reviewed retrieval policy."""


def checked_url(url: str) -> str:
    if any(ord(char) <= 32 or ord(char) == 127 for char in url) or "\\" in url:
        raise SourcePolicyError("URL contains whitespace, controls or a backslash.")
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
        port = parts.port
    except ValueError as error:
        raise SourcePolicyError("Malformed URL or port.") from error
    if (parts.scheme != "https" or not host.isascii() or host not in APPROVED_HOSTS
            or parts.username is not None or parts.password is not None or port not in (None, 443)):
        raise SourcePolicyError("Unsupported destination; an exact reviewed HTTPS host is required.")
    return urldefrag(url).url


def check_public_resolution(url: str) -> None:
    """Reject non-public answers. urllib resolves again; this is not connection pinning."""
    host = urlsplit(url).hostname
    addresses = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    if not addresses:
        raise OSError("Source hostname returned no addresses.")
    for item in addresses:
        address = ipaddress.ip_address(item[4][0])
        if not address.is_global or address.is_multicast:
            raise SourcePolicyError("Source hostname resolves to a non-public address.")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def bounded_body(response) -> bytes:
    encoding = response.headers.get("Content-Encoding", "identity").strip().lower()
    if encoding not in ("", "identity"):
        raise SourcePolicyError("Encoded response is unsupported.")
    length = response.headers.get("Content-Length")
    if length is not None:
        if not length.isascii() or not length.isdecimal():
            raise SourcePolicyError("Malformed Content-Length.")
        normalised = length.lstrip("0") or "0"
        if len(normalised) > len(str(MAX_RESPONSE_BYTES)) or int(normalised) > MAX_RESPONSE_BYTES:
            raise SourcePolicyError("Response exceeds the 8 MiB ceiling.")
    body = bytearray()
    while len(body) <= MAX_RESPONSE_BYTES:
        block = response.read(min(READ_CHUNK_BYTES, MAX_RESPONSE_BYTES + 1 - len(body)))
        if not block:
            return bytes(body)
        body.extend(block)
    raise SourcePolicyError("Response exceeds the 8 MiB ceiling; no prefix is digested.")
