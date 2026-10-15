"""Offline regressions over inherited real ZTO evidence; no transport needed."""
import hashlib
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

M = runpy.run_path(str(Path(__file__).with_name('pin.py')))
FIXTURE = Path(__file__).resolve().parents[1] / 'two-source-zto/live-agreement.json'
RAW = FIXTURE.read_bytes()
EXPECTED = hashlib.sha256(RAW).hexdigest()


def encoded(bundle):
    return (json.dumps(bundle, sort_keys=True, indent=2) + '\n').encode()


def reseal(bundle):
    p = M['A']['P']
    for source in bundle['sources']:
        for read in source['reads']:
            read['response_sha256'] = p['digest'](read['response'])
        source['reads_sha256'] = p['digest'](source['reads'])
    bundle['transcript_sha256'] = p['digest'](bundle['sources'])
    return encoded(bundle)


class PinTests(unittest.TestCase):
    def test_real_saved_observation(self):
        result = M['review'](RAW, EXPECTED)
        self.assertEqual(result['observation']['total_supply_raw'], str(10**27))
        self.assertEqual(result['file_sha256'], EXPECTED)
        self.assertEqual(result['file_bytes'], len(RAW))

    def test_replay_offline(self):
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network')):
            M['review'](RAW, EXPECTED)

    def test_input_unchanged(self):
        before = bytes(RAW)
        M['review'](RAW, EXPECTED)
        self.assertEqual(before, RAW)

    def test_wrong_pin(self):
        with self.assertRaises(M['PinError']):
            M['review'](RAW, '0'*64)

    def test_pin_format(self):
        for value in (None, True, 1, [], {}, '', 'a'*63, 'a'*65, 'A'*64,
                      'g'*64, EXPECTED+'\n', '0x'+EXPECTED):
            with self.subTest(value=value), self.assertRaises(M['PinError']):
                M['review'](RAW, value)

    def test_whitespace_changes_exact_pin(self):
        with self.assertRaises(M['PinError']):
            M['review'](RAW+b' ', EXPECTED)

    def test_whitespace_with_new_pin_is_valid(self):
        altered = RAW+b' '
        M['review'](altered, hashlib.sha256(altered).hexdigest())

    def test_resealed_consistent_substitution_rejected_by_retained_pin(self):
        bundle = json.loads(RAW)
        for source in bundle['sources']:
            source['reads'][2]['response']['result'] = '0x'+format(123, '064x')
        raw = reseal(bundle)
        # Existing internal consistency checks accept this invented replacement.
        self.assertEqual(M['A']['validate_bundle'](json.loads(raw))['total_supply_raw'], '123')
        with self.assertRaises(M['PinError']):
            M['review'](raw, EXPECTED)

    def test_replaced_pin_also_passes_documented_limit(self):
        bundle = json.loads(RAW)
        for source in bundle['sources']:
            source['reads'][2]['response']['result'] = '0x'+format(123, '064x')
        raw = reseal(bundle)
        self.assertEqual(M['review'](raw, hashlib.sha256(raw).hexdigest())[
            'observation']['total_supply_raw'], '123')

    def test_matching_hash_does_not_bypass_replay(self):
        for raw in (b'{}', b'{"a":1,"a":2}', b'NaN', b'not json', b''):
            with self.subTest(raw=raw), self.assertRaises((ValueError, M['A']['B']['SnapshotError'])):
                M['review'](raw, hashlib.sha256(raw).hexdigest())

    def test_resealed_disagreement_rejected_even_with_new_pin(self):
        bundle = json.loads(RAW)
        bundle['sources'][1]['reads'][2]['response']['result'] = '0x'+format(123, '064x')
        raw = reseal(bundle)
        with self.assertRaises(ValueError):
            M['review'](raw, hashlib.sha256(raw).hexdigest())

    def test_byte_limit(self):
        raw = b' '*100001
        with self.assertRaises(M['PinError']):
            M['review'](raw, hashlib.sha256(raw).hexdigest())

    def test_not_bytes(self):
        with self.assertRaises(M['PinError']):
            M['review'](bytearray(RAW), EXPECTED)

    def test_paths_refused(self):
        for path in ('../outside', '/absolute', '.hidden', 'line-1/../outside'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                M['verify'](path, EXPECTED)

    def test_bad_pin_before_file_access(self):
        with patch.dict(M['A']['SAFE'], {'read_bytes': lambda *a: self.fail('IO')}):
            with self.assertRaises(M['PinError']):
                M['verify']('anything', 'bad')

    def test_cli(self):
        with patch('sys.stdout'), patch('sys.stderr'):
            path = str(FIXTURE.relative_to(Path.cwd()))
            self.assertEqual(M['main']([path, '--expected-sha256', EXPECTED]), 0)
            self.assertEqual(M['main']([path, '--expected-sha256', '0'*64]), 1)


if __name__ == '__main__':
    unittest.main()
