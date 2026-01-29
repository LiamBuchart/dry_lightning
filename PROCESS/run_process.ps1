param(
    [string]$Station = "THE+PAS+UA",
    [int]$StartYear = 2018,
    [int]$EndYear = 2025
)

# Ensure script runs from the script directory (PROCESS)
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "Running combine for station '$Station' from $StartYear to $EndYear..."

for ($y = $StartYear; $y -le $EndYear; $y++) {
    Write-Host "=== Combining year $y ==="
    python -c "import sys; sys.path.insert(0, '.'); from combine_dataset import combine_year; combine_year('$Station', $y)"
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error running combine_year for $y (exit code $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Write-Host "Running clean_station (writing output)"
python -c "import sys; sys.path.insert(0, '.'); from clean_combine import clean_station; clean_station('$Station', dry_run=False)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error running clean_station (exit code $LASTEXITCODE)" -ForegroundColor Red
    exit $LASTEXITCODE
}

Write-Host "All done." -ForegroundColor Green
