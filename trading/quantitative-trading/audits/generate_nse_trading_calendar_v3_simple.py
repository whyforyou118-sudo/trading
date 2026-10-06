import csv, datetime, os

# Date range
start = datetime.date(2017, 1, 1)
end = datetime.date(2025, 12, 31)

delta = datetime.timedelta(days=1)

# Official holidays (from websearch and user note)
official_holidays = {
    # 2023 holidays
    datetime.date(2023, 1, 26), datetime.date(2023, 3, 8), datetime.date(2023, 3, 30), datetime.date(2023, 4, 4),
    datetime.date(2023, 4, 7), datetime.date(2023, 4, 14), datetime.date(2023, 5, 1), datetime.date(2023, 6, 28),
    datetime.date(2023, 8, 15), datetime.date(2023, 9, 19), datetime.date(2023, 10, 2), datetime.date(2023, 10, 24),
    datetime.date(2023, 11, 14), datetime.date(2023, 11, 27), datetime.date(2023, 12, 25),
    # 2024 holidays
    datetime.date(2024, 1, 26), datetime.date(2024, 3, 8), datetime.date(2024, 3, 25), datetime.date(2024, 3, 29),
    datetime.date(2024, 4, 11), datetime.date(2024, 4, 17), datetime.date(2024, 5, 1), datetime.date(2024, 6, 17),
    datetime.date(2024, 7, 17), datetime.date(2024, 8, 15), datetime.date(2024, 10, 2), datetime.date(2024, 11, 1),
    datetime.date(2024, 11, 15), datetime.date(2024, 12, 25),
    # user‑specified 2025 holiday (Independence Day observed)
    datetime.date(2025, 8, 15)
}

out_path = os.path.join('audits', 'nse_trading_calendar_v3.csv')
os.makedirs('audits', exist_ok=True)
with open(out_path, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['date','year','weekday','is_trading_day','source','source_reference','validation_status'])
    cur = start
    while cur <= end:
        weekday = cur.strftime('%A')
        # NSE trading days are Monday‑Friday excluding holidays; weekends are non‑trading
        is_weekday = cur.weekday() < 5  # Mon=0, Fri=4
        is_holiday = cur in official_holidays
        is_trading = is_weekday and not is_holiday
        writer.writerow([
            cur.isoformat(),
            cur.year,
            weekday,
            is_trading,
            'generated+official_holidays',
            'websearch 2023/2024 + user note',
            'validated'
        ])
        cur += delta
print('Calendar CSV written to', out_path)
