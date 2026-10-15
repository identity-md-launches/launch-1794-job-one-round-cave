"""Cross-line regressions over saved real ZTO evidence, offline throughout."""
import contextlib
import copy
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import precision_payment as p
from check import check, load

HERE = Path(__file__).resolve().parent
DOMAIN = {'name': 'Read-only Payment Evidence', 'version': '1', 'chainId': 1}
DIGEST = '0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c'


class PrecisionPaymentTests(unittest.TestCase):
    def setUp(self):
        self.sample = load(HERE / 'example.transcript.json')
        self.policy = load(HERE / 'example.policy.json')
        self.client = load(HERE / 'example.typed-data.json')

    def review(self, domain=None, primary='PaymentEvidence', expected=DIGEST):
        return p.review(self.sample, self.policy, self.client,
                        DOMAIN if domain is None else domain, primary, expected)

    def test_real_zto_exact_string(self):
        r = self.review()
        self.assertTrue(r['accepted'])
        self.assertTrue(r['paymentAccepted'])
        self.assertFalse(r['providerAuthenticated'])
        q = r['integerReview']['integers'][1]
        self.assertEqual(q['exactDecimal'], '166357571280020680094504')
        self.assertEqual(q['binary64Coercion']['deltaDecimal'], '-1979176')
        self.assertTrue(q['requiresExactIntegerHandling'])
        self.assertFalse(q['unsafeJsonNumber'])

    def test_equal_digest_unsafe_numeric_literal_rejected(self):
        self.client['message']['minimumRaw'] = int(self.policy['minimum_raw'])
        r = self.review()
        self.assertTrue(r['clientMatchesPaymentCommitment'])
        self.assertTrue(r['integerReview']['matchesExpected'])
        self.assertFalse(r['accepted'])
        self.assertEqual(r['alerts'], ['unsafe_integer_literal_in_client'])

    def test_one_unit_change_rejected(self):
        self.client['message']['minimumRaw'] = str(int(self.policy['minimum_raw']) + 1)
        r = self.review()
        self.assertTrue(r['paymentAccepted'])
        self.assertFalse(r['accepted'])
        self.assertIn('client_differs_from_payment_commitment', r['alerts'])

    def test_actual_rounded_amount_rejected(self):
        self.client['message']['minimumRaw'] = '166357571280020678115328'
        self.assertFalse(self.review()['accepted'])

    def test_wrong_prior_digest_rejected(self):
        r = self.review(expected='0x' + '12' * 32)
        self.assertFalse(r['accepted'])
        self.assertIn('retained_digest_mismatch', r['alerts'])

    def test_expected_digest_required(self):
        with self.assertRaises(ValueError):
            self.review(expected=None)

    def test_independent_domain_and_type_are_gates(self):
        for domain, primary in [({**DOMAIN, 'chainId': 2}, 'PaymentEvidence'),
                                ({**DOMAIN, 'name': 'Other'}, 'PaymentEvidence'),
                                (DOMAIN, 'Other')]:
            r = self.review(domain, primary)
            self.assertTrue(r['clientMatchesPaymentCommitment'])
            self.assertFalse(r['accepted'])
            self.assertIn('independent_domain_or_primary_type_mismatch', r['alerts'])

    def test_no_verifier_is_explicit(self):
        domain = {**DOMAIN, 'verifyingContract': self.client['message']['token']}
        self.assertFalse(self.review(domain)['accepted'])

    def test_transcript_cannot_change_independent_policy(self):
        self.sample['policy']['minimum_raw'] = '1'
        with self.assertRaises(ValueError):
            self.review()

    def test_matching_request_cannot_bypass_payment_shortfall(self):
        self.policy['minimum_raw'] = str(int(self.policy['minimum_raw']) + 1)
        self.sample['policy'] = copy.deepcopy(self.policy)
        evidence = check(self.sample, self.policy)
        self.client = evidence['typedData']
        r = self.review(expected=evidence['commitment']['digest'])
        self.assertTrue(r['clientMatchesPaymentCommitment'])
        self.assertTrue(r['integerReview']['matchesExpected'])
        self.assertFalse(r['paymentAccepted'])
        self.assertFalse(r['accepted'])

    def test_hex_string_preserves_exact_value(self):
        self.client['message']['minimumRaw'] = hex(int(self.policy['minimum_raw']))
        r = self.review()
        self.assertTrue(r['accepted'])
        self.assertEqual(r['integerReview']['integers'][1]['inputForm'], 'hex_string')

    def test_immutability_and_no_network(self):
        before = copy.deepcopy((self.sample, self.policy, self.client, DOMAIN))
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('network')):
            self.assertTrue(self.review()['accepted'])
        self.assertEqual(before, (self.sample, self.policy, self.client, DOMAIN))

    def test_no_large_json_integers_in_output(self):
        def walk(x):
            if type(x) is int:
                self.assertLessEqual(abs(x), 2**53 - 1)
            elif type(x) is dict:
                for v in x.values(): walk(v)
            elif type(x) is list:
                for v in x: walk(v)
        walk(json.loads(p.render(self.review())))

    def test_report_bound_fails_closed(self):
        with patch.object(p, 'MAX_OUTPUT', 100), self.assertRaises(ValueError):
            self.review()

    def test_cli_exit_codes_and_no_partial_output(self):
        args = [str(HERE / 'example.transcript.json'), str(HERE / 'example.policy.json'),
                str(HERE / 'example.typed-data.json'), '--chain-id', '1',
                '--name', DOMAIN['name'], '--version', '1', '--primary-type',
                'PaymentEvidence', '--no-verifier', '--expect-digest', DIGEST]
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(p.main(args), 0)
        self.assertTrue(json.loads(out.getvalue())['accepted'])
        self.client['message']['minimumRaw'] = int(self.policy['minimum_raw'])
        with patch.object(p, 'load', side_effect=[self.sample, self.policy, self.client]), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(p.main(args), 1)
        self.assertFalse(json.loads(out.getvalue())['accepted'])
        with patch.object(p, 'MAX_OUTPUT', 100), contextlib.redirect_stdout(io.StringIO()) as out:
            self.assertEqual(p.main(args), 2)
        self.assertEqual(json.loads(out.getvalue()), {'accepted': False, 'state': 'input_error'})

    def test_strict_input_boundary(self):
        for name in ('../outside', '.hidden'):
            with self.assertRaises(ValueError): load(name)
        for raw in (b'{"a":1,"a":2}', b'NaN', b'1.5'):
            from check import typed
            with self.assertRaises(ValueError): typed.loads_bounded(raw)


if __name__ == '__main__':
    unittest.main(verbosity=2)
