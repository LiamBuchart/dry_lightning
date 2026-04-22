"""

    Processing eccc model data for lightning prediction. 

    Input: a variety of .grib2 files for different variables
    Output: a combined csv file with all variables for each station and year
            same formatting as the combined lightning prediction dataset, to be used for LDA and Random Forest classification

    NOTE: make sure it is at least 9:20 MDT before executing to ensure the 12z runs are on the datamart

    Liam.Buchart@nrcan-rncan.gc.ca
    March 3, 2026

"""
#%%
import cfgrib
import os
import xarray as xr
import requests
import shutil
import difflib
import numpy as np
import pandas as pd
import geopandas as gpd
import json
import metpy.calc as mpcalc
from metpy.units import units

from shapely.geometry import Point
from datetime import datetime
from file_funcs import clean_dir, set_filenames, download_data, clean_dir_d1

##### User Input #####
date_base = datetime.today()
date = date_base.strftime("%Y-%m-%d")
print(date)

model_select = "hrdps"  # ["rdps", "hrdps"]
##### END ######

#%%
if str(model_select) == 'rdps':
    # load the rdps_vars.json file
    with open('rdps_vars.json', 'r') as f:
        model_vars = json.load(f)
elif str(model_select) == 'hrdps':
    # load the hrdps_vars.json file
    with open('hrdps_vars.json', 'r') as f:
        model_vars = json.load(f)

base_columns = model_vars["wx_vars"].keys()
pred_columns = model_vars["predict_vars"]

#%%
all_files = set_filenames(model_select, date, "000")
print(all_files.shape)

# print just the first row of all_files
print(all_files.iloc[0])

# %%
save_dir = "./temp"
clean_dir(save_dir)
for index, row in all_files.iterrows():
    output_file = row['file']
    file_url = row['full_path']
    print(f"Downloading {file_url}...")
    print(f"Saving as: {output_file}")

    download_data(file_url, output_file, save_dir)

#%%
def k_index(T500, dewpdep700, T850, dewpdep850):
    # an odd selection of variables from the datamart
    # though can still calculate k-index
    # variables will be pre-converted to numpy

    # get dewpoint 850
    Td850 = T850 - dewpdep850
    K = (T850 - T500) + Td850 - (dewpdep700)

    return K

def temp_diff(T1, T2):
    return T1 - T2

def TTI(T850, dewpdep850, T500):
    # calculate the total totals
    Td850 = T850 - dewpdep850
    totals = T850 + Td850 - (2 * T500)

    return totals

def get_lcl(p, T, dewdep):
    # get the lcl using metpy but need to get dewpoint
    Td = T - dewdep
    print("Adding Units...")
    p = p * units("hPa")
    T = T * units("degC")
    Td = Td * units("degC")
    lcl = mpcalc.lcl(p, T, Td)[0].magnitude

    return lcl

# %%
# load the grid grid stuff from the utils folder
# this will hold all future variables 
gdf = pd.read_csv(f"../UTILS/MODEL/grid_{model_select}_ecozones.csv")

# ensure GeoDataFrame
if "geometry" not in gdf.columns:
    gdf = gpd.GeoDataFrame(
        gdf,
        geometry=gpd.points_from_xy(gdf["lon"], gdf["lat"]),
        crs="EPSG:4326",
    )

print("Base grid loaded:", gdf.shape)

#%% -------------------------------------------------------------------
# Load each GRIB file and append as column
#----------------------------------------------------------------------
for base_var, var_name in model_vars["wx_vars"].items():

    matches = all_files[all_files["file"].str.contains(var_name)]

    if matches.empty:
        print(f"⚠ No GRIB file found for {var_name}, skipping")
        continue

    grib_file = matches.iloc[0]["file"]
    print(f"Loading {var_name} from {grib_file}")

    # open GRIB dataset
    ds = xr.open_dataset(f"{save_dir}/{grib_file}", 
                         engine="cfgrib")

    # normally a single variable per GRIB
    data_var = list(ds.data_vars)[0]
    values = ds[data_var].values.flatten()

    # safety check
    if len(values) != len(gdf):
        raise ValueError(
            f"Grid size mismatch for {var_name}: "
            f"{len(values)} values vs {len(gdf)} grid points"
        )

    # append column
    gdf[base_var] = values

#%% -------------------------------------------------------------------
# Final clean-up
#----------------------------------------------------------------------
final_columns = (
    [c for c in gdf.columns if c not in model_vars["wx_vars"].keys()]
    + list(model_vars["wx_vars"].keys())
)

gdf = gdf[final_columns]

print("All variables successfully loaded.")
# carry out some conversions
gdf["temperature"] = gdf["temperature"] - 273.15
gdf["T500"] = gdf["T500"] - 273.15
gdf["T850"] = gdf["T850"] - 273.15
gdf["press"] = gdf["press"] / 100
print(gdf.head())

#%%
gdf["dT850-500"] = temp_diff(gdf["T850"], 
                             gdf["T500"])
gdf["total_totals"] = TTI(gdf["T850"], 
                          gdf["dTTd850"], 
                          gdf["T500"])
gdf["lcl"] = get_lcl(gdf["press"].values,
                     gdf["temperature"].values,
                     gdf["dTTdSfc"].values)
gdf["K_index"] = k_index(gdf["T500"], 
                         gdf["dTTd700"],
                         gdf["T850"],
                         gdf["dTTd850"])
print(gdf["K_index"])

#%%
print(gdf)

# %%
# finally rename any columns that do not match the prediction column
# usually just case or minor differences
# save to the temp directory
print(pred_columns)
print(gdf.columns)

#%%
for var in pred_columns:
    print(var)
    # check if the variable is in the dataframe
    if var in list(gdf.columns):
        print("Column already good")
    else:
        # find the closest match 
        matches = difflib.get_close_matches(var, list(gdf.columns))
        if not matches:
            # should be a match converting columns to lower case
            low_var = var.upper()
            matches = difflib.get_close_matches(low_var, list(gdf.columns))

        print(var, matches)
        # rename the column to the var value
        gdf = gdf.rename(columns={matches[0]: var})

# %%
# save the the temp folder as a csv
gdf.to_csv(f"{save_dir}/{model_select}_d0_full.csv")




#%%
# -----------
## Do it again for the 24h forecast d1
# -----------
# start by clearing the gdf
gdf = []

all_files = set_filenames(model_select, date, "024")
print(all_files.shape)

# print just the first row of all_files
print(all_files.iloc[0])

# %%
save_dir = "./temp"
clean_dir_d1(save_dir)
for index, row in all_files.iterrows():
    output_file = row['file']
    file_url = row['full_path']
    print(f"Downloading {file_url}...")
    print(f"Saving as: {output_file}")

    download_data(file_url, output_file, save_dir)

#%%
# load the grid grid stuff from the utils folder
# this will hold all future variables 
gdf = pd.read_csv(f"../UTILS/MODEL/grid_{model_select}_ecozones.csv")

# ensure GeoDataFrame
if "geometry" not in gdf.columns:
    gdf = gpd.GeoDataFrame(
        gdf,
        geometry=gpd.points_from_xy(gdf["lon"], gdf["lat"]),
        crs="EPSG:4326",
    )

print("Base grid loaded:", gdf.shape)

#%% -------------------------------------------------------------------
# Load each GRIB file and append as column
#----------------------------------------------------------------------
for base_var, var_name in model_vars["wx_vars"].items():

    matches = all_files[all_files["file"].str.contains(var_name)]
    #matches = matches[matches["file"].str.contains("PT024H")]

    if matches.empty:
        print(f"⚠ No GRIB file found for {var_name}, skipping")
        continue

    grib_file = matches.iloc[0]["file"]
    print(f"Loading {var_name} from {grib_file}")

    # open GRIB dataset
    ds = xr.open_dataset(f"{save_dir}/{grib_file}", 
                         engine="cfgrib")

    # normally a single variable per GRIB
    data_var = list(ds.data_vars)[0]
    print(list(ds.data_vars))
    values = ds[data_var].values

    # why this is necessary is beyond me
    # will look into it
    if var_name == "SWEAT_Sfc":
        # this is 3d, just need first dim
        values = values[0, :, :]

    values = values.flatten()
    # safety check
    if len(values) != len(gdf):
        raise ValueError(
            f"Grid size mismatch for {var_name}: "
            f"{len(values)} values vs {len(gdf)} grid points"
        )

    # append column
    gdf[base_var] = values

#%% -------------------------------------------------------------------
# Final clean-up
#----------------------------------------------------------------------
final_columns = (
    [c for c in gdf.columns if c not in model_vars["wx_vars"].keys()]
    + list(model_vars["wx_vars"].keys())
)

gdf = gdf[final_columns]

print("All variables successfully loaded.")
# carry out some conversions
gdf["temperature"] = gdf["temperature"] - 273.15
gdf["T500"] = gdf["T500"] - 273.15
gdf["T850"] = gdf["T850"] - 273.15
gdf["press"] = gdf["press"] / 100
print(gdf.head())

#%%
gdf["dT850-500"] = temp_diff(gdf["T850"], 
                             gdf["T500"])
gdf["total_totals"] = TTI(gdf["T850"], 
                          gdf["dTTd850"], 
                          gdf["T500"])
gdf["lcl"] = get_lcl(gdf["press"].values,
                     gdf["temperature"].values,
                     gdf["dTTdSfc"].values)
gdf["K_index"] = k_index(gdf["T500"], 
                         gdf["dTTd700"],
                         gdf["T850"],
                         gdf["dTTd850"])
print(gdf["K_index"])

#%%
print(gdf)

# %%
# finally rename any columns that do not match the prediction column
# usually just case or minor differences
# save to the temp directory
print(pred_columns)
print(gdf.columns)

#%%
for var in pred_columns:
    print(var)
    # check if the variable is in the dataframe
    if var in list(gdf.columns):
        print("Column already good")
    else:
        # find the closest match 
        matches = difflib.get_close_matches(var, list(gdf.columns))
        if not matches:
            # should be a match converting columns to lower case
            low_var = var.upper()
            matches = difflib.get_close_matches(low_var, list(gdf.columns))

        print(var, matches)
        # rename the column to the var value
        gdf = gdf.rename(columns={matches[0]: var})

# %%
# save the the temp folder as a csv
gdf.to_csv(f"{save_dir}/{model_select}_d1_full.csv")