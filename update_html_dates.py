#!/usr/bin/env python3
"""
HTML Date Update Script
Updates the HTML with current dates for forecast images
"""

import os
import sys
import re
from datetime import datetime, timedelta

def update_html_dates(html_file, today_date, yesterday_date):
    """Update the HTML with current dates for forecast images"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update D0 and D1 forecast paths
        content = re.sub(r'd0_\d{4}-\d{2}-\d{2}_lightning_forecast_points\.png',
                        f'd0_{today_date}_lightning_forecast_points.png', content)
        content = re.sub(r'd1_\d{4}-\d{2}-\d{2}_lightning_forecast_points\.png',
                        f'd1_{today_date}_lightning_forecast_points.png', content, count=1)  # Current D1
        content = re.sub(r'd1_\d{4}-\d{2}-\d{2}_lightning_forecast_points\.png',
                        f'd1_{yesterday_date}_lightning_forecast_points.png', content)  # Yesterday's D1

        # Update valid periods
        today_obj = datetime.strptime(today_date, '%Y-%m-%d')
        tomorrow_obj = today_obj + timedelta(days=1)
        day_after_obj = tomorrow_obj + timedelta(days=1)

        content = re.sub(r'D0: \w+ \d+, \d{4} 00 UTC to \w+ \d+, \d{4} 00 UTC',
                        f'D0: {today_obj.strftime("%B %d, %Y")} 00 UTC to {tomorrow_obj.strftime("%B %d, %Y")} 00 UTC', content)
        content = re.sub(r'D1: \w+ \d+, \d{4} 00 UTC to \w+ \d+, \d{4} 00 UTC',
                        f'D1: {tomorrow_obj.strftime("%B %d, %Y")} 00 UTC to {day_after_obj.strftime("%B %d, %Y")} 00 UTC', content)

        # Update yesterday's date in header
        yesterday_obj = datetime.strptime(yesterday_date, '%Y-%m-%d')
        content = re.sub(r'Yesterday\'s D1 Forecast \(\w+ \d+, \d{4}\)',
                        f'Yesterday\'s D1 Forecast ({yesterday_obj.strftime("%B %d, %Y")})', content)
        content = re.sub(r'This was yesterday\'s forecast for today \(\w+ \d+, \d{4}\)\.',
                        f'This was yesterday\'s forecast for today ({today_obj.strftime("%B %d, %Y")}).', content)

        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)

        print(f"Updated HTML dates in {html_file}")
        return True
    except Exception as e:
        print(f"Error updating HTML dates: {e}")
        return False

def main():
    if len(sys.argv) != 4:
        print("Usage: python update_html_dates.py <html_file> <today_date> <yesterday_date>")
        sys.exit(1)

    html_file = sys.argv[1]
    today_date = sys.argv[2]
    yesterday_date = sys.argv[3]

    success = update_html_dates(html_file, today_date, yesterday_date)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()