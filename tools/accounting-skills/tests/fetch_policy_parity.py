"""Compare native retrieval policy with the original using fabricated responses only."""
from __future__ import annotations

import argparse
import collections
import contextlib
import importlib.util
import io
import ipaddress
import json
import random
import subprocess
import sys
import unittest
from pathlib import Path
from typing import Any
from unittest import mock


def main():
    parser = argparse.ArgumentParser()
    for name in ('root', 'probe', 'record'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    sys.path.insert(0, str(root / 'scripts'))
    spec = importlib.util.spec_from_file_location('native_policy_original_tests', root / 'tests/test_source_fetch_policy.py')
    assert spec is not None and spec.loader is not None
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    policy, refresh = tests.policy, tests.source_refresh
    originals = {name: getattr(policy, name) for name in ('checked_url', 'check_public_resolution', 'bounded_body')}
    child = subprocess.Popen([str(args.probe.resolve())], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, text=True, encoding='utf-8')
    assert child.stdin is not None and child.stdout is not None
    request_stream, response_stream = child.stdin, child.stdout
    calls = collections.Counter()
    comparisons = collections.Counter()
    objects = []

    def call(op, **values):
        calls[op] += 1
        request_stream.write(json.dumps({'op': op, **values}) + '\n')
        request_stream.flush()
        line = response_stream.readline()
        assert line, ('probe exited', child.poll())
        return json.loads(line)

    def unwrap(result):
        if 'error' in result:
            if result['kind'] == 'io':
                raise OSError(result['error'])
            raise policy.SourcePolicyError(result['error'])
        return result['ok']

    def checked(url):
        return unwrap(call('url', url=url))

    def resolved(url):
        host = policy.urlsplit(url).hostname
        addresses = policy.socket.getaddrinfo(host, 443, type=policy.socket.SOCK_STREAM)
        return unwrap(call('addresses', addresses=[item[4][0] for item in addresses]))

    def native_body(response):
        data = response.getvalue()[response.tell():]
        if len(data) > 65536:
            assert not data or data.count(data[:1]) == len(data), 'large replay bodies must be uniform'
            pattern = list(data[:1])
        else:
            pattern = list(data)
        result = unwrap(call('body', size=len(data), pattern=pattern,
                             encoding=response.headers.get('Content-Encoding'),
                             length=response.headers.get('Content-Length')))
        for size in result['reads']:
            response.read(size)
        value = unwrap(result['result'])
        returned = data[:value['size']]
        assert value['counts'] == [returned.count(i) for i in range(256)]
        assert value['prefix'] == list(returned[:64]) and value['suffix'] == list(returned[-64:])
        return returned

    class Result(unittest.TextTestResult):
        def __init__(self, *values, **options):
            super().__init__(*values, **options)

        def startTest(self, test):
            self.before = calls.copy()
            super().startTest(test)

        def stopTest(self, test):
            objects.append({'id': test.id(), 'native_calls': dict(calls - self.before)})
            super().stopTest(test)

    def outcome(fn, *values) -> dict[str, Any]:
        try:
            return {'ok': fn(*values)}
        except (ValueError, OSError) as error:
            return {'error': str(error), 'kind': 'io' if isinstance(error, OSError) else 'policy'}

    def compare_url(url):
        expected = outcome(originals['checked_url'], url)
        actual = call('url', url=url)
        assert expected == actual, ('url', repr(url), expected, actual)
        comparisons['urls'] += 1

    try:
        constants = unwrap(call('constants'))
        assert set(constants['hosts']) == policy.APPROVED_HOSTS
        assert constants['edges'] == [] and constants['redirects'] == policy.MAX_REDIRECTS
        assert constants['automatic_redirects'] is False
        assert (constants['ceiling'], constants['chunk']) == (policy.MAX_RESPONSE_BYTES, policy.READ_CHUNK_BYTES)
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(policy.socket, 'getaddrinfo', side_effect=AssertionError('real DNS is forbidden')))
            for name, wrapper in {'checked_url': checked, 'check_public_resolution': resolved, 'bounded_body': native_body}.items():
                stack.enter_context(mock.patch.object(policy, name, wrapper))
                stack.enter_context(mock.patch.object(refresh, name, wrapper))
            suite = unittest.defaultTestLoader.loadTestsFromModule(tests)
            result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
            assert result.wasSuccessful(), 'original test replay failed'

        for _, _, record in refresh.records(refresh.index_files()):
            compare_url(str(record['url']))
        hosts = ['www.ato.gov.au', 'WWW.ATO.GOV.AU', 'www.ato.gov.au.', 'www.ato.gov.au.evil.test',
                 'user@www.ato.gov.au', 'user:pw@www.ato.gov.au', 'www.ato.gov.au@evil.test',
                 '[::1]', '[::ffff:8.8.8.8]', '[8.8.8.8]', '[v1.address]', '[vZ.address]',
                 '[::1]tail', '[::1%eth0]', '[::1%]', '[::1', '::1]', 'x[::1]', '例.test',
                 'www.ato.gov.au：443', 'www.ato.gov.au／evil', '', 'github.com']
        ports = ['', ':', ':443', ':00443', ':80', ':65536', ':-1', ':bad', ':４４３', ':00000']
        for scheme in ['https', 'HTTPS', 'http', 'ftp', '']:
            for host in hosts:
                for port in ports:
                    compare_url(scheme + '://' + host + port + '/a?b=c#fragment')
        for path in ['', '/', '/a?', '/a??', '/a?b?', '/a#b#c', '/é?q=日本', '/%2e%2e/a', '?#', '/a?#x']:
            for fragment in ['', '#', '#frag']:
                compare_url('HTTPS://WWW.ATO.GOV.AU:00443' + path + fragment)
        for char in [chr(n) for n in range(33)] + ['\x7f', '\\', '\u0085', '\u00a0', '\u2028']:
            compare_url('https://www.ato.gov.au/' + char)
        for digits in ['0' * 4300, '0' * 4301, '0' * 4297 + '443', '0' * 4298 + '443', '9' * 5000]:
            compare_url('https://www.ato.gov.au:' + digits + '/')
        for url in ['https://www.fairwor\u212a.gov.au/x#f',
                    'HTTPS://WWW.FAIRWOR\u212a.GOV.AU:00443/?#f',
                    'https://www.fairwor\u212a.gov.au:443/a?',
                    'https://www.fairwor\u212a.gov.au:443/a?x=#f']:
            compare_url(url)

        for authority in ['www.ato.gov.au:443:443', 'www.ato.gov.au:443:',
                          'www.ato.gov.au:bad:', '[::1]]:443',
                          'www.ato.gov.au\uff1a443@www.ato.gov.au', '[[::1]:443']:
            compare_url('https://' + authority + '/')

        addresses = set()
        for constants_class in (getattr(ipaddress.IPv4Address, '_constants'), getattr(ipaddress.IPv6Address, '_constants')):
            for name in ('_private_networks', '_private_networks_exceptions'):
                for network in getattr(constants_class, name):
                    for n in (int(network.network_address)-1, int(network.network_address),
                              int(network.network_address)+1, int(network.broadcast_address), int(network.broadcast_address)+1):
                        if 0 <= n < 2 ** network.max_prefixlen:
                            addresses.add(str(network._address_class(n)))
        for text in ['100.64.0.0/10', '224.0.0.0/4', 'ff00::/8']:
            network = ipaddress.ip_network(text)
            addresses.update(str(type(network.network_address)(n)) for n in (int(network.network_address)-1, int(network.network_address), int(network.broadcast_address), int(network.broadcast_address)+1) if n < 2 ** network.max_prefixlen)
        rng = random.Random(20261023)
        for _ in range(5000):
            v4 = ipaddress.IPv4Address(rng.getrandbits(32))
            addresses.update((str(v4), str(ipaddress.IPv6Address(rng.getrandbits(128))), '::ffff:' + str(v4)))
        for text in sorted(addresses):
            address = ipaddress.ip_address(text)
            expected = address.is_global and not address.is_multicast
            assert call('address', address=text) == {'ok': expected}, text
            comparisons['addresses'] += 1

        class Response(io.BytesIO):
            def __init__(self, data, encoding, length, chunk, fail):
                super().__init__(data)
                self.headers = {k: v for k, v in [('Content-Encoding', encoding), ('Content-Length', length)] if v is not None}
                self.reads = []
                self.chunk, self.fail = chunk, fail

            def read(self, size: int | None = -1):
                assert size is not None
                self.reads.append(size)
                if self.fail is not None and self.tell() >= self.fail:
                    raise OSError('fabricated read failure')
                return super().read(min(size, self.chunk))

        body_cases = []
        for encoding in [None, '', 'identity', ' IDENTITY ', '\u001cidentity\u0085', 'gzip', 'br', 'İDENTITY']:
            for length in [None, '', '0', '1', '+1', ' 1', '١', '8388608', '8388609', '0' * 5000, '9' * 5000]:
                body_cases.append((37, encoding, length, 7, None, [0, 128, 255, 65]))
        for size in [0, 1, 65535, 65536, 65537, policy.MAX_RESPONSE_BYTES, policy.MAX_RESPONSE_BYTES+1]:
            body_cases.append((size, None, None, 65536, None, [120]))
        body_cases.extend([(1, None, None, 1, 0, [120]),
                           (300, None, None, 7, 14, [65]), (100, None, '1', 1, None, [0, 255])])
        for size, encoding, length, chunk, fail, pattern in body_cases:
            data = bytes(pattern) * (size // len(pattern)) + bytes(pattern[:size % len(pattern)])
            response = Response(data, encoding, length, chunk, fail)
            expected = outcome(originals['bounded_body'], response)
            if 'ok' in expected:
                body = expected['ok']
                expected['ok'] = {'size': len(body), 'counts': [body.count(i) for i in range(256)], 'prefix': list(body[:64]), 'suffix': list(body[-64:])}
            actual = unwrap(call('body', size=size, encoding=encoding, length=length, chunk=chunk, fail=fail, pattern=pattern))
            assert actual == {'result': expected, 'reads': response.reads, 'consumed': response.tell()}, (size, encoding, str(length)[:40], expected, actual)
            comparisons['bodies'] += 1
        args.record.write_text(json.dumps({'original_tests': objects, 'comparisons': comparisons,
                                           'native_calls': calls, 'network_requests': 0,
                                           'limits': ['HTTP redirects, retries, proxy configuration and socket transport remain Python; replay substitutes only URL, resolved-address and body policy operations.', 'DNS classifications use fabricated answers; no live resolver or connection pinning was tested.', 'Body qualification compares exact histograms and 64-byte ends; large bodies are uniform, so these determine all bytes.']}, indent=2) + '\n')
    finally:
        request_stream.close()
        try:
            child.wait(timeout=15)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=5)
        response_stream.close()
    print(json.dumps({'original_tests': len(objects), 'comparisons': comparisons}))


if __name__ == '__main__':
    main()
