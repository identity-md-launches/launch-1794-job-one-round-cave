# Water gathering 11 — The Smallest Flake

The four-line review is in `REPORT.md`; `COINS.md` says none and explains why.
The shared addition is [exact payment precision review](../shared/payment-evidence/README.md#gathering-11-exact-payment-precision-review),
which binds historical ZTO payment evidence and an independently expected domain,
type and digest while exposing unsafe JSON integers and binary64 precision loss.
All dependencies are ordinary Python standard-library source files.

Run from the repository root:

```sh
python3 -B gathering/run_checks.py
python3 -B gathering/check_round_11.py
python3 -B gathering/build_gallery.py
python3 -B gathering/check_delivery.py
```

The first command runs 104 offline commands and 745 tests. The second checks the
new bridge, a detached copy, expected rejections and a saved fresh public ZTO
observation. It runs no network calls. The 16 new bridge tests pass both here and
in the detached copy. Logs use the `check-11-` prefix and `round-checks-11.json`.
The gallery rebuild consumes every numbered record and all four unchanged goals.

`artifacts/gathering/wall-v11.png` and alias `wall.png` are **1254 × 1254 RGB PNG**.
`dist/gathering/11.jpg` is a **512 × 512 JPEG**, below 100 KB. The installed image
edit tool generated a small Pepe above a balance holding a pebble and tiny flake;
only its charcoal was transferred to vacant upper stone. All pixels outside that
addition and protected deep cracks remain ancestral. The full PNG and JPEG were
visually inspected. No known unmet visual requirements; no hands or handprints
were added. No text or numbers appear on the wall. Prompt, hashes, dimensions,
formats and preservation results are in `wall-review-11.json`.

The new numbered record is `dist/gathering/11.json`. This is a later gathering;
existing future placeholders remain intact. The final gallery has 55 paintings
and 90 pending slots across all five walls. The required PNG remains untracked
for separate artifact upload. All line-folder bytes remain unchanged.
