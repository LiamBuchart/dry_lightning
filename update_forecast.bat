@echo off
REM Daily Forecast Update Script
REM This script updates the dry lightning forecast webpage

echo ========================================
echo Dry Lightning Forecast Update Script
echo ========================================
echo Starting update process at %DATE% %TIME%

REM Set paths
set PROJECT_DIR=%~dp0
set FORECAST_DIR=%PROJECT_DIR%FORECAST
set RESOURCES_DIR=%FORECAST_DIR%\RESOURCES
set DOCS_DIR=%PROJECT_DIR%docs

echo.
echo Step 1: Running forecast generation...
echo ======================================

REM Run your forecast scripts (uncomment and modify as needed)
REM cd %FORECAST_DIR%
REM eccc_calcs.py
REM python daily_fcst.py
REM python d1_daily_fcst.py

echo Forecast scripts completed.

echo.
echo Step 2: Updating HTML with current dates...
echo ===========================================

REM Calculate dates
for /f "tokens=2 delims==" %%i in ('wmic os get localdatetime /value') do set datetime=%%i
set TODAY=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2%
set /a YESTERDAY_NUM=%datetime:~6,2%-1
if %YESTERDAY_NUM% lss 10 set YESTERDAY_NUM=0%YESTERDAY_NUM%
set YESTERDAY=%datetime:~0,4%-%datetime:~4,2%-%YESTERDAY_NUM%

echo Today: %TODAY%
echo Yesterday: %YESTERDAY%

REM Update the built HTML file
python update_html_dates.py "%DOCS_DIR%\build\html\index.html" "%TODAY%" "%YESTERDAY%"

echo HTML dates updated.

echo.
echo Step 3: Rebuilding documentation...
echo ===================================

cd %DOCS_DIR%
make.bat html

echo Documentation rebuild completed.

echo.
echo Step 4: Update complete!
echo ========================
echo The forecast webpage has been updated with the latest data.
echo Files updated:
echo - HTML documentation in docs/build/html/ with current dates
echo.
echo To view the updated webpage, open: docs\build\html\index.html
echo.
echo Update completed at %DATE% %TIME%
echo ========================================

REM Optional: Add deployment commands here
REM Example: copy files to web server, commit to git, etc.

pause