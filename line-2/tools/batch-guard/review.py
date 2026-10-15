#!/usr/bin/env python3
"""Reproduce all source diagnostics in an explicitly supplied JSON batch."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import types

MAX_DOCUMENTS = 32
MAX_TOTAL_BYTES = 4_000_000
MAX_REPORT_BYTES = 100_000

def bounded_module():
    # Bootstrap only the fixed, trusted sibling; user inputs use its no-follow reader.
    source = Path(__file__).absolute().parent.parent / 'bounded-contract' / 'check.py'
    relative = source.relative_to(Path.cwd()).as_posix()
    if any(not p or p.startswith('.') for p in relative.split('/')):
        raise ValueError('run inside the workspace containing the sibling tools')
    # Open each component without following links, including the trusted bootstrap.
    import os
    import stat
    directory = os.open('.', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    leaf = None
    try:
        parts = relative.split('/')
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=directory)
            os.close(directory)
            directory = child
        leaf = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                       dir_fd=directory)
        if not stat.S_ISREG(os.fstat(leaf).st_mode):
            raise ValueError('trusted sibling must be a regular file')
        chunks, remaining = [], 1_000_001
        while remaining:
            chunk = os.read(leaf, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        code = b''.join(chunks)
        if len(code) > 1_000_000:
            raise ValueError('trusted sibling exceeds byte limit')
    finally:
        if leaf is not None:
            os.close(leaf)
        os.close(directory)
    module = types.ModuleType('repair_bounded_contract')
    module.__file__ = str(source)
    exec(compile(code, str(source), 'exec'), module.__dict__)
    return module



def dependencies():
    reader = bounded_module()
    path = Path(__file__).absolute().parent.parent / 'batch-source' / 'locate.py'
    relative = path.relative_to(Path.cwd()).as_posix()
    batch = types.ModuleType('guard_batch_source')
    batch.__file__ = str(path)
    exec(compile(reader.read_bytes(relative), str(path), 'exec'), batch.__dict__)
    _, engine, source, rules = batch.dependencies()
    return reader, engine, source, rules, batch


class Capture:
    """Capture each explicitly named input once, sharing an aggregate byte budget."""
    def __init__(self, reader):
        self.reader, self.cache, self.total = reader, {}, 0

    def read_bytes(self, name):
        if name not in self.cache:
            raw = self.reader.read_bytes(name)
            if self.total + len(raw) > MAX_TOTAL_BYTES:
                raise ValueError('aggregate input byte limit exceeded')
            self.cache[name] = raw
            self.total += len(raw)
        return self.cache[name]


def exact(a, b):
    """JSON tree equality including scalar types (true cannot stand in for 1)."""
    if type(a) is not type(b):
        return False
    if isinstance(a, dict):
        return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    if isinstance(a, list):
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return a == b


def review(reader, engine, source, rules, batch, report_name, contract_name,
           names, report_sha256=None):
    if not 1 <= len(names) <= MAX_DOCUMENTS or len(set(names)) != len(names):
        raise ValueError('supply 1–32 distinct document paths in report order')
    if report_sha256 is not None and not re.fullmatch('[0-9a-f]{64}', report_sha256):
        raise ValueError('report SHA-256 must be 64 lowercase hex digits')
    captured = Capture(reader)
    raw = captured.read_bytes(report_name)
    if len(raw) > MAX_REPORT_BYTES:
        raise ValueError('saved report exceeds 100,000 bytes')
    digest = hashlib.sha256(raw).hexdigest()
    base = {'matches': False, 'report_sha256': digest}
    if report_sha256 is not None and digest != report_sha256:
        return {**base, 'status': 'report_pin_mismatch'}, 1
    saved = source.strict_json(raw.decode('utf-8'))
    if not isinstance(saved, dict) or not isinstance(saved.get('files'), list):
        raise ValueError('expected a batch-source report')
    if len(saved['files']) != len(names):
        return {**base, 'status': 'document_set_mismatch'}, 1
    # Report contents never select paths: the caller supplies every file.
    if any(not isinstance(row, dict) or row.get('file') != name
           for row, name in zip(saved['files'], names)):
        return {**base, 'status': 'document_set_mismatch'}, 1
    if any('error' in row or not isinstance(row.get('sources'), dict)
           for row in saved['files']):
        raise ValueError('unreadable-input batch reports are not supported')
    contract = source.Source(captured.read_bytes(contract_name), contract_name)
    prepared = engine.prepare(contract.value)  # fail before reading documents
    documents = [source.Source(captured.read_bytes(name), name) for name in names]
    if (not exact(saved.get('contract'), contract.identity()) or any(
            not exact(row['sources'], {'contract': contract.identity(),
                                      'document': document.identity()})
            for row, document in zip(saved['files'], documents))):
        return {**base, 'status': 'source_identity_mismatch'}, 1
    rows = [{'file': name, **batch.locate_prepared(engine, rules, contract,
                                                 document, prepared)}
            for name, document in zip(names, documents)]
    failed = sum(not row['valid'] for row in rows)
    regenerated = {'valid': failed == 0,
                   'summary': {'checked': len(rows), 'passed': len(rows)-failed,
                               'failed': failed, 'unreadable': 0},
                   'contract': contract.identity(), 'files': rows}
    if not exact(saved, regenerated):
        return {**base, 'status': 'diagnostic_mismatch'}, 1
    return {**base, 'matches': True, 'status': 'batch_report_reproduced',
            'all_documents_valid': regenerated['valid'],
            'summary': regenerated['summary'],
            'error_count': sum(row['error_count'] for row in rows)}, 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', help='saved batch-source report')
    parser.add_argument('contract', help='explicit trusted contract path')
    parser.add_argument('documents', nargs='+', help='explicit document paths in report order')
    parser.add_argument('--report-sha256', help='optional independently retained report SHA-256')
    args = parser.parse_args(argv)
    try:
        report, code = review(*dependencies(), args.report, args.contract,
                              args.documents, args.report_sha256)
    except (ValueError, OSError, RecursionError, KeyError, IndexError) as exc:
        report, code = {'matches': False, 'status': 'input_error',
                        'error': str(exc)[:1000]}, 2
    print(json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False))
    return code


if __name__ == '__main__':
    sys.exit(main())
