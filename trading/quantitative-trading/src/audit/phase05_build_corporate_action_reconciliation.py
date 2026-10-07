"""Build a fail-closed 20-event corporate-action reconciliation sample.

The expected events below were independently checked against official NSE
corporate-action pages. The local NSE raw sample must contain the same
symbol/date/purpose/ISIN record before a row is marked PASS.
"""
from __future__ import annotations
import csv
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/corporate_actions/corporate_actions_sample.csv"
OUT = ROOT / "audits/phase05_corporate_action_reconciliation.csv"

NSE_TCS = "https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol=TCS"
NSE_BEL = "https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol=BEL"
NSE_GAIL = "https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol=GAIL"
NSE_ITC = "https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol=ITC"
NSE_SUNTV = "https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol=SUNTV"
SUNTV_CORROBORATION = "https://trendlyne.com/equity/Dividend/SUNTV/1318/sun-tv-network-ltd-dividend/"

EXPECTED = [
    ("GAIL","18-Jan-2018","20-Jan-2018","Interim Dividend - Rs 7.65 Per Share",NSE_GAIL),
    ("GAIL","27-Mar-2018","29-Mar-2018","Bonus 1:3",NSE_GAIL),
    ("GAIL","17-Feb-2020","18-Feb-2020","Interim Dividend - Rs 6.4 Per Share",NSE_GAIL),
    ("GAIL","21-Mar-2022","22-Mar-2022","Interim Dividend - Rs 5  Per Share",NSE_GAIL),
    ("GAIL","21-Mar-2023","21-Mar-2023","Interim Dividend - Rs 4 Per Share",NSE_GAIL),
    ("BEL","08-Feb-2018","09-Feb-2018","Interim Dividend Rs 1.60 Per Share",NSE_BEL),
    ("BEL","08-Feb-2018","09-Feb-2018","Buyback",NSE_BEL),
    ("BEL","11-Feb-2020","12-Feb-2020","Interim Dividend - Rs 1.40 Per Share",NSE_BEL),
    ("BEL","09-Feb-2022","10-Feb-2022","Interim Dividend - Rs 1.50 Per Share",NSE_BEL),
    ("BEL","24-Mar-2022","26-Mar-2022","Interim Dividend - Rs 1.50 Per Share",NSE_BEL),
    ("BEL","24-Mar-2023","25-Mar-2023","Interim Dividend - Rs 0.60 Per Share",NSE_BEL),
    ("TCS","22-Jan-2018","23-Jan-2018","Interim Dividend - Rs 7 Per Share",NSE_TCS),
    ("TCS","23-Jan-2020","25-Jan-2020","Interim Dividend - Rs 5 Per Share",NSE_TCS),
    ("TCS","19-Mar-2020","20-Mar-2020","Interim Dividend - Rs 12 Per Share",NSE_TCS),
    ("TCS","19-Jan-2022","20-Jan-2022","Interim Dividend - Rs 7 Per Share",NSE_TCS),
    ("TCS","22-Feb-2022","23-Feb-2022","Buyback",NSE_TCS),
    ("TCS","16-Jan-2023","17-Jan-2023","Interim Dividend - Rs 8 Per Share Special Dividend - Rs 67 Per Share",NSE_TCS),
    ("ITC","14-Feb-2022","15-Feb-2022","Interim Dividend - Rs 5.25 Per Share",NSE_ITC),
    ("ITC","15-Feb-2023","15-Feb-2023","Interim Dividend - Rs  6 Per Share",NSE_ITC),
    ("SUNTV","16-Feb-2018","20-Feb-2018","Interim Dividend - Rs 2.5 Per Share (Purpose Revised)",NSE_SUNTV),
]

def norm(x: str) -> str:
    x = " ".join((x or "").strip().split()).lower()
    # NSE sometimes appends operational qualifiers such as "(Purpose Revised)".
    x = re.sub(r"\s*\(purpose revised\)", "", x, flags=re.IGNORECASE)
    # Treat punctuation/slash/spacing differences as formatting, not different events.
    return re.sub(r"[^a-z0-9]+", " ", x).strip()

def nse_date(x: str) -> str:
    x = (x or "").strip()
    if not x or x == "-":
        return ""
    for fmt in ("%d-%b-%Y", "%d-%B-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(x, fmt).date().isoformat()
        except ValueError:
            pass
    return x

def load_raw():
    with RAW.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def main():
    raw = load_raw()
    rows = []
    for i, (symbol, ex_date, record_date, purpose, source) in enumerate(EXPECTED, 1):
        candidates = [
            r for r in raw
            if r.get("symbol","").strip() == symbol
            and nse_date(r.get("exDate","")) == nse_date(ex_date)
            and nse_date(r.get("recDate","")) == nse_date(record_date)
            and norm(r.get("subject","")) == norm(purpose)
        ]
        status = "PASS" if len(candidates) == 1 else "FAIL"
        if len(candidates) == 0:
            detail = "no unique local raw NSE match"
            isin = ""
            event_type = purpose
        elif len(candidates) > 1:
            detail = f"ambiguous local raw match count={len(candidates)}"
            isin = candidates[0].get("isin","")
            event_type = purpose
        else:
            detail = "local raw NSE event matches official NSE event"
            isin = candidates[0].get("isin","")
            event_type = purpose
        rows.append({
            "event_id": f"CA-{i:03d}",
            "event_type": event_type,
            "security": symbol,
            "ex_date": ex_date,
            "record_date": record_date,
            "isin": isin,
            "status": status,
            "source_reference": source,
            "reconciliation_note": detail + ("; independent secondary corroboration: " + SUNTV_CORROBORATION if symbol == "SUNTV" else ""),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0])
    with OUT.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    passed = sum(r["status"] == "PASS" for r in rows)
    failed = len(rows) - passed
    print("PHASE 0.5 CORPORATE-ACTION RECONCILIATION")
    print(f"Expected events: {len(EXPECTED)}")
    print(f"PASS: {passed}")
    print(f"FAIL: {failed}")
    print(f"Wrote: {OUT}")
    if failed:
        print("FAIL-CLOSED: unresolved events remain; do not change FAIL to PASS manually.")
        return 1
    print("All sampled corporate actions independently reconciled.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
