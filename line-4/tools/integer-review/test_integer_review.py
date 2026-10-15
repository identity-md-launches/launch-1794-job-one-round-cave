import contextlib
import copy
import io
import json
from pathlib import Path
import random
import unittest
from unittest.mock import patch

import integer_review as ir
from typed_digest import TypedDataError, digest, loads_bounded


def data(kind='uint256', value='1'):
    return {'types': {'EIP712Domain': [{'name': 'chainId', 'type': 'uint256'}],
                      'Quantity': [{'name': 'amount', 'type': kind}]},
            'primaryType': 'Quantity', 'domain': {'chainId': 1},
            'message': {'amount': value}}


class IntegerReviewTests(unittest.TestCase):
    def item(self, kind, value):
        return ir.review(data(kind, value))['integers'][1]

    def test_historical_zto_exact_digest_and_loss(self):
        request = loads_bounded(Path(__file__).with_name('zto-payment.json').read_bytes())
        report = ir.review(request, '0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774')
        self.assertTrue(report['matchesExpected'])
        self.assertFalse(report['hasUnsafeJsonNumbers'])
        quantity = report['integers'][1]
        self.assertEqual(quantity['path'], '/message/minimumRaw')
        self.assertEqual(quantity['exactDecimal'], '166357571280020680094504')
        self.assertTrue(quantity['binary64Coercion']['changesValue'])
        self.assertEqual(int(quantity['word'], 16), 166357571280020680094504)

    def test_signed_word_vectors(self):
        self.assertEqual(self.item('int8', -1)['word'], '0x' + 'ff' * 32)
        self.assertEqual(self.item('int8', -128)['word'], '0x' + 'ff' * 31 + '80')
        self.assertEqual(self.item('int8', 127)['word'], '0x' + '00' * 31 + '7f')

    def test_unsigned_word_vectors(self):
        self.assertEqual(self.item('uint8', 255)['word'], '0x' + '00' * 31 + 'ff')
        self.assertEqual(self.item('uint256', str(2**256 - 1))['word'], '0x' + 'ff' * 32)
        self.assertEqual(self.item('uint256', 0)['word'], '0x' + '00' * 32)

    def test_every_width_boundary(self):
        for width in range(8, 257, 8):
            for signed in (False, True):
                kind = ('int' if signed else 'uint') + str(width)
                low = -(2 ** (width - 1)) if signed else 0
                high = 2 ** (width - int(signed)) - 1
                for n in (low, high):
                    item = self.item(kind, str(n))
                    self.assertEqual(item['minimumDecimal'], str(low))
                    self.assertEqual(item['maximumDecimal'], str(high))
                    self.assertEqual(int(item['word'], 16), n % 2**256)
                for n in (low - 1, high + 1):
                    with self.assertRaises(TypedDataError):
                        self.item(kind, str(n))

    def test_safe_integer_boundary_and_exact_unsafe_power(self):
        for sign in (-1, 1):
            safe = self.item('int256', sign * (2**53 - 1))
            self.assertFalse(safe['requiresExactIntegerHandling'])
            exact = self.item('int256', sign * 2**53)
            self.assertTrue(exact['unsafeJsonNumber'])
            self.assertFalse(exact['binary64Coercion']['changesValue'])

    def test_ties_to_even_positive_and_negative(self):
        for sign in (-1, 1):
            self.assertEqual(ir.binary64_integer(sign * (2**53 + 1)), sign * 2**53)
            self.assertEqual(ir.binary64_integer(sign * (2**53 + 3)), sign * (2**53 + 4))
            self.assertEqual(ir.binary64_integer(sign * (2**54 + 1)), sign * 2**54)
            self.assertEqual(ir.binary64_integer(sign * (2**54 + 3)), sign * (2**54 + 4))

    def test_conversion_crosses_declared_range(self):
        for kind, value, nearest in [('uint256', 2**256 - 1, 2**256),
                                     ('int256', 2**255 - 1, 2**255)]:
            converted = self.item(kind, str(value))['binary64Coercion']
            self.assertEqual(converted['nearestIntegerDecimal'], str(nearest))
            self.assertTrue(converted['outsideDeclaredRange'])
        self.assertFalse(self.item('int256', str(-2**255))['binary64Coercion']['outsideDeclaredRange'])

    def test_integer_simulation_against_runtime_binary64(self):
        # Independent runtime float conversion oracle; production uses no floats.
        rng = random.Random(712)
        values = [rng.getrandbits(width) for width in range(1, 257) for _ in range(3)]
        for number in values:
            self.assertEqual(ir.binary64_integer(number), int(float(number)))
            self.assertEqual(ir.binary64_integer(-number), int(float(-number)))

    def test_hex_decimal_and_numeric_equivalence(self):
        reports = [ir.review(data(value=v)) for v in (123, '123', '0x7b', '0X7B')]
        self.assertEqual(len({r['digest'] for r in reports}), 1)
        self.assertEqual([r['integers'][1]['inputForm'] for r in reports],
                         ['json_integer', 'decimal_string', 'hex_string', 'hex_string'])

    def test_large_json_number_differs_from_string_risk(self):
        number = 2**80 + 1
        literal = ir.review(data(value=number))
        string = ir.review(data(value=str(number)))
        self.assertEqual(literal['digest'], string['digest'])
        self.assertTrue(literal['hasUnsafeJsonNumbers'])
        self.assertFalse(string['hasUnsafeJsonNumbers'])
        self.assertTrue(string['binary64CoercionChangesValue'])

    def test_never_rounds_or_changes_original(self):
        request = data(value=2**80 + 1)
        before = copy.deepcopy(request)
        result = ir.review(request)
        self.assertEqual(before, request)
        self.assertEqual(result['digest'], digest(before)['digest'])
        self.assertNotEqual(result['digest'], digest(data(value=2**80))['digest'])

    def test_nested_arrays_and_recursive_finite_struct(self):
        request = data()
        request['types']['Quantity'] = [{'name': 'values', 'type': 'Leaf[][1]'}]
        request['types']['Leaf'] = [{'name': 'n', 'type': 'int16'},
                                    {'name': 'next', 'type': 'Leaf[]'}]
        request['message'] = {'values': [[{'n': -5, 'next': [{'n': 6, 'next': []}]}]]}
        paths = [x['path'] for x in ir.review(request)['integers']]
        self.assertEqual(paths, ['/domain/chainId', '/message/values/0/0/n',
                                 '/message/values/0/0/next/0/n'])

    def test_noninteger_fields_and_unreachable_types_excluded(self):
        request = data('string', '9007199254740993')
        request['types']['Unused'] = [{'name': 'n', 'type': 'uint256'}]
        self.assertEqual(ir.review(request)['integerCount'], 1)
        for kind, value in [('bool', True), ('bytes', '0x0102'),
                            ('address', '0xd782bdea4ef02a0bd391eb9089470c8080f0a68e')]:
            self.assertEqual(ir.review(data(kind, value))['integerCount'], 1)

    def test_no_integers(self):
        request = data('string', 'ZTO')
        request['types']['EIP712Domain'] = []
        request['domain'] = {}
        report = ir.review(request)
        self.assertEqual(report['integers'], [])
        self.assertFalse(report['hasUnsafeJsonNumbers'])

    def test_invalid_values_and_schema_fail_before_output(self):
        for value in (True, 1.5, '-0x1', '01', '1.0'):
            with self.assertRaises(TypedDataError):
                ir.review(data(value=value))
        request = data()
        request['message']['extra'] = 2
        with self.assertRaises(TypedDataError):
            ir.review(request)
        with self.assertRaises(TypedDataError):
            ir.review(data(), '0x12')

    def test_expected_digest_mismatch(self):
        report = ir.review(data(), digest(data(value=2))['digest'])
        self.assertFalse(report['matchesExpected'])

    def test_strict_parser_rejects_duplicate_float_and_nonfinite(self):
        for raw in (b'{"x":1,"x":2}', b'1.5', b'NaN', b'1e3'):
            with self.assertRaises(TypedDataError):
                loads_bounded(raw)

    def test_report_limits_and_no_partial_cli_output(self):
        with patch.object(ir, 'MAX_REPORT_BYTES', 100), \
                patch.object(ir, 'load_workspace_json', return_value=data()), \
                contextlib.redirect_stdout(io.StringIO()) as out, \
                contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(ir.main(['input.json']), 2)
        self.assertEqual(out.getvalue(), '')
        self.assertIn('output limit', err.getvalue())

    def test_cli_risk_and_digest_exit_codes(self):
        for value, expected_exit in [(1, 0), ('9007199254740993', 0),
                                      (9007199254740993, 1)]:
            with patch.object(ir, 'load_workspace_json', return_value=data(value=value)), \
                    contextlib.redirect_stdout(io.StringIO()) as out:
                self.assertEqual(ir.main(['input.json']), expected_exit)
                json.loads(out.getvalue())
        with patch.object(ir, 'load_workspace_json', return_value=data()), \
                contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(ir.main(['input.json', '--expect', digest(data(value=2))['digest']]), 1)

    def test_terminal_output_escapes_controls(self):
        request = data()
        request['message']['amount'] = '\u202e1'
        with patch.object(ir, 'load_workspace_json', return_value=request), \
                contextlib.redirect_stderr(io.StringIO()) as error:
            self.assertEqual(ir.main(['input.json']), 2)
        self.assertNotIn('\u202e', error.getvalue())

    def test_workspace_boundary(self):
        for path in ('../outside.json', '.hidden/data.json'):
            with self.assertRaises(TypedDataError):
                ir.load_workspace_json(path)


if __name__ == '__main__':
    unittest.main()
