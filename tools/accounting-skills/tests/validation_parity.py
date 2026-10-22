"""Replay original validator tests against native operations and compare fabricated inputs."""
from __future__ import annotations

import argparse
import collections
import contextlib
import html.entities
import importlib.util
import json
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from datetime import date, timedelta
from pathlib import Path
from unittest import mock


def main():
    parser = argparse.ArgumentParser()
    for name in ('root', 'binary', 'probe', 'record'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    root, binary = args.root.resolve(), args.binary.resolve()
    sys.path.insert(0, str(root))
    spec = importlib.util.spec_from_file_location('native_validation_original_tests', root / 'tests/test_validation_pack.py')
    tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(tests)
    v = tests.validator
    functions = ('read_utf8', 'parse_front_matter', 'normalise_for_sensitive_scan',
                 'check_sensitive_content', 'is_reparse_point', 'check_expected_path',
                 'inventory_validation_tree', 'discover_case_names', 'expected_validation',
                 'case_ids', 'split_result_files', 'git_entries', 'check_ignored',
                 'check_results_schema', 'check_result_file', 'check_published_inventories',
                 'check_text', 'main')
    originals = {name: getattr(v, name) for name in functions}
    original_patterns = dict(v.SENSITIVE_PATTERNS)
    child = subprocess.Popen([str(args.probe.resolve())], stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE, text=True, encoding='utf-8',
                             env=tests.fixture_git_environment())
    calls = collections.Counter()
    records = []
    fallback = []

    def call(op, **values):
        calls[op] += 1
        child.stdin.write(json.dumps({'op': op, **values}) + '\n')
        child.stdin.flush()
        response = child.stdout.readline()
        assert response, ('probe ended', child.poll(), op)
        result = json.loads(response)
        if 'error' in result:
            raise v.ValidationError(result['error'])
        return result['ok']

    def native_main(directory=root):
        calls['real_cli'] += 1
        result = subprocess.run([str(binary), 'validate-validation', '--root', str(directory)],
                                cwd=directory, capture_output=True, text=True,
                                encoding='utf-8', timeout=90)
        print(result.stdout, end='')
        if result.stderr:
            print(result.stderr, file=sys.stderr, end='')
        return result.returncode

    def result_file(path, text, known=v.CASE_IDS):
        if v.SENSITIVE_PATTERNS != original_patterns:
            fallback.append('dynamic Python regex injection is not a native runtime interface')
            with mock.patch.object(v, 'check_sensitive_content', originals['check_sensitive_content']):
                return originals['check_result_file'](path, text, known)
        return call('result', path=path, text=text, known=sorted(known))

    wrappers = {
        'read_utf8': lambda path: call('read', path=str(path)),
        'parse_front_matter': lambda text, name: tuple(call('front', text=text, name=name)),
        'normalise_for_sensitive_scan': lambda text: call('normalise', text=text),
        'check_sensitive_content': lambda text, waived=frozenset(): call('sensitive', text=text, waived=sorted(waived)),
        'is_reparse_point': lambda path: call('reparse', path=str(path)),
        'check_expected_path': lambda path, directory=root: call('expected_path', path=str(path), root=str(directory)),
        'inventory_validation_tree': lambda directory=root: set(call('inventory', root=str(directory))),
        'discover_case_names': lambda directory=root: set(call('discover', root=str(directory))),
        'expected_validation': lambda names: set(call('expected', names=sorted(names))),
        'case_ids': lambda names: frozenset(call('ids', names=sorted(names))),
        'split_result_files': lambda names: tuple(set(part) for part in call('split', names=sorted(names))),
        'git_entries': lambda paths, directory=root: call('git', names=paths, root=str(directory)),
        'check_ignored': lambda path, directory=root: call('ignored', path=path, root=str(directory)),
        'check_results_schema': lambda text, known=v.CASE_IDS: call('schema', text=text, known=sorted(known)),
        'check_result_file': result_file,
        'check_published_inventories': lambda skills, directory=root: call('published', names=sorted(skills), root=str(directory)),
        'check_text': lambda path, text: call('text', path=path, text=text),
        'main': native_main,
    }

    class RecordingResult(unittest.TextTestResult):
        def startTest(self, test):
            self.before = calls.copy()
            super().startTest(test)

        def stopTest(self, test):
            records.append({'test': test.id(), 'native_calls': dict(calls - self.before)})
            super().stopTest(test)

    try:
        for name, function in wrappers.items():
            setattr(v, name, function)
        result = unittest.TextTestRunner(verbosity=2, resultclass=RecordingResult).run(
            unittest.defaultTestLoader.loadTestsFromModule(tests))
        assert result.wasSuccessful() and not result.skipped
        for name, function in originals.items():
            setattr(v, name, function)
        comparisons = collections.Counter()

        def compare(label, function, op, *positional, **values):
            try:
                expected = function(*positional)
            except (v.ValidationError, ValueError, RecursionError):
                try:
                    call(op, **values)
                except v.ValidationError:
                    pass
                else:
                    raise AssertionError(('native accepted original refusal', label, values))
            else:
                actual = call(op, **values)
                if isinstance(expected, tuple):
                    expected = list(expected)
                assert actual == expected, (label, positional, expected, actual)
            comparisons[label] += 1

        for entity in sorted(html.entities.html5):
            for spelling in ('&' + entity, '&' + entity + 'suffix'):
                compare('html_entities', originals['normalise_for_sensitive_scan'], 'normalise', spelling, text=spelling)
        for point in [*range(1024), 0xd800, 0xdfff, 0xfdd0, 0xfffe, 0xffff, 0x10ffff, 0x110000, 10**30]:
            for spelling in (f'&#{point};', f'&#x{point:x}'):
                compare('numeric_entities', originals['normalise_for_sensitive_scan'], 'normalise', spelling, text=spelling)
        for spelling in [*(f'&#{digit * size};' for digit in ('0', '1') for size in (4300, 4301, 5000)),
                         '&#x' + '1' * 5000 + ';', '&#x' + '0' * 5000 + '41;']:
            compare('large_numeric_entities', originals['normalise_for_sensitive_scan'], 'normalise', spelling, text=spelling)
        special = ''.join(chr(point) for point in range(0x110000)
                          if unicodedata.normalize('NFKC', chr(point)) != chr(point)
                          or unicodedata.category(chr(point)) == 'Cf')
        for start in range(0, len(special), 32):
            value = special[start:start + 32]
            compare('unicode_normalisation', originals['normalise_for_sensitive_scan'], 'normalise', value, text=value)
        for identity in ('test-card', 'true', 'on', 'null', '0b101', '0xabc', '2026-01-01', '12_345',
                         '"test-card"', "'test-card'", '!!str test-card', '&alias test-card'):
            for skills in ('[bas-preparation]', '\n  - bas-preparation', '[on]', '[2026-01-01]', '[]', '{}'):
                value = tests.card(f'id: {identity}\nsynthetic: true\ntarget_skills: {skills}')
                compare('yaml_cards', originals['parse_front_matter'], 'front', value, 'test-card.md', text=value, name='test-card.md')
        for value in ('ordinary synthetic words', 'worker@example.test', 'worker&#64;example.test',
                      'A**B**N: 12 345 678 901', 'B<!-- -->SB 123-456',
                      'sk_abcdef**ghijkl**mnop', 'effective 1 **July** 2026',
                      'Bearer abcdefghijklmnop', 'Example Pty Ltd', 'effective 12%.'):
            for prefix in ('', 'x\u0301', '\u0130', '\u0131', '\u017f', '\u212a', '\x1c'):
                text = prefix + value
                compare('sensitive_variants', originals['check_sensitive_content'], 'sensitive', text, text=text)
        good = json.loads(tests.RecordedRunTests.GOOD)
        for spelling in ('2026-01-31', '20260131', '2026-W05-6', '2026W056', '2026-02-30',
                         '2026-W54-1', '0000-01-01', '2026-01-32', '2026W05',
                         '2026W05-6', '2026-W056', '2026--W05-6', '2-0-2-6-W0-5-6',
                         '2026-W€', '2026-Wé1'):
            good['run_date'] = spelling
            value = json.dumps(good)
            compare('result_dates', originals['check_result_file'], 'result', tests.RecordedRunTests.NAME, value,
                    path=tests.RecordedRunTests.NAME, text=value, known=sorted(v.CASE_IDS))
        for start in (date(1999, 12, 25), date(2000, 2, 25), date(2004, 12, 25),
                      date(2025, 12, 25), date(2026, 12, 25), date(9998, 12, 25)):
            for offset in range(20):
                day = start + timedelta(days=offset)
                iso = day.isocalendar()
                for spelling in (day.isoformat(), day.strftime('%Y%m%d'),
                                 f'{iso.year:04}-W{iso.week:02}-{iso.weekday}',
                                 f'{iso.year:04}W{iso.week:02}{iso.weekday}'):
                    good['run_date'] = spelling
                    path = f'validation/results/{day.isoformat()}-fixture.json'
                    value = json.dumps(good)
                    compare('calendar_and_week_dates', originals['check_result_file'], 'result', path, value,
                            path=path, text=value, known=sorted(v.CASE_IDS))
        with tempfile.TemporaryDirectory() as temporary:
            fixture = Path(temporary)
            (fixture / '.claude-plugin').mkdir()
            (fixture / 'docs').mkdir()
            (fixture / 'docs/skill-catalogue.md').write_text('| `bas-preparation` |\n', encoding='utf-8')
            for spelling in ('bas-preparation', './bas-preparation', 'a/bas-preparation/',
                             'a/bas-preparation/.', 'a//./bas-preparation///./',
                             '//a/bas-preparation', '', '.', '/', '..'):
                (fixture / '.claude-plugin/marketplace.json').write_text(
                    json.dumps({'plugins': [{'skills': [spelling]}]}), encoding='utf-8')
                compare('marketplace_posix_paths', originals['check_published_inventories'],
                        'published', {'bas-preparation'}, fixture,
                        names=['bas-preparation'], root=str(fixture))
        original_stdout = __import__('io').StringIO()
        if sys.platform != 'win32':
            with tempfile.TemporaryDirectory() as temporary:
                fixture = Path(temporary) / 'repository'
                tests.build_fixture(fixture)
                name = sorted((fixture / 'validation/cases').glob('*.md'))[0].name
                (fixture / 'validation' / ('cases\\' + name)).write_bytes(bytes([255, 254, 0]))
                with contextlib.redirect_stdout(original_stdout):
                    expected_code = originals['main'](fixture)
                actual = subprocess.run([str(binary), 'validate-validation', '--root', str(fixture)],
                                        capture_output=True, text=True, encoding='utf-8', timeout=90,
                                        env=tests.fixture_git_environment())
                assert expected_code == actual.returncode == 1
                assert actual.stdout == original_stdout.getvalue() and actual.stderr == ''
                assert 'validation inventory mismatch' in actual.stdout
                comparisons['posix_inventory_collision'] += 1
            original_stdout = __import__('io').StringIO()
        with contextlib.redirect_stdout(original_stdout):
            original_code = originals['main'](root)
        native = subprocess.run([str(binary), 'validate-validation', '--root', str(root)], cwd=root,
                                capture_output=True, text=True, encoding='utf-8', timeout=120)
        assert (native.returncode, native.stdout, native.stderr) == (original_code, original_stdout.getvalue(), '')
        original_cli = subprocess.run([sys.executable, '-I', '-X', 'utf8', str(root / 'scripts/validate_validation.py')],
                                      cwd=root, capture_output=True, timeout=120)
        native_cli = subprocess.run([str(binary), 'validate-validation', '--root', str(root)],
                                    cwd=root, capture_output=True, timeout=120)
        assert (native_cli.returncode, native_cli.stdout, native_cli.stderr) == (
            original_cli.returncode, original_cli.stdout, original_cli.stderr)
        args.record.write_text(json.dumps({'original_tests': result.testsRun, 'skips': result.skipped,
            'test_records': records, 'native_calls': dict(calls), 'python_only_fallbacks': fallback,
            'fabricated_comparisons': dict(comparisons), 'unicode_version': unicodedata.unidata_version,
            'nfkc_or_format_characters': len(special), 'real_repository_cli_bytes_equivalent_after_newline_decode': True,
            'real_repository_raw_cli_byte_comparisons': 1,
            'original_helpers_restored': all(getattr(v, name) is function for name, function in originals.items())}, indent=2) + '\n')
    finally:
        for name, function in originals.items():
            setattr(v, name, function)
        child.terminate()
        child.communicate(timeout=10)


if __name__ == '__main__':
    main()
