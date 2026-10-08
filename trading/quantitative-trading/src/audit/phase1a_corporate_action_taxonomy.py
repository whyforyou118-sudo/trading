from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "data"
    / "raw"
    / "corporate_actions"
    / "nse_corporate_actions_2018_2025.csv"
)
OUTPUT = ROOT / "audits" / "phase1a_corporate_action_taxonomy.csv"

PATTERNS = {
    "DIVIDEND": r"\bdividend\b|\binterest payment\b",
    "BONUS": r"\bbonus\b",
    "SPLIT": r"split|sub[\s-]?division|subdivision|consolidation",
    "RIGHTS": r"\bright\b|\bright issue\b",
    "BUYBACK": r"buy.?back|buy back",
    "MERGER": r"merg|amalgamat",
    "DEMERGER": r"demerg",
    "CAPITAL_REDUCTION": r"reduction of capital|capital reduction",
    "DELISTING": r"delisting",
    "WARRANT": r"\bwarrant\b",
    "IPO": r"initial public|(^|[^a-z])ipo([^a-z]|$)",
}


def classify(subject: str) -> str:
    subject = subject.strip()

    # Explicit precedence: more specific structural events first.
    precedence = [
        "DEMERGER",
        "MERGER",
        "CAPITAL_REDUCTION",
        "RIGHTS",
        "BUYBACK",
        "BONUS",
        "SPLIT",
        "DIVIDEND",
        "WARRANT",
        "DELISTING",
        "IPO",
    ]

    for event_class in precedence:
        if re.search(PATTERNS[event_class], subject, re.IGNORECASE):
            return event_class

    return "OTHER"


def main() -> int:
    if not SOURCE.exists():
        raise SystemExit(f"BLOCKED: source missing: {SOURCE}")

    with SOURCE.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    if not rows:
        raise SystemExit("BLOCKED: source contains zero records")

    classifications = []

    for row in rows:
        subject = row.get("subject", "").strip()
        event_class = classify(subject)

        classifications.append(
            {
                "event_class": event_class,
                "subject": subject,
                "symbol": row.get("symbol", ""),
                "isin": row.get("isin", ""),
                "exDate": row.get("exDate", ""),
                "recDate": row.get("recDate", ""),
                "caBroadcastDate": row.get("caBroadcastDate", ""),
            }
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "event_class",
                "subject",
                "symbol",
                "isin",
                "exDate",
                "recDate",
                "caBroadcastDate",
            ],
        )
        writer.writeheader()
        writer.writerows(classifications)

    counts = Counter(x["event_class"] for x in classifications)

    print("PHASE 1A — CORPORATE-ACTION TAXONOMY")
    print(f"Source rows: {len(rows)}")
    print(f"Unique symbols: {len(set(x.get('symbol', '') for x in rows))}")
    print()
    print("EVENT CLASS COUNTS")
    for event_class, count in counts.most_common():
        print(f"{event_class}: {count}")

    print()
    print("UNIQUE SUBJECT COUNTS BY CLASS")

    for event_class in counts:
        subjects = {
            x["subject"]
            for x in classifications
            if x["event_class"] == event_class
        }
        print(f"{event_class}: {len(subjects)}")

    other_subjects = Counter(
        x["subject"]
        for x in classifications
        if x["event_class"] == "OTHER"
    )

    print()
    print(f"OTHER UNIQUE SUBJECTS: {len(other_subjects)}")

    if other_subjects:
        print()
        print("TOP 50 OTHER SUBJECTS")
        for subject, count in other_subjects.most_common(50):
            print(f"{count:5d}  {subject}")

    print()
    print(f"Artifact: {OUTPUT}")
    print("STATUS: PASS — taxonomy generated for review.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
