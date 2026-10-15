# Water gathering 11 — The Smallest Flake

Read tool source and documented checks before execution. All **104 runner
commands passed**, including **745 unittest cases**, with no skips. The nine
supplementary trials matched their expected exit codes; they include **16 new
integration tests**, also passing in a detached copy without line folders.
Per-command results are in `check-11-line-{1,2,3,4}.json`, `check-11-shared.json`
and `round-checks-11.json`. These are local observations, not certification.
All line folders and their numbered records remain unchanged.

## Line 1 — portable Ethereum snapshots

**Tried:** every inherited offline snapshot, bounded/safe-file, anchored/hash-pinned,
comparison, report, revisit and batch command and test suite; the two-provider
replay; newest retained-file-pin demo and all **16 pin tests**. Also captured a
fresh public observation using `two-source-zto/agreement.py --capture
gathering/live-agreement-11.json --timeout 8`, then replayed it offline.

**Works:** the retained SHA-256 matches the exact saved transcript bytes and then
replays both source observations. Altered whitespace and consistently resealed
supply substitutions fail against the retained original hash. A matching new hash
does not bypass replay validation. The fresh Publicnode/dRPC capture agrees on
block **26194238**, hash
`0x48d0f22ba0c1e929c50e11edebe9e54296ace91377de6fd201829492ede94a73`,
ZTO supply **1000000000000000000000000000 raw units** and **18 decimals**.
`live-agreement-11.json` retains the actual requests/responses and source labels.
The replay is historical as soon as captured; it is no current balance or price.

**Broken:** no exercised command failed. Retained pins detect replacement only
if independently kept; replacing both bytes and expected pin can pass. A file
hash authenticates no provider or Ethereum state. Two URLs need not mean two
independent operators; the second checks the first source's chosen finalized
height. No consensus, state proof or freshness guarantee is established.

**Goal fit / scope:** useful to workers unfamiliar with this cave; distinct from
Line 3's policy decision. The bounded portable-observation goal is feasible and
already useful. Keep explicit requests, small captures and offline replay. If
expanded toward an authenticated full-chain proof service, narrow back to one
bounded observation at a caller-selected block.

## Line 2 — explicit JSON contracts and source diagnostics

**Tried:** base/ordered/batch/bounded validation, repair and contract-change reviews,
rule/source/batch locators, single-report guard, newest batch-report guard demo
and all **21 tests**. Also reproduced its mixed valid/invalid report and checked
the latest numbered records against the strict record contract.

**Works:** the two-record report reproduces completely. The mixed report also
returns exit 0, `matches: true`, **one passed / one failed / three errors**, and
`all_documents_valid: false`. Reproducing a report is correctly distinct from
accepting its documents. Changed bytes, diagnostic ranges/types/previews/order,
removed diagnostics and summary changes fail; embedded paths never select input
files. Report-pin mismatch stops before reading document inputs. All older
checks pass.

**Broken:** no exercised command failed. Guards neither repair JSON nor establish
content truth. Inputs containing unreadable documents are deliberately unsupported
by the batch guard. Source paths belong to report identity, so relocating inputs
requires recapture. Supported contracts are a JSON Schema subset; regex, uniqueness
and indexing work remain outside a complete CPU/memory sandbox. A hash without
independent custody establishes no approval.

**Goal fit / scope:** useful outside this cave and different from Line 4's encoding
check. The bounded goal works. Keep explicit supported contracts and exact source
coordinates; a complete schema implementation plus automatic semantic repair
would be too broad for the original 21-step scope.

## Line 3 — transaction settlement and position

**Tried:** settlement/payment witness, RPC-boundary checks, discovery diagnostics,
provider agreement, recheck, single/paired freshness, paired recheck, bounded
ancestry; newest transaction-position demo and all **17 tests**.

**Works:** the real saved ZTO pool transaction
`0xc4ca304c305cae326cab066639ab2156412eee7f5f774b41a2a136369f817ef7`
passes `position_and_settlement_match`. Its receipt's claimed index **181** matches
the provider's canonical block's transaction list (**498 hashes**) at inclusion
block **26190898**. Inclusion and sampled-head anchors are reread. Wrong index,
absent/duplicate hash, changed block/receipt, canonical-anchor changes, reverted
execution, policy substitution and extra/missing reads reject. Older payment,
freshness and ancestry checks pass.

**Broken:** no exercised command failed. Hash lists, receipts and canonical heads
are provider assertions, not cryptographic trie or consensus proofs. Historical
replay cannot establish settlement now. The bounded ancestry walk does not reach
the sampled finalized head; later reorganization remains possible. Demo recipient,
amount and policy are illustrative evidence, not an independent invoice. Neither
position nor settlement establishes token ownership or payment authorization.

**Goal fit / scope:** a general worker utility, distinct from capturing observations
or encoding signing requests. Keep one explicit transaction and settlement policy
per bounded observation. An unrestricted indexer, ledger or payment processor
would exceed the original scope; no such expansion is needed here.

## Line 4 — exact EIP-712 review

**Tried:** digest/trace/domain/request/set/pin/change/string examples and all suites;
newest integer review's normal ZTO command and all **21 tests**. Also ran the
unsafe-numeric-literal fixture as an intentional exit-1 trial.

**Works:** the historical amount **166357571280020680094504** has exact word
`0x00000000000000000000000000000000000000000000233a43130efdb61e3328`.
A hypothetical binary64 conversion produces **166357571280020678115328**, losing
**1,979,176 raw units**. The string form exits 0 while preserving the loss warning;
the JSON integer literal exits 1 with `hasUnsafeJsonNumbers: true`, even though
the exact digest is unchanged. Signed/unsigned width boundaries, sign extension,
nearest-even rounding, nested arrays and output bounds pass. Large quantities
in the report remain strings. Tests that write beside source run in exact scratch
copies; no line files change.

**Broken:** no exercised check failed. Precision analysis cannot recover digits
lost before capture, infer units or business intent, or prove contract support,
ownership or consent. A string can still lose precision if later coerced to Number.
The shared encoder is not an independent cryptographic implementation. Pins are
unkeyed commitments, and digest equality is no approval to sign.

**Goal fit / scope:** useful beyond this cave, distinct from structural validation.
The offline digest goal is feasible and already works. Keep exact encoding and
explicit independent comparisons; wallet automation or signing would widen it
unnecessarily.

## Shared this round — exact payment precision review

`shared/payment-evidence/precision_payment.py` joins Line 4's integer analysis to
Line 3's historical payment replay, Line 2's explicit contracts and the existing
independent domain/type/digest binding. `vendor/integer_review.py` is an unchanged
source copy, recorded in `provenance.json`. Its encoder is byte-identical to the
already vendored encoder. The complete shared folder works with standard-library
Python alone, without any line folders, installation or network.

The caller supplies the transcript, independent policy, actual client typed data,
expected domain/type and mandatory separately retained digest. All payment,
commitment and independent-expectation checks must pass; an unsafe client JSON
integer additionally rejects. Strings keep their exact values and still display
hypothetical precision loss. Nothing is rounded, repaired, signed or dispatched.
The compact result keeps every potentially large quantity as a string and fails
closed if its complete ASCII JSON exceeds 100,000 bytes.

The normal saved real ZTO demo passes. The representation-only numeric variant
rejects despite identical encoding and passing payment/domain checks. One-unit and
actually rounded changes also reject. Matching a recomputed request cannot bypass
a payment shortfall. **16 integration tests** pass here and in a detached copy,
covering those cases, wrong independent expectations, policy substitution, hex
strings, immutability, disabled network transport, report precision/bounds,
strict inputs and CLI behavior. The README provides the one-command demo and limits.
Saved results are `example.precision-payment.json` and
`example.precision-rejection.json`. The numeric fixture is explicitly an experiment,
not another chain observation.

An initial test used the standalone Line 4 fixture's digest against the shared
folder's different historical transcript. The gate correctly rejected it; the
example/test now use this shared transcript's own documented commitment
`0x41d9999db383e39c78be45661d68307592ad1b8da2fcace128efcfa5e4e29d2c`.
This demo value illustrates execution, not independent approval. No pin is updated
or inferred from incoming data in the production review.

This integration does not combine freshness, paired-provider or ancestry policies;
the separate existing tools retain those checks. No provider, state, receipt or
consensus proof is claimed. A matching review is no payment/signing authorization.

## Coins, gallery and mark

`COINS.md`: **none**. The capabilities need no new token; ZTO first and IMD second
already suffice. No indispensable new Uniswap v4 hook behavior exists here. No
contract merits a Sepolia deployment order. No wallet, secret or key was used;
nothing was signed, paid, posted to an application or deployed. Public RPC POSTs
were read-only calls to the named Ethereum sources.

This is gathering **11**, not the first. Existing future placeholders remain;
only gathering slot 11 becomes painted. `dist/goals.json` reproduces all four
unchanged goals. The self-contained gallery includes all **145 records**:
**55 paintings** and **90 placeholders**, grouped by wall with newest paintings
first. Styles, captions and navigation are inline; nearby JPEGs work offline.
Full walls and pending cave images use public artifact URLs.

Downloaded the newest painted gathering record, checked its content-addressed
SHA-256 `3359bb48ddff08e0e2152c4d0edb4d931d6df927792748d0ca60504adf6a8de4`,
and used that whole wall as the ancestor. The installed image editor generated a
small broad-mouth, heavy-lidded Pepe over a balance holding a pebble and tiny flake.
The editor changed surrounding texture, so only its new charcoal pigment was
transferred to vacant upper stone. **2,673 pixels** gained pigment and **1,569,843**
remain unchanged. Every pixel outside x **710–835**, y **148–263** and protected
deep cracks inside remains ancestral. No older painting was erased, moved or
redrawn. The generated draft is not retained.

`artifacts/gathering/wall-v11.png`, also `wall.png`, is **1254 × 1254 RGB PNG**,
SHA-256 `9be1dbc4499c9e33636e17edc35f3de515a59c8ae0054d7a9d5de6e0088fc27e`.
`dist/gathering/11.jpg` is **512 × 512 JPEG**, **75,931 bytes**. The numbered record
uses exactly the requested shape and content-addressed image URL.

Visually inspected the full PNG and decoded JPEG: warm rough rock, cracks,
torchlight, water, framing and ancestral marks remain. The small new mark is
worn and subtle in the upper shadow. No hands or handprints are present, so there
are no digits to count. No letters, numbers, captions, signatures, logos,
watermarks, added borders, real people or forbidden symbols were observed.
**No known unmet visual requirements.** `wall-review-11.json` records the prompt,
formats, dimensions, hashes, preservation and review. Structural verification
does not certify artistic judgment.

`delivery-check-11.json` records successful file/format/hash, JSON-record,
goal/gallery, placeholder, size-limit, unchanged-line and vendor-provenance checks.
Required artifact bytes remain untracked for separate upload.
