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
with open(utils_dir + '/stations.json', 'r') as f:
    stations = json.load(f)
all_stations = stations.keys()

# define a cutoff value for dry or moist lightning [mm]
precip_cutoff = 2.54

##### USER INPUT #####
station_select = "Stony Plain" 
##### END USER INPUT #####

# make sure the querying is done - plan to have this in main eventually 
if station_select in all_stations:
    print("station is valid...")
    station_info = stations[station_select]
    id = station_info["id"]
else: 
    print("please ensure stations matches one from the 'all_stations' variable...")

# %%
# get all files containing id and lightning_prediction
file_list = glob.glob(f"./OUTPUT/{id}_*_lightning_prediction.csv")

all_lightning = pd.DataFrame()
for file in file_list:
    print("processing file: ", file)
    df = pd.read_csv(file)
    
    # append to a master dataframe
    if file == file_list[0]:
        all_lightning = df
    else:
        all_lightning = pd.concat([all_lightning, df], ignore_index=True)  
print(all_lightning.shape)

# %%
is_lightning = all_lightning["no_lightning"] == 0
print(all_lightning[is_lightning])
print(all_lightning[is_lightning].shape)

# %%
# empty classifier column
all_lightning["classifier"] = np.nan

# create a classifier column 0 if no lightning, 1 if moist lightning, 2 if dry lightning
for row, index in all_lightning.iterrows():
    if index["no_lightning"] == 1:
        all_lightning.at[row, "classifier"] = 0
    elif index["moist_lightning"] == 1:
        all_lightning.at[row, "classifier"] = 1
    elif index["dry_lightning"] == 1:
        all_lightning.at[row, "classifier"] = 2

print(all_lightning.head())

#%%
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

# %%
# save the cleaned combined dataframe
all_lightning.to_csv(f"./PROCESSED/{id}_combined_lightning_prediction_cleaned.csv", sep=',', index=False)

# %%
