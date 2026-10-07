"""P6 — path-conditional corporate-action census generator."""
from __future__ import annotations

import calendar
import csv
import re
from collections import Counter
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

CA = ROOT / "data/raw/corporate_actions/nse_corporate_actions_2018_2025.csv"
MEM = ROOT / "data/reference/nifty50_membership.csv"
DECISIONS = ROOT / "audits/phase1a_pit_decision_table.csv"
OUT = ROOT / "audits/phase1a_p6_corporate_action_census.csv"

START = date(2018, 1, 1)
END = date(2025, 12, 31)

PATTERNS = {
    "RIGHTS": r"\bright|rights",
    "DEMERGER": r"demerg",
    "MERGER": r"merg|amalgamat",
    "SCHEME": r"scheme",
    "CAPITAL_REDUCTION": r"capital reduction|reduction of capital",
    "REDEMPTION": r"redemption",
    "BUYBACK": r"buy.?back|buy back",
    "BONUS": r"bonus",
    "SPLIT": r"split|sub[\s-]?division|subdivision|consolidation",
    # NSE source text contains a documented typo: "Dividned".
    "DIVIDEND": r"dividend|dividned",
    "INTEREST": r"interest payment",
    "DISTRIBUTION": r"distribution",
}

PRECEDENCE = [
    "DEMERGER",
    "MERGER",
    "SCHEME",
    "CAPITAL_REDUCTION",
    "REDEMPTION",
    "RIGHTS",
    "BUYBACK",
    "BONUS",
    "SPLIT",
    "DIVIDEND",
    "INTEREST",
    "DISTRIBUTION",
]


def parse_date(value: str) -> date | None:
    value = (value or "").strip()
    if not value or value in {"-", "NA", "N/A"}:
        return None

    for fmt in ("%d-%b-%Y", "%Y-%m-%d"):
        try:
            return (
                datetime.strptime(value, fmt).date()
                if fmt != "%Y-%m-%d"
                else date.fromisoformat(value)
            )
        except ValueError:
            pass

    return None


def subtract_months(d: date, months: int) -> date:
    y = d.year
    m = d.month - months

    while m <= 0:
        y -= 1
        m += 12

    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def classify(subject: str) -> str:
    subject = subject.strip()

    for event_class in PRECEDENCE:
        if re.search(PATTERNS[event_class], subject, re.IGNORECASE):
            return event_class

    if re.search(
        r"annual general meeting|extra.?ordinary general meeting|meeting",
        subject,
        re.IGNORECASE,
    ):
        return "ADMINISTRATIVE"

    return "UNRESOLVED"


def membership_state(
    membership: list[dict[str, str]],
    symbol: str,
    target: date,
) -> bool:
    events = []

    for row in membership:
        if row.get("symbol", "").strip().upper() != symbol:
            continue

        d = parse_date(row.get("effective_date", ""))

        if d is not None and d <= target:
            events.append((d, row.get("action", "").strip().upper()))

    events.sort()

    active = False

    for _, action in events:
        if action == "INCLUSION":
            active = True
        elif action == "EXCLUSION":
            active = False

    return active


def main() -> int:
    if not CA.exists():
        raise SystemExit(f"BLOCKED: missing {CA}")

    if not MEM.exists():
        raise SystemExit(f"BLOCKED: missing {MEM}")

    with CA.open("r", encoding="utf-8-sig", newline="") as f:
        corporate_actions = list(csv.DictReader(f))

    with MEM.open("r", encoding="utf-8-sig", newline="") as f:
        membership = list(csv.DictReader(f))

    pit_symbols = {
        row.get("symbol", "").strip().upper()
        for row in membership
        if row.get("symbol", "").strip()
    }

    decision_dates = set()

    if DECISIONS.exists():
        with DECISIONS.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                d = parse_date(row.get("decision_date", ""))
                if d:
                    decision_dates.add(d)

    if not decision_dates:
        raise SystemExit(
            "BLOCKED: phase1a_pit_decision_table.csv is required"
        )

    census = []

    for row in corporate_actions:
        symbol = row.get("symbol", "").strip().upper()

        if symbol not in pit_symbols:
            continue

        ex_date = parse_date(row.get("exDate", ""))

        if ex_date is None:
            continue

        if not START <= ex_date <= END:
            continue

        subject = row.get("subject", "").strip()
        event_class = classify(subject)

        active_on_ex_date = membership_state(
            membership,
            symbol,
            ex_date,
        )

        historical_signal_relevance = False

        for decision_date in decision_dates:
            if not START <= decision_date <= END:
                continue

            lookback_start = subtract_months(decision_date, 12)

            if lookback_start <= ex_date < decision_date:
                if membership_state(
                    membership,
                    symbol,
                    decision_date,
                ):
                    historical_signal_relevance = True
                    break

        if event_class == "DIVIDEND":
            treatment = "CASH_DISTRIBUTION"
        elif event_class == "BONUS":
            treatment = "SHARE_RATIO_ACTION"
        elif event_class == "SPLIT":
            treatment = "SHARE_RATIO_ACTION"
        elif event_class == "BUYBACK":
            treatment = "NO_MECHANICAL_PRICE_ADJUSTMENT"
        elif event_class == "ADMINISTRATIVE":
            treatment = "NO_ECONOMIC_EFFECT"
        elif event_class == "RIGHTS":
            treatment = "REQUIRES_EX_RIGHTS_TREATMENT"
        elif event_class in {"MERGER", "DEMERGER", "SCHEME"}:
            treatment = "REQUIRES_SECURITY_CONVERSION_RECONCILIATION"
        elif event_class == "CAPITAL_REDUCTION":
            treatment = "REQUIRES_EX_DATE_VALUE_TREATMENT"
        elif event_class == "REDEMPTION":
            treatment = "REQUIRES_SECURITY_AND_CASH_TREATMENT"
        elif event_class in {"INTEREST", "DISTRIBUTION"}:
            treatment = "REQUIRES_SECURITY_TYPE_VERIFICATION"
        else:
            treatment = "FAIL_CLOSED_UNRESOLVED"

        census.append(
            {
                "ex_date": ex_date.isoformat(),
                "symbol": symbol,
                "isin": row.get("isin", ""),
                "series": row.get("series", ""),
                "subject": subject,
                "record_date": row.get("recDate", ""),
                "broadcast_date": row.get("caBroadcastDate", ""),
                "event_class": event_class,
                "treatment": treatment,
                "active_on_ex_date": str(active_on_ex_date).lower(),
                "historical_signal_relevance": str(
                    historical_signal_relevance
                ).lower(),
            }
        )

    census.sort(
        key=lambda x: (
            x["ex_date"],
            x["symbol"],
            x["event_class"],
            x["subject"],
        )
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "ex_date",
        "symbol",
        "isin",
        "series",
        "subject",
        "record_date",
        "broadcast_date",
        "event_class",
        "treatment",
        "active_on_ex_date",
        "historical_signal_relevance",
    ]

    with OUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(census)

    unresolved_classes = {
        "UNRESOLVED",
        "RIGHTS",
        "MERGER",
        "DEMERGER",
        "SCHEME",
        "CAPITAL_REDUCTION",
        "REDEMPTION",
        "INTEREST",
        "DISTRIBUTION",
    }

    unresolved = [
        row
        for row in census
        if row["event_class"] in unresolved_classes
        and (
            row["active_on_ex_date"] == "true"
            or row["historical_signal_relevance"] == "true"
        )
    ]

    structural = [
        row
        for row in census
        if row["event_class"]
        not in {"ADMINISTRATIVE", "DIVIDEND"}
    ]

    print("PHASE 1A P6 — CORPORATE-ACTION CENSUS")
    print(f"Raw NSE records: {len(corporate_actions)}")
    print(f"PIT symbols ever observed: {len(pit_symbols)}")
    print(f"Relevant PIT-symbol actions: {len(census)}")
    print(f"Structural/non-ordinary records: {len(structural)}")
    print(f"Relevant unresolved/special records: {len(unresolved)}")
    print()

    print("EVENT CLASS COUNTS")

    for event_class, count in Counter(
        row["event_class"] for row in census
    ).most_common():
        print(f"{event_class}: {count}")

    print()
    print("RELEVANT SPECIAL-TREATMENT RECORDS")

    for row in unresolved:
        print(
            row["ex_date"],
            row["symbol"],
            row["event_class"],
            row["active_on_ex_date"],
            row["historical_signal_relevance"],
            row["subject"],
        )

    print()
    print(f"Artifact: {OUT}")

    if unresolved:
        print(
            "STATUS: BLOCKED — economically material actions "
            "still require explicit treatment."
        )
        return 2

    print("STATUS: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
