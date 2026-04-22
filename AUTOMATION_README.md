# Daily Forecast Update Automation

This project includes automated scripts to update the dry lightning forecast webpage daily.

## Available Scripts

### `update_forecast.bat` (Windows Batch)
- **Usage**: Double-click the file or run from command prompt
- **What it does**:
  1. Runs forecast generation scripts (currently commented out)
  2. Converts TIF files to PNG format
  3. Archives yesterday's D1 forecast for historical display
  4. Rebuilds the Sphinx documentation
  5. Reports completion status

### `update_forecast.py` (Python)
- **Usage**: `python update_forecast.py`
- **Same functionality as batch file but more flexible**
- **Better error handling and logging**
- **Archives yesterday's forecast automatically**

## Files Updated Daily

- `FORECAST/RESOURCES/d0.png` - Current day forecast
- `FORECAST/RESOURCES/d1.png` - Next day forecast
- `FORECAST/RESOURCES/d1_yesterday.png` - Previous day's forecast (archived)
- `docs/build/html/index.html` - Updated webpage with current dates

## Setup Instructions

1. **Enable Forecast Scripts** (Optional):
   - Edit `update_forecast.py` or `update_forecast.bat`
   - Uncomment the forecast script execution lines
   - Modify paths if needed

2. **Schedule Daily Updates** (Windows):
   - Open Task Scheduler
   - Create new task
   - Set trigger to "Daily"
   - Set action to run `update_forecast.bat`
   - Set start time (e.g., 6:00 AM)

3. **Schedule Daily Updates** (Python/cron):
   - Use Windows Task Scheduler or cron
   - Run: `python update_forecast.py`

## Files Updated Daily

- `FORECAST/RESOURCES/d0.png` - Current day forecast
- `FORECAST/RESOURCES/d1.png` - Next day forecast
- `docs/build/html/index.html` - Updated webpage

## Manual Testing

To test the update process without scheduling:

```batch
# Windows
update_forecast.bat

# Python
python update_forecast.py
```

## Troubleshooting

- **TIF conversion fails**: Ensure VIZENV conda environment is available
- **Documentation build fails**: Check that sphinx-design is installed
- **Forecast scripts fail**: Verify your forecast generation scripts work independently

## Customization

Edit the scripts to:
- Add email notifications on completion/failure
- Deploy to web server automatically
- Commit changes to git repository
- Send alerts if forecast generation fails