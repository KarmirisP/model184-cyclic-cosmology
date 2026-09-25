# Machine-readable figure inputs

Do not hand-edit publication numbers here. Each file should be exported from a frozen authority package and listed in `reproducibility/SHA256SUMS.txt`.

Final expected inputs:

- `rg_trajectory.npz` — frozen UV-to-threshold trajectory arrays.
- `matching_ledger.csv` — strict raw matching ledger after the W-channel adjudication.
- `bounce_transfer.npz` — scalar/tensor transfer matrices versus k from the frozen perturbation authority.
- `mcmc_convergence.json` — final production-chain R-1 values; generate only after DAWN stops by its declared criterion.
- `heldout_chi2.json` — final best-fit held-out contributions regenerated after the production-chain freeze.

The plotting script skips absent inputs. This is intentional: draft figures must never silently substitute synthetic data.
