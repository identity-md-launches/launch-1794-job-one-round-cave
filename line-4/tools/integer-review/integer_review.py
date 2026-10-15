#!/usr/bin/env python3
"""Review exact EIP-712 integers and binary64 coercion loss, entirely offline."""
import argparse
import json
import sys

from typed_digest import (ARRAY, INTEGER, Encoder, TypedDataError, digest,
                          load_workspace_json, parse_hex, parse_integer)

MAX_SAFE_INTEGER = (1 << 53) - 1
MAX_REPORT_BYTES = 100_000


def binary64_integer(value):
    """Nearest binary64 integer, ties to even; integer arithmetic only.

    Called only for validated EIP-712 integers (at most 256 bits), so no
    overflow, fractional result or subnormal case is possible.
    """
    magnitude = abs(value)
    shift = max(0, magnitude.bit_length() - 53)
    if not shift:
        return value
    quotient, remainder = divmod(magnitude, 1 << shift)
    halfway = 1 << (shift - 1)
    if remainder > halfway or (remainder == halfway and quotient % 2):
        quotient += 1
    nearest = quotient << shift
    return -nearest if value < 0 else nearest


def render(report):
    text = json.dumps(report, ensure_ascii=True, indent=2) + '\n'
    if len(text.encode('ascii')) > MAX_REPORT_BYTES:
        raise TypedDataError('integer review exceeds 100000-byte output limit')
    return text


def review(data, expected=None):
    # Validate the whole object before walking any reachable integer values.
    hashes = digest(data)
    expected_bytes = parse_hex(expected, 32) if expected is not None else None
    encoder = Encoder(data['types'])
    integers = []

    def visit(kind, value, path):
        array = ARRAY.fullmatch(kind)
        if array:
            for index, child in enumerate(value):
                visit(array.group(1), child, path + '/' + str(index))
        elif kind in data['types']:
            for field in data['types'][kind]:
                # Validated field identifiers contain no JSON Pointer escapes.
                visit(field['type'], value[field['name']], path + '/' + field['name'])
        elif INTEGER.fullmatch(kind):
            match = INTEGER.fullmatch(kind)
            number = parse_integer(value)
            width = int(match.group(2))
            signed = match.group(1) == 'int'
            lower = -(1 << (width - 1)) if signed else 0
            upper = (1 << (width - int(signed))) - 1
            nearest = binary64_integer(number)
            outside_safe = abs(number) > MAX_SAFE_INTEGER
            form = ('json_integer' if type(value) is int else
                    'hex_string' if value.lower().startswith('0x') else 'decimal_string')
            integers.append({
                'path': path, 'type': kind, 'widthBits': width, 'signed': signed,
                'inputForm': form, 'parsedValue': str(value),
                'exactDecimal': str(number), 'minimumDecimal': str(lower),
                'maximumDecimal': str(upper),
                'word': '0x' + encoder.value_word(kind, value).hex(),
                'requiresExactIntegerHandling': outside_safe,
                'unsafeJsonNumber': form == 'json_integer' and outside_safe,
                'binary64Coercion': {
                    'nearestIntegerDecimal': str(nearest),
                    'deltaDecimal': str(nearest - number),
                    'changesValue': nearest != number,
                    'outsideDeclaredRange': not lower <= nearest <= upper,
                },
            })
            # Refuse the complete report rather than silently omitting values.
            render({'integers': integers})

    visit('EIP712Domain', data['domain'], '/domain')
    visit(data['primaryType'], data['message'], '/message')
    report = {
        'reviewVersion': 1, **hashes, 'integers': integers,
        'integerCount': len(integers),
        'requiresExactIntegerHandling': any(x['requiresExactIntegerHandling'] for x in integers),
        'hasUnsafeJsonNumbers': any(x['unsafeJsonNumber'] for x in integers),
        'binary64CoercionChangesValue': any(x['binary64Coercion']['changesValue'] for x in integers),
        'interpretation': 'Original exact integers determine the digest. Binary64 values '
                          'are hypothetical nearest-even conversions, never substituted. '
                          'Strings preserve input values but later Number coercion may lose '
                          'precision. No units, token decimals or business meaning are inferred. '
                          'No numeric cues does not mean approval.',
    }
    if expected_bytes is not None:
        report['matchesExpected'] = expected_bytes.hex() == hashes['digest'][2:]
    render(report)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', help='typed-data JSON beneath cwd; max 65536 bytes; no symlinks')
    parser.add_argument('--expect', help='independently obtained exact 32-byte digest')
    args = parser.parse_args(argv)
    try:
        report = review(load_workspace_json(args.input), args.expect)
        print(render(report), end='')
        return int(report['hasUnsafeJsonNumbers'] or not report.get('matchesExpected', True))
    except (ValueError, OSError, RecursionError) as exc:
        print('integer-review: ' + json.dumps(str(exc), ensure_ascii=True), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
