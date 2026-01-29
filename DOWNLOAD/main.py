"""
Run the three download scripts from 2016-2025 at a selected station

Liam.Buchart@nrcan-rncan.gc.ca
January 20, 2026
"""
#%%
import os
import json
from context import utils_dir
import geopandas as gpd

# open the stations json file
with open(utils_dir + 'unique_ecozone_stations.json', 'r') as f:
    stations = json.load(f)

all_stations = list(stations.keys())
print(all_stations)

census_shapefile = './ca.shp'
census = gpd.read_file(census_shapefile)

#%%
##### USER INPUT #####
station_select = all_stations[1]  # e.g., "Port Hardy"
years = range(2018, 2026)  # 2018 to 2025
time = 12  # which sounding do we want: 12Z
timestep = 1  # iterate every day

if station_select in all_stations:
    print(f"station {station_select} is valid...")
    station_info = stations[station_select]
    id = station_info["id"]
    station = station_info["sounding_id"]
    lat = station_info["lat"]
    lon = station_info["lon"]

    # check is "cwfis_id" key exists
    if "cwfis_id" in station_info:
        cwfis_id = station_info["cwfis_id"]
        print(f"CWFIS ID for {station_select} is {cwfis_id}")
    else:
        cwfis_id = id

else: 
    print("please ensure stations matches one from the 'all_stations' variable...")
##### END USER INPUT #####
##########

#%%
# loop through years and run the download scripts
for year in years:
    # define fire season
    start_date = f"{year}-05-01"  # YYYY-MM-DD
    end_date = f"{year}-09-30"  # YYYY-MM-DD

    mstart = start_date.split("-")[1]  # defining the month in which the fire season starts
    mend = end_date.split("-")[1]  # defining the month in which the fire

    station_info = stations[station_select]
    print(f"Downloading data for {station_select} for the year {year}...")

    # check if files exist for this station and year, if not create directory
    # if exists break the loop
    output_file = f"./OUTPUT/{id}/{id}_{year}_all_soundings.csv"
    output_dir = f"./OUTPUT/{id}"

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    if not os.path.exists(output_file):
        print(f"Output file {output_file} does not exist, proceeding with downloads...")
    else:
        print(f"Directory {output_file} already exists.")
        print("Skip to next year...")
        continue

    # get precipitation data
    from station_precip_query import can_set_query, usa_set_query, db_query
    from shapefile_utils import point_in_shapefile, load_simplified_shapefile
    if point_in_shapefile(shapefile_path=census_shapefile, lat=lat, lon=lon):
        print(f"{station_select} is in Canada, using Canadian precipitation query...")
        query = can_set_query(start_date, end_date, cwfis_id)
    else:
        print(f"{station_select} is in the USA, using USA precipitation query...")
        query = usa_set_query(start_date, end_date, cwfis_id)
    db_query(query=query, csv_output=f"./OUTPUT/{id}/{id}_{year}_precip_output.csv")

    # get lightning data
    from cldn_query import db_query, full_station_location_cldn_query
    query = full_station_location_cldn_query(stat_info=station_info, dstart=start_date, dend=end_date)
    db_query(query=query, csv_output=f"./OUTPUT/{id}/{id}_{year}_cldn_output.csv")

    # get sounding data 
    from uw_sounding_query import daterange, check_file, download_soundings
    all_soundings = check_file(id=id, year=year)

    # check if all_soundings in empty
    if all_soundings.empty:
        # getting 12Z soundings for the fire season
        download_soundings(year=year, mstart=int(mstart), mend=int(mend),
                           station=station, id=id)
    else:
        print(f"Soundings for {year} already downloaded...")

    print(f"Completed downloads for {station_select} for the year {year}.")

# %%
