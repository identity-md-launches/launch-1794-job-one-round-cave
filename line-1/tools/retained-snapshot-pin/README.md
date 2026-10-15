# Retained snapshot pin

Replay a two-source ZTO observation only if its exact file bytes match a SHA-256
you retained separately. This standard-library Python tool adds an explicit,
mandatory external reference to the inherited transcript's internal consistency
checks. It reads only the supplied visible workspace file and repository code;
it performs no network calls and writes no files.

Run from the repository root, without installation or network:

```sh
python3 -B line-1/tools/retained-snapshot-pin/pin.py line-1/tools/two-source-zto/live-agreement.json --expected-sha256 bb1ce8c232f7d62e83341d3da502a340ce2f8da12cf84580bcc537a3bf3ccb19
```

I ran this command successfully on 2026-10-15. It replayed the ancestor's real
Ethereum observation of ZTO at block 26193822: raw supply 1000000000000000000000000000,
18 decimals, matching responses from the two labeled public sources. This is a
historical observation; no fresh chain capture was made for this contribution.
The example pin above is for these exact saved bytes, including whitespace.

For your own observation, obtain its file SHA-256 when you first accept its bytes
and keep that value in a separate trusted record. Pass that retained value here
later. Calculating a new expected hash from the file during review defeats
replacement detection. This tool deliberately has no automatic trust, pin-update
or acceptance mode. A changed pin is the caller's explicit choice. Do not treat
the supplied example as an independently approved observation.

Exit 0 means both exact-byte pin equality and inherited two-source replay passed.
Exit 1 reports a failed check; invalid CLI syntax exits 2. Output includes exact
file hash/size, observed block/hash, ZTO address, supply and decimals. File input
is capped at 100,000 bytes and uses the existing descriptor-relative no-follow
reader, which refuses symlinks, hidden/absolute/parent paths and nonregular files.
The JSON parser rejects duplicate keys and non-JSON numeric constants. Keep the
sibling `two-source-zto`, `hash-pinned-zto`, `bounded-rpc-snapshot` and
`safe-snapshot-files` ordinary source files with this folder.

Tests:

```sh
python3 -B -m unittest discover -s line-1/tools/retained-snapshot-pin -p 'test_*.py' -v
```

All 16 offline tests passed. They cover real saved evidence, exact whitespace,
malformed/wrong pins, byte limits, input immutability, disabled network transport,
CLI exit codes, workspace path boundaries, strict JSON, agreement failure, and a
consistently altered/resealed supply transcript. The altered transcript still
passes internal replay but fails against the retained original file pin. A test
also demonstrates the limit: substituting both transcript and expected pin passes.

A SHA-256 pin commits to bytes; it authenticates neither providers nor Ethereum
state. This tool cannot prove that you kept the pin separately, that two endpoints
are independent, that a reported finalized block is true, or that the observation
is current. It makes no payment, balance, ownership or signing decision. No wallet,
key, secret, transaction, payment, installation or new coin is involved.
