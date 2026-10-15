"""Regression tests use in-memory inputs and real read-only inherited records."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('batch_guard', Path(__file__).with_name('review.py'))
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)


class Memory:
    def __init__(self, files):
        self.files, self.opened = files, []

    def read_bytes(self, name):
        self.opened.append(name)
        if name not in self.files:
            raise OSError('missing explicit input')
        return self.files[name]


class GuardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reader, cls.engine, cls.source, cls.rules, cls.batch = guard.dependencies()

    def setUp(self):
        self.files = {
            'contract.json': b'{"type":"object","required":["x"],"properties":{"x":{"type":"integer"}},"additionalProperties":false}',
            'good.json': b'{"x": 1}',
            'bad.json': '{\r\n "x":"é", "extra":true\r\n}'.encode()}
        self.names = ['good.json', 'bad.json']
        self.memory = Memory(self.files)
        self.regenerate()
        self.memory.opened.clear()

    def regenerate(self):
        c = self.source.Source(self.files['contract.json'], 'contract.json')
        self.saved, _ = self.batch.check_all(self.memory, self.engine, self.source,
                                           self.rules, c, self.names)
        self.save()

    def save(self):
        self.files['report.json'] = json.dumps(self.saved).encode()

    def review(self, names=None, pin=None):
        return guard.review(self.memory, self.engine, self.source, self.rules,
                            self.batch, 'report.json', 'contract.json',
                            self.names if names is None else names, pin)

    def mismatch(self, status):
        result, code = self.review()
        self.assertEqual(code, 1)
        self.assertEqual(result['status'], status)
        self.assertFalse(result['matches'])

    def test_mixed_report_reproduced(self):
        result, code = self.review()
        self.assertEqual(code, 0)
        self.assertEqual(result['status'], 'batch_report_reproduced')
        self.assertFalse(result['all_documents_valid'])
        self.assertEqual(result['error_count'], 2)
        self.assertEqual(result['summary'], {'checked':2,'passed':1,'failed':1,'unreadable':0})
        self.assertEqual(self.memory.opened, ['report.json','contract.json','good.json','bad.json'])

    def test_all_valid(self):
        self.files['bad.json'] = b'{"x":2}'
        self.regenerate()
        result, code = self.review()
        self.assertEqual(code, 0)
        self.assertTrue(result['all_documents_valid'])

    def test_missing_property_anchor(self):
        self.files['bad.json'] = b'{}'; self.regenerate()
        self.assertFalse(self.saved['files'][1]['errors'][0]['document_source']['present'])
        self.assertEqual(self.review()[1], 0)

    def test_changed_bytes_even_same_value(self):
        self.files['good.json'] += b' '
        self.mismatch('source_identity_mismatch')

    def test_changed_contract(self):
        self.files['contract.json'] += b'\n'
        self.mismatch('source_identity_mismatch')

    def test_dropped_row(self):
        self.saved['files'].pop(); self.save()
        self.mismatch('document_set_mismatch')

    def test_reordered_documents(self):
        result, code = self.review(names=list(reversed(self.names)))
        self.assertEqual((result['status'],code), ('document_set_mismatch',1))
        self.assertEqual(self.memory.opened, ['report.json'])

    def test_mutations_of_diagnostics_and_summary(self):
        original = copy.deepcopy(self.saved)
        for mutation in ('range', 'boolean', 'removed', 'preview', 'order', 'summary', 'extra'):
            with self.subTest(mutation=mutation):
                self.saved = copy.deepcopy(original)
                row = self.saved['files'][1]
                error = row['errors'][0]
                if mutation == 'range': error['document_source']['value']['start']['byte_offset'] += 1
                if mutation == 'boolean': error['document_source']['value']['start']['line'] = True
                if mutation == 'removed': row['errors'].pop()
                if mutation == 'preview': error['observed']['preview'] = 'different'
                if mutation == 'order': row['errors'].reverse()
                if mutation == 'summary': self.saved['summary']['failed'] = 0
                if mutation == 'extra': self.saved['approved'] = True
                self.save(); self.mismatch('diagnostic_mismatch')

    def test_embedded_paths_never_read(self):
        self.saved['files'][0]['sources']['document']['file'] = 'forbidden/path'
        self.save(); self.mismatch('source_identity_mismatch')
        self.assertNotIn('forbidden/path', self.memory.opened)

    def test_pin(self):
        pin = hashlib.sha256(self.files['report.json']).hexdigest()
        self.assertEqual(self.review(pin=pin)[1],0)
        self.memory.opened.clear()
        self.files['report.json'] += b' '
        result, code = self.review(pin=pin)
        self.assertEqual((result['status'],code), ('report_pin_mismatch',1))
        self.assertEqual(self.memory.opened,['report.json'])

    def test_invalid_pin(self):
        with self.assertRaises(ValueError): self.review(pin='bad')
        self.assertEqual(self.memory.opened,[])

    def test_bad_counts_and_duplicate_paths(self):
        for names in ([], ['good.json']*2, [str(i) for i in range(33)]):
            with self.assertRaises(ValueError): self.review(names=names)
        self.assertEqual(self.memory.opened,[])

    def test_unreadable_report_unsupported(self):
        self.saved['files'][1] = {'file':'bad.json','error':'malformed'}
        self.save()
        with self.assertRaises(ValueError): self.review()
        self.assertEqual(self.memory.opened,['report.json'])

    def test_malformed_document_fails(self):
        self.files['bad.json'] = b'{'
        with self.assertRaises(ValueError): self.review()

    def test_duplicate_report_keys(self):
        self.files['report.json'] = b'{"files":[],"files":[]}'
        with self.assertRaises(ValueError): self.review()

    def test_contract_before_documents(self):
        self.files['contract.json'] = b'{"type":"object","unknown":true}'
        with self.assertRaises(ValueError): self.review()
        self.assertEqual(self.memory.opened,['report.json','contract.json'])

    def test_budgets(self):
        with patch.object(guard, 'MAX_REPORT_BYTES', 1):
            with self.assertRaises(ValueError): self.review()
        with patch.object(guard, 'MAX_TOTAL_BYTES', len(self.files['report.json'])):
            with self.assertRaises(ValueError): self.review()

    def test_contract_also_document_captured_once(self):
        self.files['contract.json'] = b'{"type":"object"}'
        self.names = ['contract.json']; self.regenerate(); self.memory.opened.clear()
        self.assertEqual(self.review()[1],0)
        self.assertEqual(self.memory.opened,['report.json','contract.json'])

    def test_real_records(self):
        c = 'line-2/tools/ordered-deliverables/record.strict.contract.json'
        names = ['dist/line-2/29.json', 'dist/line-2/30.json']
        files = {n:self.reader.read_bytes(n) for n in [c,*names]}
        memory = Memory(files)
        report, code = self.batch.check_all(memory, self.engine, self.source, self.rules,
                            self.source.Source(files[c],c), names)
        self.assertEqual(code,0)
        files['report.json'] = json.dumps(report).encode()
        result, code = guard.review(memory,self.engine,self.source,self.rules,self.batch,
                                   'report.json',c,names)
        self.assertEqual(code,0)
        self.assertTrue(result['all_documents_valid'])

    def test_real_reader_path_boundary(self):
        for name in ('/etc/passwd','../outside','line-2/../x','.hidden'):
            with self.assertRaises(ValueError): self.reader.read_bytes(name)

    def test_cli_actual_demo(self):
        self.assertEqual(guard.main(['line-2/tools/batch-guard/records.report.json',
            'line-2/tools/ordered-deliverables/record.strict.contract.json',
            'dist/line-2/29.json','dist/line-2/30.json']),0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
