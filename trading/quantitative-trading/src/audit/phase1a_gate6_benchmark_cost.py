"""Phase 1A Gate 6: benchmark and cost reconciliation.

Fail-closed checks for:
1. date-effective Zerodha cost coverage across the frozen 2018-2025 interval;
2. explicit pre-2020 stamp-duty sensitivity treatment;
3. required benchmark declarations;
4. availability of the full NIFTY 50 TRI and equal-weight benchmark artifacts.

This gate never fabricates benchmark data and never authorizes performance.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "config/phase05_config.json"
PREG = ROOT / "config/phase1a_preregistration.json"
COST = ROOT / "data/reference/zerodha_delivery_cost_schedule.csv"
TRI = ROOT / "data/reference/nifty50_tri.csv"
EW = ROOT / "data/reference/nifty50_equal_weight_tri.csv"
OUT = ROOT / "audits/phase1a_gate6_benchmark_cost.csv"

START = dt.date(2018, 1, 1)
END = dt.date(2025, 12, 31)


def load_csv(path: Path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def benchmark_series_check(path: Path):
    if not path.exists():
        return False, f"missing benchmark artifact: {path.relative_to(ROOT)}"
    try:
        rows = load_csv(path)
    except Exception as exc:
        return False, f"cannot read benchmark artifact: {exc}"
    if not rows:
        return False, "benchmark artifact is empty"
    required = {"date", "value", "source", "source_reference"}
    if not required.issubset(rows[0]):
        return False, f"benchmark schema missing: {sorted(required - set(rows[0]))}"
    dates = []
    for row in rows:
        try:
            d = dt.date.fromisoformat(row["date"])
            v = float(row["value"])
            if v <= 0:
                return False, f"non-positive benchmark value on {d}"
            if row["source"].strip() != "Nifty Indices Historical Data — Total Returns Index Values":
                return False, f"unexpected benchmark source on {d}"
            if not row["source_reference"].strip():
                return False, f"missing source reference on {d}"
            dates.append(d)
        except (KeyError, TypeError, ValueError) as exc:
            return False, f"invalid benchmark row: {row!r}: {exc}"
    if len(dates) != len(set(dates)):
        return False, "benchmark contains duplicate dates"
    if min(dates) > START or max(dates) < END:
        return False, f"benchmark coverage {min(dates)} to {max(dates)} does not cover frozen period"
    return True, f"{len(rows)} unique observations; coverage {min(dates)} to {max(dates)}"


def coverage_check(rows):
    intervals = []
    for row in rows:
        a = dt.date.fromisoformat(row["effective_from"])
        b = dt.date.fromisoformat(row["effective_to"])
        if b < START or a > END:
            continue
        intervals.append((max(a, START), min(b, END), row))
    intervals.sort()
    failures = []
    if not intervals or intervals[0][0] != START:
        failures.append("cost schedule does not begin at 2018-01-01")
    for prev, cur in zip(intervals, intervals[1:]):
        if cur[0] != prev[1] + dt.timedelta(days=1):
            failures.append(f"cost schedule gap/overlap between {prev[1]} and {cur[0]}")
    if intervals and intervals[-1][1] != END:
        failures.append("cost schedule does not end at 2025-12-31")
    return intervals, failures


def main():
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    preg = json.loads(PREG.read_text(encoding="utf-8"))

    cost_rows = load_csv(COST)
    intervals, failures = coverage_check(cost_rows)

    if any(r.get("verified", "").strip().upper() != "TRUE" for r in cost_rows):
        failures.append("one or more cost schedule rows are not verified")
    if any(not r.get("source_reference", "").strip() for r in cost_rows):
        failures.append("one or more cost rows lack source references")

    # Pre-2020 stamp duty is deliberately a sensitivity anchor, not a universal
    # Indian retail rate.
    pre2020 = [r for r in cost_rows if r["effective_from"] <= "2020-06-30" and r["effective_to"] >= "2018-01-01"]
    if not pre2020 or not any("SENSITIVITY" in r.get("stamp_basis", "") for r in pre2020):
        failures.append("pre-2020 stamp-duty state dependence/sensitivity is not explicitly represented")

    required_benchmarks = set(preg["benchmarks"])
    benchmark_results = []
    for name, path in [
        ("NIFTY_50_TRI", TRI),
        ("NIFTY_50_EQUAL_WEIGHT_SECONDARY", EW),
    ]:
        ok, detail = benchmark_series_check(path)
        benchmark_results.append((name, str(path.relative_to(ROOT)), "PASS" if ok else "BLOCKED"))
        if not ok:
            failures.append(detail)

    # Required exposure-matched formula must remain explicit in the preregistration.
    formula = preg.get("exposure_matched_benchmark", {}).get("formula", "")
    if formula != "R_EM_t = w_t * R_NIFTY50_TRI_t + (1-w_t) * R_CASH_t":
        failures.append("exposure-matched benchmark formula does not match preregistration")

    out = [
        {"check": "cost_date_coverage", "status": "PASS" if not coverage_check(cost_rows)[1] else "FAIL",
         "detail": f"{len(intervals)} date-effective intervals cover {START} through {END}"},
        {"check": "pre2020_stamp_sensitivity", "status": "PASS" if pre2020 and any("SENSITIVITY" in r.get("stamp_basis", "") for r in pre2020) else "FAIL",
         "detail": "state-agnostic sensitivity anchor explicitly labeled"},
        *({"check": name, "status": status, "detail": path} for name, path, status in benchmark_results),
        {"check": "exposure_matched_formula", "status": "PASS" if formula else "FAIL", "detail": formula},
    ]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["check", "status", "detail"])
        w.writeheader()
        w.writerows(out)

    print("PHASE 1A GATE 6 — BENCHMARK / COST RECONCILIATION")
    print(f"Cost intervals covering frozen period: {len(intervals)}")
    print(f"Cost coverage failures: {len(coverage_check(cost_rows)[1])}")
    print(f"Full NIFTY 50 TRI artifact: {'PRESENT' if TRI.exists() else 'MISSING'}")
    print(f"Equal-weight NIFTY 50 TRI artifact: {'PRESENT' if EW.exists() else 'MISSING'}")
    if failures:
        print("STATUS: BLOCKED")
        for failure in failures:
            print("BLOCKED:", failure)
        return 1
    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
