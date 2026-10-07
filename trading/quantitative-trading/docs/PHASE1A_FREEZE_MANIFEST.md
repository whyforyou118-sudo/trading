# Phase 1A Freeze Manifest

Generated after the V6 adversarial review and before any Phase 1 performance run.

- Branch: `phase1a-freeze-controls`
- Freeze commit before this manifest: `b18d8f623c88d4a301473e45fdd078a7d26bf290`
- `config/phase1a_preregistration.json` Git blob SHA: `c097c4de20768f4beb1a5cf8c146e809cdaa6575`
- Random seed: `20261007`
- Permutation repetitions: `100000`
- Bootstrap repetitions: `10000`
- Bootstrap mean block lengths: `2, 3, 4` sensitivity; primary = 3
- Protected discipline holdout: `2023-01-01` through `2025-12-31`
- Primary capital: ₹25,000
- Primary strategy: PIT NIFTY 50 / 12M / 1M skip / Top-5 / quarterly
- Primary slippage: 0.10%
- Primary broker cost model: Zerodha date-effective schedule

The Git commit containing this manifest becomes the final reproducibility anchor for the Phase 1A specification. No performance result may be generated before this commit exists.
