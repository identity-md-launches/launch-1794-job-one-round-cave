# Transaction position check

Check that an Ethereum transaction's receipt points to the same transaction hash
at its claimed index in the canonical inclusion block. The inherited settlement
checker first checks successful execution, canonical block hash, confirmations and
the chosen finality requirement. This adds a cross-check against the block's
complete transaction-hash list, followed by fresh reads of the inclusion and
sampled head anchors. Python 3.9+ standard library only.

Run from the repository root, offline:

```sh
python3 -B line-3/tools/tx-position/position.py --demo
```

This returned `position_and_settlement_match`, exit 0, for a real ZTO pool
transaction (`0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`).
The receipt claimed index **181** and the provider's canonical block listed that
hash at index **181** among **498** transaction hashes. The saved inclusion is block
**26190898**. `live-evidence.json` contains actual compact public RPC responses;
`live-check.json` records the live result. The demo replays historical evidence.
It does not claim the transaction is settled now.

For your own transaction, select the hash and settlement policy independently:

```sh
python3 -B line-3/tools/tx-position/position.py --live --tx 0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7 --confirmations 12
```

`--live` reads Ethereum mainnet through Publicnode by default; `--rpc
https://eth.drpc.org` selects the other documented public source. The report
includes a replayable `sample`. To replay a saved sample, use `--replay PATH --tx
HASH` and supply the same independently selected confirmations and finality rule.
Finality is required unless `--allow-unfinalized` is explicitly set. The demo's
policy is illustrative, not an invoice or approval.

The live transport is read-only with a specific User-Agent, no redirects, no
environment proxy discovery, a 20-second limit per read and a 4 MB response
limit. The sample allows at most 16 reads, 1024 transaction hashes and 90 KB of
compact evidence. Replay opens only a visible workspace-relative regular JSON
file of at most 90 KB, without following symlinks; duplicate JSON keys and
nonfinite values are rejected by the inherited reader. Extra, missing or
reordered reads fail. Exit 0 means both settlement and position match; exit 1
means review is required; exit 2 means invalid input or unavailable public read.

Tests:

```sh
python3 -B -m unittest discover -s line-3/tools/tx-position -p 'test_*.py' -v
```

All 17 tests passed. They use the saved real ZTO evidence and mutate copies in
memory to reject a wrong index, absent transaction, duplicate hash, changed
receipt, changed block, changed canonical reread, reverted execution, policy
substitution and transcript mismatch. No fabricated response is presented as
live chain evidence.

This folder reuses unchanged `payment-witness/witness.py` and
`settlement-check/settlement.py`; keep those siblings when copying it. The
provider's block hash, transaction list and receipt remain assertions. This is
not a cryptographic transaction-trie or receipt proof, an independently
authenticated provider, a consensus proof, a current-balance check, or a
payment authorization. A later reorganization remains possible. The tool
never reads a key or wallet and never signs, sends, pays, posts or deploys.
