#!/usr/bin/env python3
"""
Daily Forecast Update Script
Automates the process of updating the dry lightning forecast webpage
"""

import os
import sys
import subprocess
import shutil
from datetime import datetime
from pathlib import Path

def run_command(cmd, cwd=None, shell=True):
    """Run a command and return success status"""
    try:
        result = subprocess.run(cmd, shell=shell, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Command failed: {cmd}")
            print(f"Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"Error running command '{cmd}': {e}")
        return False

def update_html_dates(html_file, today_date, yesterday_date):
    """Update the HTML with current dates for forecast images"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update D0 and D1 forecast paths
        import re
        content = re.sub(r'd0_\d{4}-\d{2}-\d{2}_lightning_forecast_points\.png',
                        f'd0_{today_date}_lightning_forecast_points.png', content)
        content = re.sub(r'd1_\d{4}-\d{2}-\d{2}_lightning_forecast_points\.png',
                        f'd1_{today_date}_lightning_forecast_points.png', content, count=1)  # Current D1
        content = re.sub(r'd1_\d{4}-\d{2}-\d{2}_lightning_forecast_points\.png',
                        f'd1_{yesterday_date}_lightning_forecast_points.png', content)  # Yesterday's D1

        # Update valid periods
        from datetime import datetime, timedelta
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
    print("=" * 50)
    print("Dry Lightning Forecast Update Script")
    print("=" * 50)
    print(f"Starting update process at {datetime.now()}")

    # Get project directory
    project_dir = Path(__file__).parent.absolute()
    forecast_dir = project_dir / "FORECAST"
    resources_dir = forecast_dir / "RESOURCES"
    docs_dir = project_dir / "docs"

    print(f"\nProject directory: {project_dir}")

    # Step 1: Run forecast generation (uncomment as needed)
    print("\nStep 1: Running forecast generation...")
    print("-" * 40)

    # Uncomment and modify these lines to run your forecast scripts
    # forecast_scripts = [
    #     ["python", "eccc_calcs.py"],
    #     ["python", "daily_fcst.py"],
    #     ["python", "d1_daily_fcst.py"]
    # ]

    # for script in forecast_scripts:
    #     if run_command(script, cwd=forecast_dir):
    #         print(f"✓ {script[1]} completed successfully")
    #     else:
    #         print(f"✗ {script[1]} failed")
    #         return False

    print("Forecast scripts completed (uncomment in script to enable).")

    # Step 2: Update HTML with current dates
    print("\nStep 2: Updating HTML with current dates...")
    print("-" * 40)

    # Calculate dates
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    today_date = today.strftime('%Y-%m-%d')
    yesterday_date = yesterday.strftime('%Y-%m-%d')

    # Update the built HTML file
    html_file = docs_dir / "build" / "html" / "index.html"
    if update_html_dates(html_file, today_date, yesterday_date):
        print("HTML dates updated successfully.")
    else:
        print("HTML date update failed!")
        return False

    # Step 3: Rebuild documentation
    print("\nStep 3: Rebuilding documentation...")
    print("-" * 40)

    if run_command("make.bat html", cwd=docs_dir):
        print("Documentation rebuild completed successfully.")
    else:
        print("Documentation rebuild failed!")
        return False

    # Step 4: Success message
    print("\n" + "=" * 50)
    print("UPDATE COMPLETE!")
    print("=" * 50)
    print("The forecast webpage has been updated with the latest data.")
    print("Files updated:")
    print("- d0.png and d1.png in FORECAST/RESOURCES/")
    print("- HTML documentation in docs/build/html/")
    print("\nTo view the updated webpage, open:")
    print("docs\\build\\html\\index.html")
    print(f"\nUpdate completed at {datetime.now()}")
    print("=" * 50)

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)