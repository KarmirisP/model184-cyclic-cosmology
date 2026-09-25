# MODEL184 — source-explicit Wilsonian cyclic cosmology

Reproducibility repository for the CQG manuscript.

## Status

**Manuscript draft. Final production MCMC chains are still running.** Posterior-dependent tables and figures are regenerated only after the declared DAWN convergence/freeze criterion is met.

Two pre-submission numerical closure gates remain explicit:

1. `S8_RECONCILIATION`: DAWN and ASUS must propagate the **same hashed chain-row manifest** through identical hashed CLASS source. No publication S8 mean is accepted until sample-by-sample parity is demonstrated.
2. `STRICT_RMATCH`: the W-channel must be classified from raw full-theory vs matched-EFT projectors, and the post-match error must satisfy the predeclared `1e-4` threshold without relaxing it.

## Layout

- `main.tex`, `references.bib` — CQG manuscript source.
- `scripts/reconcile_s8.py` — deterministic cross-machine posterior-predictive reconciliation.
- `scripts/strict_rmatch_ledger.py` — strict matching-error adjudicator.
- `scripts/make_publication_figures.py` — figures generated only from released machine-readable inputs.
- `data/` — small figure inputs exported from frozen authorities.
- `figures/` — generated PDFs used by `main.tex` when present.
- `reproducibility/` — hashes and release manifests.

## Figure generation

```bash
python3 -m pip install -r requirements.txt
python3 scripts/make_publication_figures.py
```

Missing numerical inputs cause the associated figure to be skipped rather than fabricated.

## Release policy

Large raw authorities and chain archives should be attached to a versioned GitHub release and/or DOI-backed archive. Their SHA-256 hashes belong in this repository. The final paper release should be tagged only after the production MCMC freeze, the S8 reconciliation PASS, and the strict matching-ledger PASS.
