"""Independent CPython byte and Content-Type comparisons, with no network."""
import argparse
import codecs
import encodings
import encodings.aliases
import hashlib
import importlib.machinery
import importlib.util
import json
import pkgutil
import random
import subprocess
import sys
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--root', required=True, type=Path)
parser.add_argument('--probe', required=True, type=Path)
parser.add_argument('--record', required=True, type=Path)
args = parser.parse_args()
P = args.root / 'tools/accounting-skills'
assert sys.get_int_max_str_digits() == 4300


def reference(name, digest):
    path = P / f'tests/reference_email_{name}_3148.py.fixture'
    assert hashlib.sha256(path.read_bytes()).hexdigest() == digest
    loader = importlib.machinery.SourceFileLoader('codec_reference_' + name, str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


utils = reference('utils', '44a9e7251c44e5a1df70bcf3e8077f66da55bf4653aae48bb09e186504308734')
message = reference('message', 'f0299633f792a88342a9893ebc2fa07f24d7fe6ad15fe26204b0b7577a8f32fc')
message.utils = utils
manifest = json.loads((P / 'tests/reference_single_byte_codecs_3148.json.fixture').read_text(encoding='utf-8'))
assert manifest['table_count'] == len(manifest['codec_names']) == 70
assert hashlib.sha256((P / 'src/source_single_byte.bin').read_bytes()).hexdigest() == manifest['asset_sha256']
probe = subprocess.Popen([str(args.probe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding='utf-8')
counts = {'headers': 0, 'header_errors': 0, 'decoded_bodies': 0, 'aliases': 0}
limits = []
inputs = hashlib.sha256()


def rpc(op, **fields):
    text = json.dumps({'op': op, **fields}, ensure_ascii=True) + '\n'
    inputs.update(text.encode())
    probe.stdin.write(text)
    probe.stdin.flush()
    line = probe.stdout.readline()
    assert line, ('probe exited', probe.poll())
    reply = json.loads(line)
    if 'error' in reply:
        raise ValueError(reply['error'])
    return reply['ok']


def header(value):
    counts['headers'] += 1
    item = message.Message()
    if value is not None:
        item['Content-Type'] = value
    try:
        expected = [item.get_content_type(), item.get_content_charset()]
    except Exception as error:
        try:
            rpc('headers', text=value)
        except ValueError as actual:
            assert str(actual) == str(error), (value, str(error), str(actual))
        else:
            raise AssertionError(('native accepted failed header', value))
        counts['header_errors'] += 1
    else:
        actual = rpc('headers', text=value)
        assert actual == expected, (value, expected, actual)


def decoded(name, body):
    expected = body.decode(name, errors='replace')
    actual = rpc('decoded', charset=name, body=list(body))
    assert actual['status'] == 200 and actual['error'] == '', (name, actual)
    assert actual['text'] == expected, (name, list(body), repr(expected), repr(actual['text']))
    assert actual['digest'] == (hashlib.sha256(body).hexdigest() if body else '')
    assert not actual['text_truncated']
    counts['decoded_bodies'] += 1


try:
    for value in [None, '', 'charset=utf-8', 'text/html;charset=utf-8',
                  "text/html;charset*=utf-8''utf%2D8", "text/html;charset*=made-up''utf-8",
                  "text/html;charset*=utf-16''abc", "text/html;charset*=rot13''utf-8",
                  "text/html;charset*=utf-8%00''ascii", "text/html;charset*=utf-8''ascii;charset=utf-8",
                  'text/html;charset*1=8;charset*0=utf-', 'text/html;charset*=ascii;charset*0=utf-8',
                  'text/html;CHARSET*;charset*0=utf-8', 'text/html;charset*4294967295=x',
                  "text/html;charset*=cpé037''UTF-8", "text/html;charset*=cpK037''UTF-8",
                  "text/html;charset*=cpſ037''UTF-8",
                  'text/html;charset*' + '9' * 4300 + '=utf-8',
                  'text/html;x*' + '0' * 4301 + '=unused;charset=utf-8',
                  'text/html;charset*' + '9' * 4301 + '=x']:
        header(value)
    for scalar in [0x1C89, 0x11DB0, 0x1E6C0, 0x16EA0]:
        header('text/plain;x' + chr(scalar) + '*' + '0' * 4301 + '=unused;charset=utf-8')
    rng = random.Random(20261023)
    names = ['charset', 'CHARSET', 'charset*', 'charset*0', 'charset*1', 'charset*01*',
             'charset*0*', 'charset*2*', 'charset*00', 'charset**', 'x', 'x*0*', 'X*',
             'charset-more*0', 'charset*bogus', '']
    values = ['', 'UTF-8', 'ascii', 'latin-1', "utf-8''utf%2D8", "ascii'en'utf-8",
              "made-up''UTF-8", "utf-16''abc", "windows-1252''%81", '%ff', '%0x', 'é',
              '𝄞', '"utf-8"', '<utf-8>', '"u\\"tf8"', '"a;b"', '"unterminated',
              "'utf-8'", '\\', '"\\\\"', 'utf-', '8']
    for _ in range(7000):
        first = rng.choice(['text/html', 'TEXT/PLAIN', 'text / html', 'invalid', 'text/html/invalid', '', 'charset=utf-8'])
        fields = []
        for _ in range(rng.randrange(0, 9)):
            name, value = rng.choice(names), rng.choice(values)
            fields.append(name if rng.randrange(5) == 0 else name + rng.choice(['=', ' = ', '=\t']) + value)
        header(first + ''.join(';' + item for item in fields))
    for name in manifest['codec_names']:
        for byte in range(256):
            decoded(name, bytes([byte]))
        decoded(name, bytes(range(256)))
        for _ in range(8):
            decoded(name, rng.randbytes(rng.randrange(0, 257)))
        encoded = ''.join(f'%{byte:02X}' for byte in 'UTF-8'.encode(name))
        header(f"text/plain;charset*={name}'en'{encoded}")
    for name in ['utf-8', 'utf-8-sig', 'utf-16', 'utf-16-le', 'utf-16-be', 'utf-32', 'utf-32-le', 'utf-32-be']:
        for _ in range(700):
            body = rng.randbytes(rng.randrange(0, 21))
            encoded = ''.join(f'%{byte:02X}' for byte in body)
            header(f"text/plain;charset*={name}''{encoded}")
    names = set(encodings.aliases.aliases) | set(encodings.aliases.aliases.values())
    names |= {entry.name for entry in pkgutil.iter_modules(encodings.__path__) if not entry.name.startswith('_')}
    for name in sorted(names):
        try:
            canonical = codecs.lookup(name).name
        except LookupError:
            continue
        if canonical in manifest['codec_names']:
            decoded(name, bytes(range(256)))
            counts['aliases'] += 1
    for encoding, encoded in [('utf-8', '%FF'), ('utf-16', '%FF%FE%75%00%74%00%66%00%2D%00%38%00'),
                              ('utf-32-le', '%75%00%00%00%74%00%00%00%66%00%00%00%38%00%00%00')]:
        header(f"text/plain;charset*={encoding}''{encoded}")
    for value in ["text/html;charset*=utf-7''+AFU-+AFQ-+AEY--8", "text/html;charset*=shift_jis''utf-8"]:
        try:
            rpc('headers', text=value)
        except ValueError as error:
            assert str(error).startswith('Unqualified source charset ')
            limits.append({'header': value, 'native': str(error), 'scope': 'Remaining decoder compatibility, not a blanket RFC2231 refusal'})
        else:
            raise AssertionError(('unsupported parameter codec accepted', value))
    args.record.write_text(json.dumps({'counts': counts, 'known_decoder_limits': limits,
        'input_sequence_sha256': inputs.hexdigest(), 'runtime': sys.version,
        'single_byte_tables': 70, 'reference': 'Hash-pinned unmodified CPython 3.14.8 email modules; independent installed CPython codec decode',
        'network_requests': 0, 'failures': 0}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'counts': counts, 'single_byte_tables': 70, 'known_decoder_limits': len(limits), 'failures': 0}))
finally:
    probe.stdin.close()
    try:
        probe.wait(timeout=10)
    except subprocess.TimeoutExpired:
        probe.kill()
        probe.wait(timeout=10)
