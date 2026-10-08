from pathlib import Path
import zipfile
import pandas as pd

ROOT = Path("data/raw/prices")

required_old = {"SYMBOL", "SERIES", "OPEN", "TIMESTAMP", "ISIN"}
required_new = {"TckrSymb", "SctySrs", "OpnPric", "TradDt", "ISIN"}

files = sorted(ROOT.rglob("*.zip"))

old = []
new = []
bad = []

for path in files:
    try:
        with zipfile.ZipFile(path) as z:
            names = z.namelist()
            if not names:
                bad.append((str(path), "empty_zip"))
                continue

            name = names[0]
            header = set(pd.read_csv(z.open(name), nrows=0).columns)

            if required_old.issubset(header):
                df = pd.read_csv(z.open(name), usecols=["TIMESTAMP"])
                date = pd.to_datetime(df["TIMESTAMP"], dayfirst=True).iloc[0]
                old.append(date.date())

            elif required_new.issubset(header):
                df = pd.read_csv(z.open(name), usecols=["TradDt"])
                date = pd.to_datetime(df["TradDt"]).iloc[0]
                new.append(date.date())

            else:
                bad.append((str(path), "unknown_schema"))

    except Exception as e:
        bad.append((str(path), str(e)))

print("PRICE DATA INTEGRITY")
print("====================")
print(f"Total ZIP files : {len(files)}")
print(f"Legacy files    : {len(old)}")
print(f"New-format files: {len(new)}")
print(f"Bad files       : {len(bad)}")

if old:
    print(f"Legacy dates    : {min(old)} -> {max(old)}")

if new:
    print(f"New dates       : {min(new)} -> {max(new)}")

all_dates = old + new

if all_dates:
    print(f"Overall dates   : {min(all_dates)} -> {max(all_dates)}")
    print(f"Unique dates    : {len(set(all_dates))}")

if bad:
    print("\nBAD FILES:")
    for item in bad[:20]:
        print(item)

status = (
    len(files) == 2226
    and len(old) == 1732
    and len(new) == 494
    and len(bad) == 0
)

print("\nSTATUS:", "PASS" if status else "FAIL")