import copy
import importlib.util
import json
from pathlib import Path
import unittest

PATH = Path(__file__).with_name('position.py')
spec = importlib.util.spec_from_file_location('position', PATH)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PositionTests(unittest.TestCase):
    def setUp(self):
        self.sample = json.loads(PATH.with_name('live-evidence.json').read_text())
        self.expected = p.policy(p.DEMO_TX, 12, True)

    def check(self):
        return p.replay(self.sample, self.expected)

    def test_real_zto_transaction(self):
        result = self.check()
        self.assertTrue(result['accepted'])
        self.assertEqual(result['transactionIndex'], 181)
        self.assertEqual(result['transactionCount'], 498)

    def test_wrong_position_even_when_transaction_elsewhere(self):
        receipt = self.sample['reads'][8]['result']
        receipt['transactionIndex'] = '0xb6'
        self.assertIn('transaction_missing_at_receipt_index', self.check()['alerts'])

    def test_transaction_absent(self):
        self.sample['reads'][9]['result']['transactions'][181] = '0x' + 'a' * 64
        self.assertFalse(self.check()['accepted'])

    def test_duplicate_transaction(self):
        hashes = self.sample['reads'][9]['result']['transactions']
        hashes[182] = hashes[181]
        self.assertIn('duplicate_transaction_hash', self.check()['alerts'])

    def test_shorter_transaction_list(self):
        self.sample['reads'][9]['result']['transactions'] = []
        self.assertIn('transaction_missing_at_receipt_index', self.check()['alerts'])

    def test_changed_block_hash(self):
        self.sample['reads'][9]['result']['hash'] = '0x' + 'a' * 64
        self.assertIn('inclusion_block_changed', self.check()['alerts'])

    def test_receipt_changes_after_settlement(self):
        self.sample['reads'][8]['result']['blockHash'] = '0x' + 'a' * 64
        self.assertIn('receipt_changed', self.check()['alerts'])

    def test_anchor_changes_after_position_check(self):
        self.sample['reads'][10]['result']['hash'] = '0x' + 'a' * 64
        self.assertIn('canonical_anchor_changed', self.check()['alerts'])

    def test_reverted_receipt(self):
        self.sample['reads'][2]['result']['status'] = '0x0'
        # A declined settlement must not request the later position reads.
        self.sample['reads'] = self.sample['reads'][:8]
        result = self.check()
        self.assertFalse(result['accepted'])
        self.assertEqual(result['alerts'], ['settlement_policy_not_met'])

    def test_policy_substitution(self):
        self.expected['minimumConfirmations'] = 13
        with self.assertRaises(p.w.Error):
            self.check()

    def test_read_request_mismatch(self):
        self.sample['reads'][9]['params'] = ['latest', False]
        with self.assertRaises(p.w.Error):
            self.check()

    def test_boolean_numeric_request_confusion(self):
        self.sample['reads'][9]['params'][1] = 0
        with self.assertRaises(p.w.Error):
            self.check()

    def test_boolean_numeric_policy_confusion(self):
        self.sample['policy']['requireFinalized'] = 1
        with self.assertRaises(p.w.Error):
            self.check()

    def test_unused_read(self):
        self.sample['reads'].append(copy.deepcopy(self.sample['reads'][-1]))
        with self.assertRaises(p.w.Error):
            self.check()

    def test_invalid_policy_before_transport(self):
        with self.assertRaises(p.w.Error):
            p.collect({'transactionHash': p.DEMO_TX, 'minimumConfirmations': True,
                       'requireFinalized': True}, rpc_factory=lambda _: self.fail('transport constructed'))

    def test_replay_exact_envelope(self):
        self.sample['accepted'] = True
        with self.assertRaises(p.w.Error):
            self.check()

    def test_offline_demo(self):
        import contextlib
        import io
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = p.main(['--demo'])
        self.assertEqual(code, 0)
        self.assertTrue(json.loads(output.getvalue())['accepted'])


if __name__ == '__main__':
    unittest.main()
