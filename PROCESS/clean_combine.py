"""
    Docstring for clean_combine
    load all *lightning_prediction.csv files and combine
    clean and have a classifier column to be used for LDA
    and Random Forest models

    Liam.Buchart@nrcan-rncan.gc.ca
    December 23, 2025
"""
#%%
import pandas as pd
import numpy as np
import json
import glob

from context import utils_dir

#%%
# open the stations json file
with open(utils_dir + '/unique_ecozone_stations.json', 'r') as f:
    stations = json.load(f)
all_stations = stations.keys()

# define a cutoff value for dry or moist lightning [mm]
precip_cutoff = 2.54

def clean_station(station_select, dry_run=False):
    """Combine all yearly lightning_prediction files for a station and clean them.

    Parameters
    ----------
    station_select : str
        Station key (case-insensitive) from unique_ecozone_stations.json
    dry_run : bool
        If True, do not write output CSV; just print summary and return the dataframe
    """
    import difflib

    # Normalize and try to find station key (case-insensitive)
    station_key = station_select.strip().upper()
    if station_key not in stations:
        # try to find close matches
        close = difflib.get_close_matches(station_key, list(stations.keys()), n=3, cutoff=0.6)
        if close:
            print(f"Station '{station_select}' not found. Did you mean: {close}?")
        else:
            print(f"Station '{station_select}' not found in stations list.")
        return None

    print("station is valid...")
    station_info = stations[station_key]
    id = station_info["id"]

    # get all files containing id and lightning_prediction
    file_list = glob.glob(f"./OUTPUT/{id}_*_lightning_prediction.csv")

    if not file_list:
        print(f"No files found for station id {id} in ./OUTPUT/. Nothing to do.")
        return None

    all_lightning = pd.DataFrame()
    for i, file in enumerate(file_list):
        print("processing file: ", file)
        df = pd.read_csv(file)

        # append to a master dataframe
        if i == 0:
            all_lightning = df
        else:
            all_lightning = pd.concat([all_lightning, df], ignore_index=True)
    print(f"Combined shape: {all_lightning.shape}")

    is_lightning = all_lightning["no_lightning"] == 0
    print(all_lightning[is_lightning].head())
    print(f"Lightning rows: {all_lightning[is_lightning].shape}")

    # empty classifier column
    all_lightning["classifier"] = np.nan

    # create a classifier column 0 if no lightning, 1 if moist lightning, 2 if dry lightning
    for row_idx, row in all_lightning.iterrows():
        if row["no_lightning"] == 1:
            all_lightning.at[row_idx, "classifier"] = 0
        elif row["moist_lightning"] == 1:
            all_lightning.at[row_idx, "classifier"] = 1
        elif row["dry_lightning"] == 1:
            all_lightning.at[row_idx, "classifier"] = 2

    print(all_lightning.head())

    # normalize a few columns and convert to z-scores
    from scipy.stats import zscore
    cols_normalize = ["dTTd850", "dT850-500", "K_index", 
                      "lcl", "pw", "lifted_index", "sfc_rh"]

    for col in cols_normalize:
        print(f"normalizing column: {col}")
        all_lightning[f"{col}_zscore"] = zscore(all_lightning[col], nan_policy='omit')

    # normalize mucape and dTTd700 differently - log transform
    all_lightning["mucape_log"] = np.log1p(all_lightning["mucape"])
    all_lightning["dtTd700_log"] = np.log1p(all_lightning["dTTd700"])

    # round all columns in dataframe to 2 decimal places
    all_lightning = all_lightning.round(2)

    print(all_lightning.head())

    # save the cleaned combined dataframe
    all_lightning.to_csv(f"./CLEANED/{id}_combined_lightning_prediction_cleaned.csv", sep=',', index=False)
