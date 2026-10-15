#!/usr/bin/env python3
"""Bind historical payment evidence while retaining exact client integer forms."""
import argparse
import json

from bind import bind_payment
from check import load
# bind/explain loads the fixed vendored modules; this file is a byte-for-byte
# copy of Line 4's integer reviewer, using the same trusted encoder.
from integer_review import review as integer_review

MAX_OUTPUT = 100_000


def render(report):
    text = json.dumps(report, indent=2, ensure_ascii=True, allow_nan=False) + '\n'
    if len(text.encode('ascii')) > MAX_OUTPUT:
        raise ValueError('precision payment report exceeds 100000 bytes')
    return text


def review(sample, policy, client, expected_domain, primary_type, expected_digest):
    """Pure API: all expectations are explicit, and no input is rewritten."""
    if expected_digest is None:
        raise ValueError('independently retained expected digest is required')
    bound = bind_payment(sample, policy, client, expected_domain, primary_type,
                         expected_digest, summary=True)
    integers = integer_review(client, expected_digest)
    alerts = []
    if not bound['paymentAccepted']:
        alerts.append('payment_policy_not_met')
    if not bound['comparison']['matchesCommitment']:
        alerts.append('client_differs_from_payment_commitment')
    if not bound['domainBinding']['domainAndPrimaryTypeMatch']:
        alerts.append('independent_domain_or_primary_type_mismatch')
    if bound['matchesExpectedDigest'] is not True or integers['matchesExpected'] is not True:
        alerts.append('retained_digest_mismatch')
    if integers['hasUnsafeJsonNumbers']:
        alerts.append('unsafe_integer_literal_in_client')
    result = {
        'accepted': bound['accepted'] and not integers['hasUnsafeJsonNumbers'],
        'state': 'exact_payment_review_matches' if not alerts else 'review_required',
        'alerts': alerts,
        'paymentAccepted': bound['paymentAccepted'],
        'clientMatchesPaymentCommitment': bound['comparison']['matchesCommitment'],
        'domainAndPrimaryTypeMatch': bound['domainBinding']['domainAndPrimaryTypeMatch'],
        'paymentMatchesExpectedDigest': bound['matchesExpectedDigest'],
        'paymentCommitment': bound['commitment']['digest'],
        'integerReview': integers,
        'providerAuthenticated': False,
        'evidenceMode': bound['evidenceMode'],
        'limits': 'Historical provider assertions, not current settlement or a state proof. '
                  'Caller policy, domain, type and digest must be independently chosen. '
                  'Exact strings can still lose precision if later coerced to Number. '
                  'A matching review authorizes no signature, token permit or payment.'}
    render(result)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('transcript')
    parser.add_argument('policy')
    parser.add_argument('client')
    parser.add_argument('--chain-id', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--version', required=True)
    parser.add_argument('--primary-type', required=True)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--verifier')
    group.add_argument('--no-verifier', action='store_true')
    parser.add_argument('--salt')
    parser.add_argument('--expect-digest', required=True)
    args = parser.parse_args(argv)
    expected = {'chainId': args.chain_id, 'name': args.name, 'version': args.version}
    if args.verifier is not None:
        expected['verifyingContract'] = args.verifier
    if args.salt is not None:
        expected['salt'] = args.salt
    try:
        result = review(load(args.transcript), load(args.policy), load(args.client),
                        expected, args.primary_type, args.expect_digest)
        print(render(result), end='')
        return 0 if result['accepted'] else 1
    except (ValueError, OSError, TypeError, KeyError, RecursionError):
        print('{"accepted":false,"state":"input_error"}')
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
