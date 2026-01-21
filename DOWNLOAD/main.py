"""
Run the three download scripts from 2016-2025 at a selected station

Liam.Buchart@nrcan-rncan.gc.ca
January 20, 2026
"""

import json
from context import utils_dir

# open the stations json file
with open(utils_dir + '/stations.json', 'r') as f:
    stations = json.load(f)

all_stations = stations.keys()
print(all_stations)

##### USER INPUT #####
station_select = "Stony Plain" 
years = range(2016, 2026)  # 2016 to 2025

if station_select in all_stations:
    print("station is valid...")
    station_info = stations[station_select]
    id = station_info["id"]
else: 
    print("please ensure stations matches one from the 'all_stations' variable...")
##### END USER INPUT #####

# loop through years and run the download scripts
for year in years:
    # define fire season
    start_date = f"{year}-05-01"  # YYYY-MM-DD
    end_date = f"{year}-09-30"  # YYYY-MM-DD
    station_info = stations[station_select]

    # get precipitation data
    from station_precip_query import set_query, db_query
    query = set_query(start_date, end_date, station_info["id"])
    db_query(query=query, csv_output=f"./OUTPUT/{id}_{year}_precip_output.csv")

    # get lightning data
    from cldn_query import db_query, full_station_location_cldn_query
    query = full_station_location_cldn_query(stat_info=station_info, dstart=start_date, dend=end_date)
    db_query(query=query, csv_output=f"./OUTPUT/{id}_{year}_cldn_output.csv")

    # get sounding data 

