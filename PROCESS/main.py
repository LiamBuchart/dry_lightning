"""
Docstring for main.py

Itartively run combine_dateset.py for all years
then run clean_combine.py to clean and combine all years
Finally a function here will combine files that are in the 
same form the same ecozone

Input: years and ecozone

Output: cleaned and combined files per ecozone

The output file is the final file used in
station_lightning_lda.py

Liam.Buchart@nrcan-rncan.gc.ca
January 28, 2026
"""
#%%
import os
from context import utils_dir, download_dir
from combine_dataset import combine_year
from clean_combine import clean_station


def main(station_select, start_year=2018, end_year=2025):
    """Run combining for each year then clean/aggregate all years for station."""
    # ensure we're in the PROCESS directory so relative paths in scripts work
    os.chdir(os.path.dirname(__file__))

    for yr in range(start_year, end_year + 1):
        print(f"Running combine for {station_select} year {yr} ...")
        combine_year(station_select, yr)

    print("Running clean_combine to aggregate all years...")
    clean_station(station_select)
    print("Processing complete.")


if __name__ == "__main__":
    # set a default station; update 
    station_select = "THE+PAS+UA"
    main(station_select, 2018, 2025)

