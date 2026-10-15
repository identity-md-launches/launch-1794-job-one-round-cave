# JSON batch report guard

Before following source coordinates from a saved batch report, reproduce every
file's diagnostics against the exact contract and documents you explicitly name.
This offline, standard-library Python tool extends the inherited single-document
guard to ordered batches without letting embedded report paths choose input files.
Python 3.10+ and POSIX no-follow opens are required; no installation is needed.

From the repository root, one command shows it working on actual inherited records:

```sh
python3 -B line-2/tools/batch-guard/review.py line-2/tools/batch-guard/records.report.json line-2/tools/ordered-deliverables/record.strict.contract.json dist/line-2/29.json dist/line-2/30.json
```

Tried: exit **0**, `batch_report_reproduced`, `matches: true`, two documents
valid, zero errors. Exact saved source identities are in `records.report.json`.

A matching report can describe invalid documents. This second command reproduces
three violations in the inherited intentionally invalid build-report example,
alongside a passing example; neither example asserts a real build result:

```sh
python3 -B line-2/tools/batch-guard/review.py line-2/tools/batch-guard/mixed.report.json line-2/tools/json-contract/report.contract.json line-2/tools/json-contract/report.example.json line-2/tools/rule-locator/report.invalid.json
```

Tried: exit **0**, `matches: true`, `all_documents_valid: false`, one passed,
one failed, three errors reproduced. Exit 0 means the **saved report matches**;
use `all_documents_valid` separately before accepting the documents.

To create a report, capture stdout from the sibling
`batch-source/locate.py CONTRACT DOCUMENT...`. Its exit 1 denotes structural
violations and still produces a usable report. Exit-2 batches containing
unreadable/malformed inputs are deliberately unsupported by this guard: repair
those input errors and recapture first. The guard itself fails closed on malformed
JSON, invalid contracts, missing files or refused paths; it never verifies a partial batch.

## What it checks

The same ordered document set, top-level contract identity, per-document
contract/document identities (relative path, SHA-256 and byte length), complete
violations, previews, exact document/rule ranges, diagnostic order, summary and
all other report fields must reproduce. Equality distinguishes booleans from
integers. Unknown extra fields also fail. JSON object key order and report
whitespace can differ unless its bytes are pinned. Source whitespace and CRLF
changes always invalidate its identity, even if parsed values are unchanged.
Each explicitly named file is captured once, including a contract also named
as a document; no input is reread for hashing or source indexing.

Optional `--report-sha256 DIGEST` takes 64 lowercase hex digits independently
retained by the caller. A mismatched pin stops before any contract/document
read. A pin supplied alongside a replaceable report is not independent approval.
Embedded paths never select files, even if they name a different existing file.

- Exit **0**: complete report reproduced; inspect `all_documents_valid`.
- Exit **1**: report pin, ordered file set, source identity or diagnostic mismatch.
- Exit **2**: unsupported report, invalid contract, malformed/refused/unreadable
  input, invalid pin syntax or budget violation.

Inputs: 1–32 distinct document paths; visible relative workspace regular files,
no symlinks, absolute, hidden or parent components; at most 1,000,000 bytes per
input, 100,000 bytes for the saved report and 4,000,000 bytes across unique
report/contract/document captures. Bounds are checked before accepting a report.
The contract is prepared before document reads. These byte limits do not bound
regex execution, uniqueness comparisons, indexing or intermediate diagnostics;
this is not a general CPU or memory sandbox. Trusted contracts and sibling
Python sources are required. A captured read is not an atomic multi-file snapshot.

## Checks and dependencies

```sh
python3 -B line-2/tools/batch-guard/test_review.py
```

All **21 tests passed**, including mixed acceptance, real records, missing-field
anchors, byte changes, altered ranges/types/previews/order, deleted diagnostics,
wrong summaries, pin short-circuit, path injection, duplicate paths/keys, invalid
contracts before document access, malformed documents, budgets, shared captures
and CLI replay. Test fixtures stay in memory; no local setup is needed.
`validation.json` retains the actual commands and local results.

Keep this folder beside `batch-source/`, `source-locator/`, `rule-locator/`,
`bounded-contract/` and `json-contract/`. The no-follow bootstrap and typed tree
equality are copied unchanged from `source-guard/review.py`; validation and source
indexing reuse unchanged siblings. No sibling tool is replaced. The tool reads
only explicit inputs and fixed sibling code and writes only stdout. It uses no
network, environment, secret, wallet, signing, payment or transaction.

The contract language is the inherited supported subset, not full JSON Schema.
Matching bytes and diagnostics establish neither content truth, authenticity,
source approval nor payment settlement. No coin is required by this utility.

## Mark

**Paired Witnesses**, record 31: Pepe compares every remembered pebble with its
source before trusting the group. Generated charcoal and ochre pigment was added
to vacant lower-right stone. All ancestral paintings and every pixel outside the
small addition remain unchanged. The mark is intentionally worn and subtle in
shadow. See `../../WALL-31.md` and `../../wall-review-31.json` for dimensions,
formats, preservation checks, prompt and visual review.
