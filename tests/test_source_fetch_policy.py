import io
import sys
import unittest
import urllib.error
from email.message import Message
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import source_fetch_policy as policy
import source_refresh

URL = "https://www.ato.gov.au/source"


class Response(io.BytesIO):
    def __init__(self, body=b"<main>Fabricated source</main>", url=URL, **headers):
        super().__init__(body)
        self.status = 200
        self.url = url
        self.headers = Message()
        self.headers["Content-Type"] = "text/html; charset=utf-8"
        for name, value in headers.items():
            self.headers[name.replace("_", "-")] = value
        self.read_sizes = []

    def geturl(self):
        return self.url

    def read(self, size=-1):
        self.read_sizes.append(size)
        return super().read(size)


def redirect(url, location):
    headers = Message()
    headers["Location"] = location
    return urllib.error.HTTPError(url, 302, "redirect", headers, io.BytesIO())


class SourceFetchPolicyTests(unittest.TestCase):
    def fetch(self, responses):
        with mock.patch.object(source_refresh.urllib.request, "build_opener") as build, \
                mock.patch.object(source_refresh, "check_public_resolution"):
            build.return_value.open.side_effect = responses
            result = source_refresh.fetch(URL, tries=1, delay=0)
            return result, build.return_value.open.call_count

    def test_reviewed_index_hosts_and_url_rejections(self):
        for _, _, record in source_refresh.records(source_refresh.index_files()):
            policy.checked_url(str(record["url"]))
        for url in ["http://www.ato.gov.au/", "ftp://www.ato.gov.au/", "https:///empty",
                    "https://user@www.ato.gov.au/", "https://user:password@www.ato.gov.au/",
                    "https://127.0.0.1/", "https://[::1]/", "https://www.ato.gov.au:444/",
                    "https://www.ato.gov.au:bad/", "https://www.ato.gov.au./",
                    "https://unreviewed.test/", "https://例.test/", URL + "\n", URL + "\\evil"]:
            with self.subTest(url=url), self.assertRaises(policy.SourcePolicyError):
                policy.checked_url(url)
        self.assertEqual(policy.checked_url(URL + "#fact"), URL)

    def test_public_resolution_matrix_and_mixed_answers(self):
        for address in ["127.0.0.1", "10.0.0.1", "169.254.1.1", "100.64.0.1", "0.0.0.0",
                        "224.0.0.1", "::1", "fc00::1", "fe80::1", "ff02::1", "192.0.2.1"]:
            with self.subTest(address=address), mock.patch.object(policy.socket, "getaddrinfo",
                    return_value=[(0, 0, 0, "", ("8.8.8.8", 443)), (0, 0, 0, "", (address, 443))]), \
                    self.assertRaises(policy.SourcePolicyError):
                policy.check_public_resolution(URL)
        with mock.patch.object(policy.socket, "getaddrinfo", return_value=[(0, 0, 0, "", ("8.8.8.8", 443))]):
            policy.check_public_resolution(URL)
        with mock.patch.object(policy.socket, "getaddrinfo", return_value=[]), self.assertRaises(OSError):
            policy.check_public_resolution(URL)

    def test_exact_ceiling_and_overflow_never_digest_a_prefix(self):
        for size, accepted in [(policy.MAX_RESPONSE_BYTES, True), (policy.MAX_RESPONSE_BYTES + 1, False)]:
            response = Response(b"x" * size)
            if accepted:
                self.assertEqual(len(policy.bounded_body(response)), size)
            else:
                with self.assertRaises(policy.SourcePolicyError):
                    policy.bounded_body(response)
            self.assertTrue(all(0 < n <= policy.READ_CHUNK_BYTES for n in response.read_sizes))
        for headers in [{"Content_Length": str(policy.MAX_RESPONSE_BYTES + 1)},
                        {"Content_Encoding": "gzip"}, {"Content_Length": "broken"},
                        {"Content_Length": "9" * 5000}]:
            result, count = self.fetch([Response(**headers)])
            self.assertEqual((result.digest, count), ("", 1))
            self.assertEqual(source_refresh.classify({}, result)[0], source_refresh.UNREADABLE)
        with mock.patch.object(source_refresh, "body_digest") as digest:
            result, _ = self.fetch([Response(b"x" * (policy.MAX_RESPONSE_BYTES + 1), Content_Length="1")])
            self.assertFalse(result.readable)
            digest.assert_not_called()

    def test_redirect_limit_loop_and_cross_host_rejected_before_second_fetch(self):
        result, count = self.fetch([redirect(URL, "/next"), Response(url="https://www.ato.gov.au/next")])
        self.assertTrue(result.readable)
        self.assertEqual(count, 2)
        result, count = self.fetch([redirect(URL, "/a"), redirect(URL, "/b"), redirect(URL, "/c"),
                                   Response(url="https://www.ato.gov.au/c")])
        self.assertTrue(result.readable)
        self.assertEqual(count, 4)
        for target in [URL, "http://www.ato.gov.au/", "https://www.tpb.gov.au/",
                       "https://127.0.0.1/", "https://user@www.ato.gov.au/", "https://www.ato.gov.au:444/"]:
            result, count = self.fetch([redirect(URL, target)])
            self.assertFalse(result.readable)
            self.assertEqual(count, 1)
        result, count = self.fetch([redirect(URL, "/a"), redirect(URL, "/b"),
                                   redirect(URL, "/c"), redirect(URL, "/d")])
        self.assertFalse(result.readable)
        self.assertEqual(count, 4)

    def test_proxy_disabled_and_human_fields_preserved_on_policy_failure(self):
        with mock.patch.dict("os.environ", {"HTTPS_PROXY": "http://127.0.0.1:4444"}), \
                mock.patch.object(source_refresh.urllib.request, "build_opener") as build:
            result = source_refresh.fetch("http://private.test/", tries=1)
            self.assertEqual(build.call_args.args[0].proxies, {})
            build.return_value.open.assert_not_called()
        record: dict[str, object] = {"checked_at": "2026-01-01", "fact": "human", "reverify_by": "2027-01-01",
                  "sha256": "previous", "content_url": URL}
        before = {key: record[key] for key in ("checked_at", "fact", "reverify_by")}
        source_refresh.apply_fetch(record, result, "2026-10-03")
        self.assertEqual({key: record[key] for key in before}, before)
        self.assertEqual(record["sha256"], "previous")
