import pandas as pd, pandas_market_calendars as mcal, csv

# Define date range
start = '2017-01-01'
end = '2025-12-31'

# Obtain NSE schedule using pandas_market_calendars (as base)
cal = mcal.get_calendar('NSE')
schedule = cal.schedule(start_date=start, end_date=end)
schedule = schedule.tz_localize(None)

# Official holiday dates gathered from NSE circulars (2023, 2024) and user note for 2025-08-15
official_holidays = {
    # 2023 holidays
    '2023-01-26','2023-03-08','2023-03-30','2023-04-04','2023-04-07','2023-04-14','2023-05-01','2023-06-28','2023-08-15','2023-09-19','2023-10-02','2023-10-24','2023-11-14','2023-11-27','2023-12-25',
    # 2024 holidays
    '2024-01-26','2024-03-08','2024-03-25','2024-03-29','2024-04-11','2024-04-17','2024-05-01','2024-06-17','2024-07-17','2024-08-15','2024-10-02','2024-11-01','2024-11-15','2024-12-25',
    # User-specified 2025 holiday
    '2025-08-15'
}

# Output CSV path
out_path = r"C:/Users/damar/Downloads/trading/quantitative-trading/audits/nse_trading_calendar_v3.csv"
with open(out_path, 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['date','year','weekday','is_trading_day','source','source_reference','validation_status'])
    for idx, row in schedule.iterrows():
        d = idx.date()
        date_str = d.isoformat()
        is_trade = date_str not in official_holidays
        writer.writerow([
            date_str,
            d.year,
            d.strftime('%A'),
            is_trade,
            'pandas_market_calendars+official_holidays',
            '2023/2024 circulars + user note',
            'adjusted'
        ])
print('Calendar generated with', len(schedule), 'rows')
