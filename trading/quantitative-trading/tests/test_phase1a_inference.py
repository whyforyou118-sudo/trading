from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from statistics.phase1a_inference import random5_permutation_pvalue, spearman_rank_ic, stationary_bootstrap_mean

def test_bootstrap_deterministic():
    x=[.01,-.005,.02,0,-.01]
    assert stationary_bootstrap_mean(x,reps=100,seed=20261007)==stationary_bootstrap_mean(x,reps=100,seed=20261007)

def test_rank_ic(): assert spearman_rank_ic([1,2,3],[10,20,30])==1.0

def test_permutation_deterministic():
    x=list(range(10)); y=[.01*v for v in x]
    assert random5_permutation_pvalue(x,y,reps=1000,seed=20261007)==random5_permutation_pvalue(x,y,reps=1000,seed=20261007)
