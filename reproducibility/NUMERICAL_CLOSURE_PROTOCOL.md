# Pre-submission numerical closure protocol

## Gate A — S8 reconciliation

Run only after DAWN freezes the final production chains.

1. DAWN generates `FINAL_S8_SAMPLE_MANIFEST.csv` from the final four raw chains using `scripts/reconcile_s8.py --generate-manifest`.
2. Freeze/hash the four chain files, manifest, CLASS executable, `background.c`, `perturbations.c`, and `thermodynamics.c`.
3. DAWN computes all manifest samples and writes `DAWN_FINAL_S8_RECONCILIATION.json`.
4. Copy the exact chains + manifest + hashed CLASS authority to ASUS.
5. ASUS runs the same script **without** `--generate-manifest` and writes `ASUS_FINAL_S8_RECONCILIATION.json`.
6. Join by `sample_id` and require identical chain hashes and manifest hash. Publication gate: max sample-by-sample |Delta S8| < 1e-5 and |Delta mean| < 2e-5. If not, FAIL and diagnose before publication.
7. The final paper quotes only the reconciled value from this common manifest, with the full weighted-chain posterior summary reported separately.

Do not compare two independently thinned/resampled subsets and call their means a replay.

## Gate B — strict Wilsonian matching ledger

The authority generator must export `STRICT_RMATCH_RAW.csv` with columns:

`channel,classification,full_value,eft_matched_value,normalization,raw_shift`

Allowed classifications are exactly:

- `WILSON_COEFFICIENT_SHIFT`
- `REPRESENTED_POST_MATCH_RESIDUAL`
- `UNREPRESENTED_TRUNCATION_REMAINDER`

For the W channel, classification must follow from the actual matched projection: if the retained EFT coefficient absorbs the W displacement, show the post-match full-minus-EFT residual explicitly. Do not classify W from its magnitude or from the desired verdict.

Run:

```bash
python3 scripts/strict_rmatch_ledger.py STRICT_RMATCH_RAW.csv \
  --threshold 1e-4 \
  --out STRICT_RMATCH_VERDICT.json
```

Submission gate:

`CANONICAL_WILSONIAN_HANDOFF_PASS_STRICT=true`

No threshold relaxation is permitted.
