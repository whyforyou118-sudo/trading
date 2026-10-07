"""Build a fail-closed PIT external-reconciliation worksheet.

The local PIT ledger is authoritative for the project's reconstruction, but
external official NSE evidence must be recorded separately. This script never
converts a plausible event into PASS automatically.
"""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "audits/phase05_pit_external_reconciliation.csv"

CANDIDATES = [
    ROOT / "data/reference/nifty50_membership.csv",
    ROOT / "data/reference/nifty50_constituent_transitions.csv",
    ROOT / "data/reference/nifty50_membership_transitions.csv",
]

# Known official NSE evidence anchors. These are references to official
# publications, not assertions that the local ledger matches them.
OFFICIAL_EVIDENCE = [
    ("2020-03-27", "YESBANK", "EXCLUSION",
     "https://nsearchives.nseindia.com/web/sites/default/files/2020-02/ind_prs18022020.pdf"),
    ("2021-03-31", "", "NIFTY50_REVIEW",
     "https://nsearchives.nseindia.com/web/sites/default/files/2021-02/ind_prs23022021.pdf"),
    ("2022-09-30", "ADANIENT", "INCLUSION",
     "https://nsearchives.nseindia.com/web/sites/default/files/2022-09/ind_prs01092022.pdf"),
    ("2023-07-13", "HDFC", "HDFC_EXCLUSION_AMALGAMATION",
     "https://nsearchives.nseindia.com/web/sites/default/files/2023-07/ind_prs04072023.pdf"),
    ("2024-03-28", "SHRIRAMFIN", "INCLUSION",
     "https://www.nseindia.com/mediacoverage/nse-replacements-in-indices-wef-march-28-2024"),
]

def read(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def locate():
    for p in CANDIDATES:
        if p.exists():
            return p
    names = ", ".join(str(p.relative_to(ROOT)) for p in CANDIDATES)
    raise SystemExit(f"BLOCKED: PIT membership ledger not found. Expected one of: {names}")

def normalize(row):
    return {
        "effective_date": row.get("effective_date","").strip(),
        "symbol": row.get("symbol","").strip(),
        "action": row.get("action","").strip().upper(),
        "company_name": row.get("company_name","").strip(),
        "isin": row.get("isin","").strip(),
    }

def main():
    source = locate()
    local = [normalize(r) for r in read(source)]
    local = [r for r in local if r["effective_date"]]

    rows = []
    for d, symbol, event_type, url in OFFICIAL_EVIDENCE:
        matches = [
            r for r in local
            if r["effective_date"] == d
            and (not symbol or r["symbol"] == symbol)
        ]
        # A match is only a candidate for manual reconciliation. It is NOT
        # marked PASS because the official document must be checked for the
        # exact effective date/action and the local state transition.
        status = "PENDING"
        evidence = (
            f"Local ledger candidates={len(matches)}; manually reconcile "
            f"effective date, symbol/action and resulting PIT state against "
            f"the cited official NSE publication."
        )
        local_matches = "|".join(
            f'{m["symbol"]}:{m["action"]}:{m["isin"]}' for m in matches
        )
        rows.append({
            "effective_date": d,
            "check": f"PIT_EXTERNAL_{d}_{symbol or 'REVIEW'}",
            "status": status,
            "official_event_type": event_type,
            "security": symbol,
            "local_match_count": len(matches),
            "local_matches": local_matches,
            "official_source_reference": url,
            "evidence": evidence,
        })

    with OUT.open("w", encoding="utf-8", newline="") as f:
        fields = [
            "effective_date","check","status","official_event_type","security",
            "local_match_count","local_matches","official_source_reference","evidence"
        ]
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    print("PHASE 0.5 PIT EXTERNAL RECONCILIATION")
    print(f"Local PIT ledger: {source}")
    print(f"Wrote {len(rows)} PENDING official-evidence rows: {OUT}")
    for row in rows:
        print(
            f'{row["effective_date"]} | official={row["official_event_type"]} '
            f'| security={row["security"] or "REVIEW"} '
            f'| local_match_count={row["local_match_count"]} '
            f'| local_matches={row["local_matches"] or "NONE"}'
        )
    print("No row is marked PASS automatically.")
    print("Manual/independent reconciliation is required before the fail-closed gate can pass.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
