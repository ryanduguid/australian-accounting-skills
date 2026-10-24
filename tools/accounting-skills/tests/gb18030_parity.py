"""Independent one-shot CPython checks of the exact private native decoder."""
import argparse
import codecs
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
parser.add_argument('--production-probe', type=Path, required=True)
parser.add_argument('--record', type=Path, required=True)
args = parser.parse_args()
crate = args.root / 'tools/accounting-skills'
manifest = json.loads((crate / 'tests/reference_gb18030_3148.json.fixture').read_text(encoding='utf-8'))
assert hashlib.sha256((crate / 'src/source_gb18030.bin').read_bytes()).hexdigest() == manifest['asset_sha256']
sequence = hashlib.sha256()
counts = {}
probe = subprocess.Popen([str(args.probe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8')
production = subprocess.Popen([str(args.production_probe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8')

def check_batch(name, bodies):
    probe.stdin.write(json.dumps([list(body) for body in bodies]) + '\n')
    probe.stdin.flush()
    actual = json.loads(probe.stdout.readline())
    assert len(actual) == len(bodies)
    for body, value in zip(bodies, actual, strict=True):
        replacement = body.decode('gb18030', errors='replace')
        try:
            strict = body.decode('gb18030', errors='strict')
        except UnicodeDecodeError:
            strict = None
        assert value == [replacement, strict], (name, body.hex(), value, replacement, strict)
        sequence.update(len(body).to_bytes(4, 'little') + body)
    counts[name] = counts.get(name, 0) + len(bodies)

def check(name, bodies):
    pending = []
    for body in bodies:
        pending.append(body)
        if len(pending) == 1024:
            check_batch(name, pending)
            pending.clear()
    if pending:
        check_batch(name, pending)

def full_response(body, alias):
    production.stdin.write(json.dumps({'op': 'decoded', 'body': list(body), 'charset': alias}) + '\n')
    production.stdin.flush()
    reply = json.loads(production.stdout.readline())
    assert 'ok' in reply, reply
    actual = reply['ok']
    assert actual['status'] == 200 and not actual['error'] and not actual['text_truncated'], actual
    assert actual['text'] == body.decode(alias, errors='replace'), (alias, body.hex(), actual)
    assert actual['digest'] == (hashlib.sha256(body).hexdigest() if body else '')
    counts['production_responses'] = counts.get('production_responses', 0) + 1

try:
    check('empty_and_single', [b''] + [bytes([byte]) for byte in range(256)])
    check('all_two_bytes', (bytes([a, b]) for a in range(256) for b in range(256)))
    check('incomplete_digit_prefixes', (bytes([a, b, c]) for a in range(128, 256) for b in range(0x30, 0x3a) for c in range(256)))
    check('all_four_byte_shapes', (bytes([a, b, c, d]) for a in range(0x81, 0xff) for b in range(0x30, 0x3a) for c in range(0x81, 0xff) for d in range(0x30, 0x3a)))
    edges = [0, 0x2f, 0x30, 0x39, 0x3a, 0x7f, 0x80, 0x81, 0x84, 0x8f, 0x90, 0xe3, 0xfe, 0xff]
    check('malformed_third_bytes', (bytes([a, b, c, d]) for a in edges[6:] for b in [0x30, 0x39] for c in range(256) for d in edges))
    check('malformed_fourth_bytes', (bytes([a, b, c, d]) for a in edges[6:] for b in [0x30, 0x39] for c in edges[6:] for d in range(256)))
    rng = random.Random(18030)
    random_bodies = [rng.randbytes(rng.randrange(0, 1025)) for _ in range(3000)]
    valid_bodies = [''.join(chr(point) for point in (rng.randrange(0x110000) for _ in range(100)) if not 0xd800 <= point <= 0xdfff).encode('gb18030') for _ in range(1000)]
    check('random_chains', random_bodies)
    check('unicode_chains', valid_bodies)
    for body in random_bodies[:128] + valid_bodies[:128] + [b'', bytes(range(256)), b'\x80\x30A', b'\x81\x30\x81\x30', b'\x90\x30\x81\x30']:
        full_response(body, 'gb18030')
    aliases = []
    for alias in sorted(set(encodings.aliases.aliases) | set(encodings.aliases.aliases.values())):
        try:
            canonical = codecs.lookup(alias).name
        except LookupError:
            continue
        if canonical == 'gb18030':
            aliases.append(alias)
            full_response('你好 € 𐀀'.encode('gb18030'), alias)
    assert counts['all_four_byte_shapes'] == 1587600
    record = {'counts': counts, 'decode_modes_per_body': ['replace', 'strict'], 'aliases': aliases,
              'input_sequence_sha256': sequence.hexdigest(), 'asset_sha256': manifest['asset_sha256'],
              'runtime': sys.version, 'failures': 0, 'network_requests': 0,
              'scope': 'Large comparisons compile the exact private production decoder in an offline probe; replacement response samples and aliases separately exercise the production bounded reader, header interpreter and raw digest. Expected output comes from independent installed CPython one-shot decoding.'}
    args.record.write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'counts': counts, 'aliases': aliases, 'failures': 0}), flush=True)
finally:
    for child in [probe, production]:
        child.stdin.close()
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            child.kill()
            child.wait(timeout=10)
