# Offline EIP-712 integer reviewer

Expose every reachable signed integer's exact decimal value, input form,
declared range and 32-byte encoding word. Preview the exact loss if it is
coerced to a binary64 JavaScript `Number`. The original integers always
determine the digest. Python standard library only; copy this entire folder
to run offline without the rest of the repository.

Run from the repository root:

```sh
python3 -B line-4/tools/integer-review/integer_review.py line-4/tools/integer-review/zto-payment.json --expect 0xf33e2506e5c103f98dbfe3feb6d4b87d55f1fad4e423dbaa8462465ff4ab9774
```

Tried: exit **0**, `matchesExpected: true`, three integer fields, and
`hasUnsafeJsonNumbers: false`. The inherited historical payment evidence uses
real Ethereum ZTO, `0xd782bdea4ef02a0bd391eb9089470c8080f0a68e`, transaction
`0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`.
Its exact `minimumRaw` is the decimal string **166357571280020680094504**.
A hypothetical Number conversion would instead represent
**166357571280020678115328**, a difference of **-1979176** raw units.
`requiresExactIntegerHandling` and `binary64CoercionChangesValue` are true.
The original digest remains unchanged. See `example-zto.json` for full output.
This is saved historical evidence, not a fresh observation, invoice, permit,
payment instruction or claim that ZTO supports this typed-data schema.

Replace `zto-payment.json` with `zto-numeric-literal.json` in that command to
see exit **1** and `hasUnsafeJsonNumbers: true`, while `matchesExpected`
remains true. That second fixture changes only the representation of the
same exact amount to a JSON integer literal. Python reads that literal
exactly; a JavaScript JSON consumer using Number could already lose its low
bits during parsing. It is an explicit representation experiment, not new
chain evidence. Its full output is `example-zto-numeric-literal.json`.
The example expected digest demonstrates execution; obtain an independent
expected digest for a real request.

Input is an EIP-712 object with `types`, `primaryType`, `domain` and `message`.
This tool does not accept or dispatch RPC requests. Nested structs, arrays,
domain integers and finite recursive values are included in schema order.
Booleans, addresses, bytes, numeric-looking strings declared as `string`,
empty arrays and unreachable type declarations contribute no integer entries.
The complete object is validated before the review begins.

Each integer entry gives its JSON Pointer, type, width, signedness, exact
decimal value and minimum/maximum, and its full big-endian word. Negative
signed integers are sign-extended to 256 bits. `inputForm` distinguishes
`json_integer`, `decimal_string` and `hex_string`. `parsedValue` preserves a
string's spelling, but is a decimal rendering of a parsed JSON integer;
the tool does not retain JSON whitespace, escape spelling or literal `-0`.
All potentially large report integers are **decimal strings** so the report
itself can pass through a JavaScript JSON parser without losing their bits.

`requiresExactIntegerHandling` means the magnitude exceeds **2^53 - 1**.
`unsafeJsonNumber` additionally requires a JSON integer literal, and its
aggregate is `hasUnsafeJsonNumbers`. Some integers outside that interval,
such as 2^53, are individually representable as Number; they are still
outside the safe integer interval where adjacent integers remain distinct.
`binary64Coercion` separately reports the nearest representable integer,
its signed delta (`nearest - original`), whether it differs, and whether it
would exceed the declared EIP-712 range. Conversion uses integer arithmetic
and round-to-nearest, ties-to-even; there is no float conversion in production.
It does not model `parseInt`, arbitrary formatting, arithmetic operations,
or what a particular wallet actually does. If precision was lost before this
file was created, it cannot reconstruct the original value without independent
evidence. A decimal or hex string preserves its integer, but later converting
it to Number can still lose bits. No input is rounded or rewritten here.

Exit **0** means no integer literals outside the safe interval and a matching
expected digest if supplied. String quantities can still require exact integer
handling and have lossy hypothetical conversions; inspect those fields even
on exit 0. Exit **1** means at least one such numeric literal or an expected
digest mismatch. Exit **2** means invalid input, unsafe file access or a bound
was exceeded, with no partial JSON report. None of these outcomes approves
signing or interprets quantities, units, token decimals, allowances, timestamps,
prices, ownership, consent, replay protection, settlement or contract support.
The tool never accesses a wallet, key, secret, environment variable or network,
and never signs, sends, posts or modifies inputs.

The unchanged ancestor encoder accepts strict UTF-8 JSON without duplicate
keys, floats or nonfinite numbers; files must be regular no-follow files below
cwd. Hidden paths, traversal and symlinks are refused. POSIX directory
descriptors are required. Limits: 65,536 input bytes, depth 48, 8,192 nodes,
64 types, 256 fields and eight array dimensions. The complete ASCII report,
including newline, is capped at 100,000 bytes. Excess fails closed, with no
truncated values. These are size limits, not a CPU-time guarantee. This tool
shares the ancestor encoder; it is not independent cryptographic validation.

```sh
python3 -B -m unittest discover -s line-4/tools/integer-review -v
```

Tried: **21 tests pass**, including every legal integer width's limits and
rejection immediately outside them, known signed/unsigned encoding words,
positive/negative ties, maximum-width rounding overflow, nested arrays,
finite recursive structs, input immutability, exact digest equality across
numeric spellings, CLI exit codes, strict parsing and report bounds. The
integer-only conversion also agrees with an independent runtime float oracle
on 1,536 deterministic positive/negative values. The **28 ancestor tests**
pass in scratch, including Keccak/Ether Mail vectors and file boundaries.
A detached copy passes all 21 new tests and the example CLI offline.
Logs: `line-4/check-results-31.json`.

Unchanged source/fixture hashes are in `provenance.json`. Primary references:
[EIP-712 encoding](https://eips.ethereum.org/EIPS/eip-712#definition-of-encodedata)
and [ECMAScript safe integer interval](https://tc39.es/ecma262/multipage/numbers-and-dates.html#sec-number.max_safe_integer).
The wall's small balance and flake represent preserving even the smallest
part of an exact quantity.
