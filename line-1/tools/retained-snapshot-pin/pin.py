#!/usr/bin/env python3
"""Replay two-source ZTO evidence only against a caller-retained exact-byte pin."""
import argparse
import hashlib
import hmac
import json
from pathlib import Path
import re
import runpy
import sys

A = runpy.run_path(str(Path(__file__).resolve().parents[1] /
                       'two-source-zto' / 'agreement.py'))
PIN = re.compile(r'[0-9a-f]{64}\Z')


class PinError(ValueError):
    pass


def review(raw, expected_sha256):
    """No IO. Neither derive nor replace the caller's expected pin."""
    if not isinstance(expected_sha256, str) or not PIN.fullmatch(expected_sha256):
        raise PinError('expected SHA-256 must be exactly 64 lowercase hex digits')
    if not isinstance(raw, bytes) or len(raw) > A['MAX_BYTES']:
        raise PinError('expected at most 100000 evidence bytes')
    actual = hashlib.sha256(raw).hexdigest()
    if not hmac.compare_digest(actual, expected_sha256):
        raise PinError('exact file bytes differ from the retained SHA-256')
    observation = A['validate_bundle'](A['B']['parse_json'](raw))
    return {
        'status': 'retained_file_pin_and_two_source_replay_match',
        'file_sha256': actual,
        'file_bytes': len(raw),
        'observation': observation,
        'limits': 'Equality to caller-supplied bytes, not provider authenticity, '
                  'a state proof, freshness, or independent custody of the pin.'
    }


def verify(path, expected_sha256):
    # Descriptor-relative reader refuses hidden/parent/absolute/symlink paths.
    # Validate the pin first, so malformed pin input never selects a file.
    if not isinstance(expected_sha256, str) or not PIN.fullmatch(expected_sha256):
        raise PinError('expected SHA-256 must be exactly 64 lowercase hex digits')
    return review(A['SAFE']['read_bytes'](path, A['MAX_BYTES']), expected_sha256)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('evidence', help='relative visible workspace evidence path')
    parser.add_argument('--expected-sha256', required=True,
                        help='exact-byte SHA-256 retained separately before review')
    args = parser.parse_args(argv)
    try:
        result = verify(args.evidence, args.expected_sha256)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0
    except (ValueError, A['B']['SnapshotError'], OSError, RecursionError) as exc:
        print('retained-snapshot-pin: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
