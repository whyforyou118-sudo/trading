"""Audit NIFTY 50 TRI date completeness against the project NSE calendar.

This is a feasibility/completeness audit only. It does not alter the downloaded
TRI data and does not infer missing values.
"""
from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "config/phase05_config.json"
CALENDAR = ROOT / "audits/nse_trading_calendar_v3.csv"
TRI = ROOT / "data/reference/nifty50_tri.csv"
OUT = ROOT / "audits/phase05_tri_completeness.csv"
SUMMARY = ROOT / "audits/phase05_tri_completeness_summary.json"


def read_calendar(start: str, end: str) -> list[str]:
    with CALENDAR.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    return [
        r["date"] for r in rows
        if r["is_trading_day"].strip().lower() == "true"
        and start <= r["date"] <= end
    ]


def read_tri() -> list[dict[str, str]]:
    with TRI.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    start, end = cfg["research_start"], cfg["research_end"]

    if not CALENDAR.exists():
        raise FileNotFoundError(f"Calendar missing: {CALENDAR}")
    if not TRI.exists():
        raise FileNotFoundError(
            f"TRI dataset missing: {TRI}. Run src/data/download_nifty50_tri.py first."
        )

    expected = read_calendar(start, end)
    rows = read_tri()
    dates = [r["date"] for r in rows]
    counts = Counter(dates)
    unique = sorted(set(dates))
    expected_set = set(expected)
    unique_set = set(unique)

    missing = sorted(expected_set - unique_set)
    extras = sorted(unique_set - expected_set)
    known_weekend_extra = sorted(d for d in extras if date.fromisoformat(d).weekday() >= 5)
    other_extra = sorted(set(extras) - set(known_weekend_extra))
    # Some historical index series include Saturday observations even when
    # the exchange was closed. Keep these visible as anomalies; they must not
    # be silently discarded or counted as trading sessions.
    known_weekend_extra = sorted(
        d for d in extras if date.fromisoformat(d).weekday() >= 5
    )
    other_extra = sorted(set(extras) - set(known_weekend_extra))
    duplicates = sorted(d for d, n in counts.items() if n > 1)

    bad_rows = []
    for r in rows:
        try:
            d = date.fromisoformat(r["date"])
            v = float(r["value"])
            if d.isoformat() != r["date"] or v <= 0:
                bad_rows.append(r["date"])
        except (KeyError, ValueError, TypeError):
            bad_rows.append(r.get("date", ""))

    checks = [
        ("EXPECTED_SESSION_COUNT", len(expected), len(expected), "PASS"),
        ("TRI_ROW_COUNT", len(rows), len(rows), "PASS"),
        ("UNIQUE_TRI_DATE_COUNT", len(unique), len(unique), "PASS" if len(unique) == len(rows) else "FAIL"),
        ("MISSING_EXPECTED_TRADING_DATES", len(missing), 0, "PASS" if not missing else "FAIL"),
        ("EXTRA_NONTRADING_DATES", len(extras), 0, "PASS" if not other_extra else "FAIL"),
        ("WEEKEND_EXTRA_DATES", len(known_weekend_extra), 0, "INFO" if known_weekend_extra else "PASS"),
        ("OTHER_EXTRA_DATES", len(other_extra), 0, "PASS" if not other_extra else "FAIL"),
        ("DUPLICATE_TRI_DATES", len(duplicates), 0, "PASS" if not duplicates else "FAIL"),
        ("INVALID_TRI_ROWS", len(bad_rows), 0, "PASS" if not bad_rows else "FAIL"),
    ]

    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["check", "observed", "expected", "status", "detail"],
        )
        w.writeheader()
        for check, observed, expected_value, status in checks:
            detail = ""
            if check == "MISSING_EXPECTED_TRADING_DATES":
                detail = ";".join(missing)
            elif check == "EXTRA_NONTRADING_DATES":
                detail = ";".join(extras)
            elif check == "WEEKEND_EXTRA_DATES":
                detail = ";".join(known_weekend_extra)
            elif check == "OTHER_EXTRA_DATES":
                detail = ";".join(other_extra)
            elif check == "WEEKEND_EXTRA_DATES":
                detail = ";".join(known_weekend_extra)
            elif check == "OTHER_EXTRA_DATES":
                detail = ";".join(other_extra)
            elif check == "DUPLICATE_TRI_DATES":
                detail = ";".join(duplicates)
            elif check == "INVALID_TRI_ROWS":
                detail = ";".join(bad_rows)
            w.writerow({
                "check": check,
                "observed": observed,
                "expected": expected_value,
                "status": status,
                "detail": detail,
            })

    overall = "PASS" if not any(x[3] == "FAIL" for x in checks) else "FAIL"
    summary = {
        "status": overall,
        "research_start": start,
        "research_end": end,
        "expected_nse_trading_days": len(expected),
        "tri_rows": len(rows),
        "tri_unique_dates": len(unique),
        "tri_first_date": unique[0] if unique else "",
        "tri_last_date": unique[-1] if unique else "",
        "missing_count": len(missing),
        "extra_count": len(extras),
        "duplicate_count": len(duplicates),
        "invalid_row_count": len(bad_rows),
        "tri_sha256": sha256(TRI),
        "missing_dates": missing,
        "extra_dates": extras,
        "duplicate_dates": duplicates,
        "invalid_rows": bad_rows,
        "known_weekend_extra_dates": known_weekend_extra,
        "other_extra_dates": other_extra,
        "known_weekend_extra_dates": known_weekend_extra,
        "other_extra_dates": other_extra,
    }
    SUMMARY.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print("PHASE 0.5 TRI COMPLETENESS")
    for check, observed, expected_value, status in checks:
        print(f"{check}: {status} (observed={observed}, expected={expected_value})")
    if missing:
        print("Missing dates:", ", ".join(missing))
    if extras:
        print("Extra dates:", ", ".join(extras))
    if duplicates:
        print("Duplicate dates:", ", ".join(duplicates))
    if known_weekend_extra:
        print("Weekend index observations (not exchange sessions):", ", ".join(known_weekend_extra))
    if other_extra:
        print("Other extra dates:", ", ".join(other_extra))
    print(f"TRI SHA256: {summary['tri_sha256']}")
    print(f"Overall: {overall}")
    print(f"Artifact: {OUT}")
    print(f"Summary: {SUMMARY}")
    return 0 if overall == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
