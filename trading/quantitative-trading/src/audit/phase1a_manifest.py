from __future__ import annotations
import hashlib, json, subprocess
from pathlib import Path

def sha256_file(path: Path) -> str:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def build_manifest(repo: Path, config: Path, data_files: list[Path]) -> dict:
    sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=repo,text=True).strip()
    return {"schema":"phase1a-reproducibility-v1","git_commit_sha":sha,"config":{"path":str(config.relative_to(repo)),"sha256":sha256_file(config)},"data":[{"path":str(p.relative_to(repo)),"sha256":sha256_file(p)} for p in sorted(data_files)],"seeds":{"bootstrap":20261007,"random5_permutation":20261007},"performance_run_allowed":False}
