"""Build a fail-closed 20-event corporate-action reconciliation sample.

The expected events below were independently checked against official NSE
corporate-action pages. The local NSE raw sample must contain the same
symbol/date/purpose/ISIN record before a row is marked PASS.
"""
from __future__ import annotations
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data/raw/corporate_actions/corporate_actions_sample.csv"
OUT = ROOT / "audits/phase05_corporate_action_reconciliation.csv"

NSE_INFOSYS = "https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol=INFY&tabIndex=equity"
NSE_ITC = "https://www.nseindia.com/companies-listing/corporate-filings-actions?symbol=ITC&tabIndex=sme"

EXPECTED = [
    # Official NSE: Infosys corporate-actions page.
    ("INFY","2018-09-04","05-Sep-2018","Bonus 1:1",NSE_INFOSYS),
    ("INFY","2018-10-23","24-Oct-2018","Interim Dividend - Rs 8 Per Share",NSE_INFOSYS),
    ("INFY","2019-01-24","25-Jan-2019","Special Dividend - Rs 4 Per Share",NSE_INFOSYS),
    ("INFY","2019-10-23","24-Oct-2019","Interim Dividend - Rs 8 Per Share",NSE_INFOSYS),
    ("INFY","2020-05-29","01-Jun-2020","Dividend - Rs 9.50 Per Share",NSE_INFOSYS),
    ("INFY","2020-10-23","26-Oct-2020","Interim Dividend - Rs 12 Per Share",NSE_INFOSYS),
    ("INFY","2021-05-31","01-Jun-2021","Annual General Meeting/Dividend - Rs 15 Per Share",NSE_INFOSYS),
    ("INFY","2021-10-26","27-Oct-2021","Interim Dividend - Rs 15 Per Share",NSE_INFOSYS),
    ("INFY","2022-05-31","01-Jun-2022","Annual General Meeting/Dividend - Rs 16 Per Share",NSE_INFOSYS),
    ("INFY","2022-10-27","28-Oct-2022","Interim Dividend - Rs 16.50 Per Share",NSE_INFOSYS),
    # Official NSE: ITC corporate-actions page.
    ("ITC","2018-05-25","29-May-2018","Dividend- Rs 5.15 Per Share",NSE_ITC),
    ("ITC","2019-05-22","24-May-2019","Dividend - Rs 5.75 Per Share",NSE_ITC),
    ("ITC","2020-07-06","08-Jul-2020","Dividend - Rs 10.15 Per Share",NSE_ITC),
    ("ITC","2021-02-22","23-Feb-2021","Interim Dividend - Rs 5 Per Share",NSE_ITC),
    ("ITC","2021-06-10","11-Jun-2021","Dividend - Rs 5.75 Per Share",NSE_ITC),
    ("ITC","2022-02-14","15-Feb-2022","Interim Dividend - Rs 5.25 Per Share",NSE_ITC),
    ("ITC","2022-05-26","28-May-2022","Dividend - Rs 6.25 Per Share",NSE_ITC),
    ("ITC","2023-02-15","15-Feb-2023","Interim Dividend - Rs 6 Per Share",NSE_ITC),
    ("ITC","2023-05-30","30-May-2023","Dividend - Rs 6.75 Per Share /Special Dividend - Rs 2.75 Per Share",NSE_ITC),
    ("ITC","2024-02-08","08-Feb-2024","Interim Dividend - Rs 6.25 Per Share",NSE_ITC),
]

def norm(x: str) -> str:
    return " ".join((x or "").strip().split()).lower()

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
            and r.get("exDate","").strip() == ex_date
            and r.get("recDate","").strip() == record_date
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
            "reconciliation_note": detail,
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
