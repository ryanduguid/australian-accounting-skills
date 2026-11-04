"""Compare every frozen multibyte-state edge with independent CPython decoding."""
import argparse
import codecs
import encodings
import encodings.aliases
import hashlib
import json
import random
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--root', type=Path, required=True)
parser.add_argument('--probe', type=Path, required=True)
parser.add_argument('--record', type=Path, required=True)
args = parser.parse_args()
P = args.root / 'tools/accounting-skills'
manifest = json.loads((P / 'tests/reference_multibyte_codecs_3148.json.fixture').read_text(encoding='utf-8'))
assert hashlib.sha256((P / 'src/source_multibyte.bin').read_bytes()).hexdigest() == manifest['asset_sha256']
assert len(manifest['codecs']) == 15 and sum(row['states'] for row in manifest['codecs']) == 2415
probe = subprocess.Popen([str(args.probe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8')
counts = {'state_edges_and_eof': 0, 'random_bodies': 0, 'aliases': 0}
inputs = hashlib.sha256()
receipts = []

def check(name, body):
    expected = body.decode(name, errors='replace')
    request = json.dumps({'op': 'decoded', 'charset': name, 'body': list(body)}) + '\n'
    inputs.update(request.encode())
    probe.stdin.write(request)
    probe.stdin.flush()
    line = probe.stdout.readline()
    assert line, ('probe exited', probe.poll())
    reply = json.loads(line)
    assert 'ok' in reply, (name, list(body), reply)
    actual = reply['ok']
    assert actual['status'] == 200 and actual['error'] == '', (name, list(body), actual)
    assert actual['text'] == expected and not actual['text_truncated'], (name, list(body), repr(expected), repr(actual['text']))
    assert actual['digest'] == (hashlib.sha256(body).hexdigest() if body else ''), (name, list(body))

try:
    rng = random.Random(2026102302)
    for row in manifest['codecs']:
        name = row['name']
        start = counts['state_edges_and_eof']
        assert len(row['witnesses']) == row['states']
        for prefix in row['witnesses']:
            prefix = bytes(prefix)
            check(name, prefix)
            counts['state_edges_and_eof'] += 1
            for byte in range(256):
                check(name, prefix + bytes([byte]))
                counts['state_edges_and_eof'] += 1
        for _ in range(100):
            check(name, rng.randbytes(rng.randrange(0, 2049)))
            counts['random_bodies'] += 1
        receipts.append({'codec': name, 'states': row['states'], 'edge_and_eof_bodies': counts['state_edges_and_eof'] - start, 'random_bodies': 100})
    names = set(encodings.aliases.aliases) | set(encodings.aliases.aliases.values())
    qualified = {row['name'] for row in manifest['codecs']}
    for name in sorted(names):
        try:
            canonical = codecs.lookup(name).name
        except LookupError:
            continue
        if canonical in qualified:
            check(name, bytes(range(256)))
            counts['aliases'] += 1
    assert counts['state_edges_and_eof'] == 620655 and counts['random_bodies'] == 1500
    args.record.write_text(json.dumps({'counts': counts, 'codecs': receipts, 'input_sequence_sha256': inputs.hexdigest(),
        'runtime': sys.version, 'asset_sha256': manifest['asset_sha256'], 'network_requests': 0, 'failures': 0,
        'scope': 'Each retained state witness plus every byte and EOF through the production response interpreter; additional chained random bodies and aliases. Installed CPython one-shot decode is the independent expected output.'}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'counts': counts, 'failures': 0}), flush=True)
finally:
    probe.stdin.close()
    try:
        probe.wait(timeout=10)
    except subprocess.TimeoutExpired:
        probe.kill()
        probe.wait(timeout=10)
