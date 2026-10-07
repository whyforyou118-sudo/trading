"""Planning power simulation for the frozen quarterly study design.

This is NOT the final strategy inference. It quantifies the statistical limitation of
about 31 quarterly observations and seven pre-registered configurations. Phase 1 must
repeat dependence-aware inference on realized returns.
"""
from __future__ import annotations
import argparse, math, random
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def sample_normal(rng, mean, sd):
    # Box-Muller without third-party dependencies.
    u1=max(rng.random(),1e-12); u2=max(rng.random(),1e-12)
    return mean + sd*math.sqrt(-2*math.log(u1))*math.cos(2*math.pi*u2)

def sharpe(xs):
    m=sum(xs)/len(xs)
    v=sum((x-m)**2 for x in xs)/(len(xs)-1)
    return m/math.sqrt(v) if v>0 else 0.0

def run(n=31, annual_vol=0.20, alpha=0.05, trials=7, reps=10000, seed=20261007):
    rng=random.Random(seed)
    # Annual Sharpe -> quarterly mean using annualized volatility / 2.
    quarterly_sd=annual_vol/2.0
    annual_sharpes=[0.0,0.25,0.50,0.75,1.0]
    print("PHASE 0.5 PLANNING POWER SIMULATION")
    print(f"observations={n} annual_vol={annual_vol:.2%} trials={trials} reps={reps} seed={seed}")
    print("This simulation is a planning diagnostic; it is not the Phase 1 realized-return inference.")
    for target_s in annual_sharpes:
        detections=0
        false_positive=0
        threshold=0.0
        maxima=[]
        for _ in range(reps):
            vals=[]
            for _trial in range(trials):
                mu=target_s*annual_vol/4.0
                xs=[sample_normal(rng,mu,quarterly_sd) for _ in range(n)]
                vals.append(sharpe(xs)*math.sqrt(4))
            mx=max(vals)
            maxima.append(mx)
        # Empirical 95% null maximum threshold is used as a multiple-trial diagnostic.
        if target_s==0.0:
            ordered=sorted(maxima)
            threshold=ordered[int(0.95*len(ordered))-1]
        # Re-run detection at the null-derived threshold for each alternative.
        if target_s>0:
            detections=sum(x>=threshold for x in maxima)/len(maxima)
        else:
            detections=sum(x>=threshold for x in maxima)/len(maxima)
        print(f"annual_sharpe={target_s:.2f} | null-95%-max-threshold={threshold:.3f} | detection_rate={detections:.3f}")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--reps",type=int,default=10000)
    ap.add_argument("--seed",type=int,default=20261007)
    args=ap.parse_args()
    run(reps=args.reps,seed=args.seed)
