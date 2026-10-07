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

def run(n=31, annual_vol=0.20, trials=7, reps=10000, seed=20261007):
    rng=random.Random(seed)
    quarterly_sd=annual_vol/2.0
    annual_sharpes=[0.0,0.25,0.50,0.75,1.0]

    print("PHASE 0.5 PLANNING POWER SIMULATION")
    print(f"observations={n} annual_vol={annual_vol:.2%} trials={trials} reps={reps} seed={seed}")
    print("This simulation is a planning diagnostic; it is not the Phase 1 realized-return inference.")

    # First establish the family-wise 95% threshold under the null.
    null_maxima=[]
    for _ in range(reps):
        trial_sharpes=[]
        for _trial in range(trials):
            xs=[sample_normal(rng,0.0,quarterly_sd) for _ in range(n)]
            trial_sharpes.append(sharpe(xs)*math.sqrt(4))
        null_maxima.append(max(trial_sharpes))

    null_maxima.sort()
    threshold=null_maxima[int(0.95*len(null_maxima))-1]

    print(f"FAMILYWISE_NULL_95_THRESHOLD={threshold:.3f}")

    # Apply the SAME precomputed null threshold to every alternative.
    for target_s in annual_sharpes:
        detections=0
        for _ in range(reps):
            trial_sharpes=[]
            for _trial in range(trials):
                mu=target_s*annual_vol/4.0
                xs=[sample_normal(rng,mu,quarterly_sd) for _ in range(n)]
                trial_sharpes.append(sharpe(xs)*math.sqrt(4))
            if max(trial_sharpes) >= threshold:
                detections += 1
        detection_rate=detections/reps
        print(f"annual_sharpe={target_s:.2f} | fixed-null-95-max-threshold={threshold:.3f} | detection_rate={detection_rate:.3f}")

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--reps",type=int,default=10000)
    ap.add_argument("--seed",type=int,default=20261007)
    args=ap.parse_args()
    run(reps=args.reps,seed=args.seed)
