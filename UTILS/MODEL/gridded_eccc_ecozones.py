"""

    Pull data from the MSc datamart to get a RDPS and HRDPS grid
    use the ecozones and create a dataframe for both models
    that includes lat and lon points the name of the ecozone that the point sits in 
    and a zones classifier (integer)

    February 17, 2026
    Liam.Buchart@nrcan-rncan.gc.ca

"""
#%%
import cfgrib
import os
import xarray as xr
import requests
import shutil
import numpy as np
import pandas as pd
import geopandas as gpd
import json

from shapely.geometry import Point
from datetime import datetime
from file_funcs import set_filenames, download_data

##### User Input #####
date_base = datetime.today()
date = date_base.strftime("%Y-%m-%d")
print(date)

model_select = "hrdps"  # ["rdps", "hrdps"]

# %%
all_files = set_filenames(model_select, date)
print(all_files.shape)

# print just the first row of all_files
print(all_files.iloc[0])

# %%
download = all_files.iloc[0]
output_file = download['file']
file_url = download['full_path']
print(f"Downloading {file_url}...")
print(f"Saving as: {output_file}")

download_data(file_url, output_file)

# %%
# load the temperature vairable to get the latlon grid
# use xarray to open the grib file and extract the lat and lon values
ds = xr.open_dataset(download["file"], engine="cfgrib")
lats = ds.latitude.values.flatten()
lons = ds.longitude.values.flatten()

print(np.shape(lats), np.shape(lons))

# %%
# build a GeoDataFrame of the grid points using the flattened lat/lon arrays
# this will allow us to spatially join against the ecozone polygons efficiently

# load ecozone shapefile
ecozone_shapefile = '../ecozones_FuelLayer.shp'
ecozones = gpd.read_file(ecozone_shapefile)

# ensure ecozones are in EPSG:4326
if ecozones.crs is None:
    print("Warning: Ecozones CRS is None, assuming EPSG:4326")
    ecozones = ecozones.set_crs("EPSG:4326")
elif ecozones.crs != "EPSG:4326":
    print(f"Converting ecozones from {ecozones.crs} to EPSG:4326")
    ecozones = ecozones.to_crs("EPSG:4326")

# load ecozone mapping from JSON (parent directory)
json_path = os.path.join(os.path.dirname(__file__), '..', 'ecozone_stations.json')
try:
    with open(json_path) as jf:
        station_data = json.load(jf)
except FileNotFoundError:
    raise RuntimeError(f"Could not find ecozone stations file at {json_path}")

# build a simple name -> grid_id map; first element in each list holds grid_id
ecozone_id_map = {}
for zone, entries in station_data.items():
    if isinstance(entries, list) and entries:
        first = entries[0]
        if 'grid_id' in first:
            ecozone_id_map[zone] = first['grid_id']
print(ecozone_id_map)

print(f"Loaded {len(ecozone_id_map)} ecozone IDs from {json_path}")

#%%
# create geodataframe for grid points
gdf = gpd.GeoDataFrame(
    {"lat": lats, "lon": lons},
    geometry=gpd.points_from_xy(lons, lats),
    crs="EPSG:4326",
)

# perform spatial join (within predicate) to tag each point with its ecozone name only
joined = gpd.sjoin(
    gdf,
    ecozones[['Name', 'geometry']],
    how='left',
    predicate='within',
)

# replace missing zone names for points outside any polygon
joined['Name'].fillna('No Ecozone', inplace=True)

# rename column for clarity
joined = joined.rename(columns={
    'Name': 'ecozone',
})

# add ecozone_id from JSON mapping; unmapped values (e.g. 'No Ecozone') become NaN
joined['ecozone_id'] = joined['ecozone'].map(ecozone_id_map)

# output to CSV
out_csv = f"grid_{model_select}_ecozones.csv"
# drop any unwanted columns (none expected) before saving
joined.to_csv(out_csv, index=False)
print(f"Saved lat-lon ecozone lookup to {out_csv}")
# %%
