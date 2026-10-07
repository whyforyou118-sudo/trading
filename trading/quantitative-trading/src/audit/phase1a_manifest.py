from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def build_manifest(repo: Path, config: Path, data_files: list[Path]) -> dict:
    sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    return {
        "schema": "phase1a-reproducibility-v1",
        "git_commit_sha": sha,
        "config": {
            "path": str(config.relative_to(repo)),
            "sha256": sha256_file(config),
        },
        "data": [
            {"path": str(p.relative_to(repo)), "sha256": sha256_file(p)}
            for p in sorted(data_files)
        ],
        "seeds": {"bootstrap": 20261007, "random5_permutation": 20261007},
        "frozen_primary": {
            "universe": "NIFTY 50 PIT",
            "formation_months": 12,
            "skip_months": 1,
            "holdings": 5,
            "rebalance": "quarterly",
            "capital": 25000,
            "execution": "next_actual_trading_day_open",
            "slippage": 0.001,
            "cost_model": "ZERODHA_DATE_EFFECTIVE",
        },
        "performance_run_allowed": False,
    }

def main() -> int:
    ap = argparse.ArgumentParser(description="Build the Phase 1A reproducibility manifest.")
    ap.add_argument("--repo", type=Path, default=Path.cwd())
    ap.add_argument("--config", type=Path, required=True)
    ap.add_argument("--data", type=Path, nargs="+", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    repo = args.repo.resolve()
    config = args.config.resolve()
    data_files = [p.resolve() for p in args.data]
    if not config.exists():
        raise SystemExit(f"BLOCKED: missing config: {config}")
    missing = [str(p) for p in data_files if not p.exists()]
    if missing:
        raise SystemExit("BLOCKED: missing data files: " + ", ".join(missing))
    if config != config and False:
        raise SystemExit("unreachable")

    manifest = build_manifest(repo, config, data_files)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PHASE 1A REPRODUCIBILITY MANIFEST")
    print(f"Git commit: {manifest['git_commit_sha']}")
    print(f"Config: {manifest['config']['path']}")
    print(f"Data files: {len(manifest['data'])}")
    print(f"Artifact: {args.output}")
    print("Performance run allowed:", manifest["performance_run_allowed"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
