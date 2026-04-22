""" 

    Validate the previous days d0 forecast.
    Calculated verfication statistics; POD, FAR, CSI, BIAS, and HSS.

    Validation is carried out at each sounding launch location 
    where surface precipitation obsesrvations are available

    Liam.Buchart@nrcan-rncan.gc.ca
    April 10, 2026

"""
#%%
import json
import psycopg2
import paramiko
import json
import csv
import sshtunnel

import pandas as pd
import geopandas as gpd
from scipy.spatial import cKDTree

from datetime import datetime, timedelta
from sshtunnel import SSHTunnelForwarder

##### User Input #####
vd = "other"  # "other" or "today"
if vd == "other":
    date_base = input("Enter the date to validate (YYYY-MM-DD): ")
    d0_date = (datetime.strptime(date_base, "%Y-%m-%d") + timedelta(days=-1)).strftime("%Y-%m-%d")
elif vd == "today":
    date_base = datetime.today()
    date = date_base.strftime("%Y-%m-%d")
    d0_date = (date_base + timedelta(days=-1)).strftime("%Y-%m-%d")
print(date_base)

model_select = "hrdps"  # ["rdps", "hrdps"]
##### END ######

# we will create a dataframe of the stations and their location
# we will then grad lightning and precipitation data from the previous day
# and add the the dataframe
# finally we extract the forecast value for these locations
#then do verification statistics

#%%
d0_df = pd.DataFrame()  # initialize the dataframe
# open the unqiue stations list with all required metadata
with open(f"../UTILS/unique_ecozone_stations.json", "r") as f:
    stations = json.load(f)

for key, values in stations.items():
    station_info = stations[key]
    print(key)  # print the station name
    print(values)  # print the metadata for the station
    # check if "cwfis_id" is in the metadata
    if "cwfis_id" in values:
        id = station_info["cwfis_id"]
    else:
        id = station_info["id"]  # if not, use the id
    # add the station name, id, and location to the dataframe
    d0_df = pd.concat(
        [
            d0_df,
            pd.DataFrame(
                {
                    "station": key,
                    "id": id,
                    "latitude": values["lat"],
                    "longitude": values["lon"],
                    "country": values["country"],
                    "rep_date": date,
                    "fcst_date": d0_date,
                },
                index=[0],
            ),
        ],
        ignore_index=True,
    ) 

#%%
print(d0_df.head())

# %%
def can_set_query(start, end, stationid):
    """
    start + end - strings YYYY-MM-DD
    station_name - string
    output: SQL query string
    """
    # query from can_hly2020s
    year = start[0:4]
    if int(year) < 2020 and int(year) > 2009:
        Q1 = f"SELECT rep_date, precip, pcp_period, sog FROM can_hly2010s WHERE "
    else:
        Q1 = f"SELECT rep_date, precip, pcp_period, sog FROM can_hly2020s WHERE "
    Q2 = f"wmo = '{stationid}' AND rep_date BETWEEN '{start} 12:00:00' AND '{end} 11:59:59' "
    Q3 = f"ORDER BY rep_date;" 

    QUERY = Q1 + Q2 + Q3

    return QUERY

def usa_set_query(start, end, stationid):
    """
    start + end - strings YYYY-MM-DD
    station_name - string
    output: SQL query string
    """
    # query from can_hly2020s
    year = start[0:4]
    if int(year) < 2020 and int(year) > 2009:
        Q1 = f"SELECT rep_date, precip, pcp_period, sog FROM usa_hly2010s WHERE "
    else:
        Q1 = f"SELECT rep_date, precip, pcp_period, sog FROM usa_hly2020s WHERE "
    Q2 = f"wmo = '{stationid}' AND rep_date BETWEEN '{start} 12:00:00' AND '{end} 11:59:59' "
    Q3 = f"ORDER BY rep_date;" 

    QUERY = Q1 + Q2 + Q3

    return QUERY

def db_query(query, csv_output='query_output.csv'):
    """
    Call the database to get wind data
    Inut: cursor object (defined below)
          start and end [dates YYYY-MM-DD - string]
    Output: pandas dataframe
    """
    # open the .keys json file
    with open('./.keys.json', 'r') as f:
        keys = json.load(f)

    # dagan info
    hostname = keys["dagan"]["full_name"]
    user = keys["dagan"]["user"]
    pw = keys["dagan"]["pw"]

    # database info
    d_hostname = keys["database"]["hostname"]
    d_username = keys["database"]["user"]
    db_name = keys["database"]["name"]
    d_pw = keys["database"]["pw"]

    portnum = 22  # just lookedup in my putty session

    # connect to remote database
    with sshtunnel.open_tunnel(
        (hostname, portnum),
        ssh_username=user,
        ssh_password=pw,
        remote_bind_address=(d_hostname, 5432)
    ) as tunnel:
        try:
            print("SSH tunnel established")
            print(f"{d_hostname, tunnel.local_bind_port}")
            print(f"Connecting to database {db_name} as user {d_username}")
            conn = psycopg2.connect(
                host=d_hostname,
                port=5432,
                database=db_name,
                user=d_username,
                password=d_pw
            )  

            cur = conn.cursor()
            # start by setting the search path
            cur.execute("set search_path to bt;")
            cur.execute(query)
            rows = cur.fetchall()  

            colnames = [desc[0] for desc in cur.description]
            with open(csv_output, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(colnames)
                writer.writerows(rows)
            cur.close()
            conn.close()

            print(f"Query results saved to {csv_output}")

        except Exception as e:
            print("Error:", e)

def full_station_location_cldn_query(lat, lon, dstart, dend):
    """
    Query the cldn_strikes table for strikes within ~20km (10km radius) 
    of a lat/lon point and between two dates

    Input:
           stat_info - station json object
           dstart - start date string 'YYYY-MM-DD'
           dend - end date string 'YYYY-MM-DD'
    """
    min_lat = lat-0.09
    max_lat = lat+0.09

    min_lon = lon-0.15
    max_lon = lon+0.15

    q1 = f"SELECT rep_date, lat, lon, peak_current, mult_flash FROM cldn_strikes "
    q2 = f"WHERE rep_date BETWEEN '{dstart} 00:00:00' and '{dend} 23:59:59' and "
    q3 = f"lat BETWEEN {min_lat} and {max_lat} and "
    q4 = f"lon BETWEEN {min_lon} and {max_lon} ORDER BY rep_date;"

    Query = q1 + q2 + q3 + q4

    return Query

def append_nearest_forecast(d0_df, fcst_df, forecast_col='text', lat_col='latitude', lon_col='longitude', out_col='forecast'):
    """Append nearest forecast values from fcst_df to d0_df using a KDTree.

    Parameters:
        d0_df: pandas.DataFrame with station locations.
        fcst_df: pandas.DataFrame or GeoDataFrame with forecast point locations.
        forecast_col: name of the forecast value column in fcst_df.
        lat_col: latitude column name for both dataframes.
        lon_col: longitude column name for both dataframes.
        out_col: output column name to add to d0_df.

    Returns:
        pandas.DataFrame: copy of d0_df with nearest forecast values appended.
    """
    if forecast_col not in fcst_df.columns:
        raise KeyError(f"Forecast column '{forecast_col}' not found in fcst_df")

    # Build KDTree from forecast point locations.
    tree = cKDTree(fcst_df[[lat_col, lon_col]].values)
    station_coords = d0_df[[lat_col, lon_col]].values

    # Query nearest forecast point for each station location.
    _, idx = tree.query(station_coords)
    nearest_forecast = fcst_df.iloc[idx][forecast_col].values

    result = d0_df.copy()
    result[out_col] = nearest_forecast
    return result

#%%
# loop through the datafame and get the precipitation and lightning data for each station
for index, row in d0_df.iterrows():
    sid = row["id"]
    lat = row["latitude"]
    lon = row["longitude"]

    # check if station is in the USA or Canada
    country = row["country"]

    if country == "Canada":
        query = can_set_query(d0_date, date, sid)
    elif country == "USA":
        query = usa_set_query(d0_date, date, sid)
    db_query(query, csv_output=f"./temp/precip_data_{sid}.csv")

    # lightning query
    query = full_station_location_cldn_query(lat, lon, d0_date, date)
    db_query(query, csv_output=f"./temp/cldn_data_{sid}.csv")

    # load the csvs and add the pertinent data to the dataframe
    precip_df = pd.read_csv(f"./temp/precip_data_{sid}.csv")
    cldn_df = pd.read_csv(f"./temp/cldn_data_{sid}.csv")

    # add the precip data to the dataframe
    d0_df.loc[index, "precip"] = precip_df["precip"].sum()

    # add the cldn data to the dataframe
    d0_df.loc[index, "cldn_strikes"] = len(cldn_df)

#%%
# now use a kd tree to extract the forecast value for each station location

# open the geopackage with the forecast data for the day before
fcst_gdf = gpd.read_file(f"../FORECAST/RESOURCES/d0_{d0_date}_lightning_forecast.gpkg")

#%%
print(d0_df.head())
print(fcst_gdf.head())

#%%
# append nearest forecast values to d0_df using KDTree
try:
    d0_df = append_nearest_forecast(d0_df, fcst_gdf)
except Exception as e:
    print('Error appending nearest forecast:', e)

print(d0_df.head())

# %%
# finally add a column to d0_df with a 1 or 0 
# for dry lightning (precip = 0 and cldn_strikes > 0) 
# dry_lightning=1, else = 0
d0_df["dry_lightning"] = ((d0_df["precip"] == 0) & (d0_df["cldn_strikes"] > 0)).astype(int)

# %%
print(d0_df.head())

# %%
# now its time to calculate the verification statistics; POD, FAR, CSI, BIAS, and HSS.
# we will use the following formulas:
# POD = TP / (TP + FN)
# FAR = FP / (TP + FP)
# CSI = TP / (TP + FP + FN)
# BIAS = (TP + FP) / (TP + FN)
# HSS = 2 * (TP * TN - FP * FN) / ((TP + FN) * (FN + TN) + (TP + FP) * (FP + TN))

# what defines a true positive, false positive, true negative, and false negative in this context?
# TP: dry_lightning = 1 and forecast = considerable
# TN: dry_lightning = 0 and forecast = low
# FP: dry_lightning = 0 and forecast = considerable
# FN: dry_lightning = 1 and forecast = low

# how to handle the "moderate" forecast category? For now, we will exclude it from the verification statistics calculation.
# call moderate forecast a hit if any lightning occurs
# TP_low: cldn_strikes > 0 and forecast = moderate
# TN_low: cldn_strikes = 0 and forecast = moderate
# FP_low: cldn_strikes = 0 and forecast = moderate
# FN_low: cldn_strikes > 0 and forecast = moderate

# calculate the contingency table values
# add them to dataframe
d0_df["TP"] = ((d0_df["dry_lightning"] == 1) & (d0_df["forecast"] == "considerable")).astype(int)
d0_df["TN"] = ((d0_df["dry_lightning"] == 0) & (d0_df["forecast"] == "low")).astype(int)
d0_df["FP"] = ((d0_df["dry_lightning"] == 0) & (d0_df["forecast"] == "considerable")).astype(int)
d0_df["FN"] = ((d0_df["dry_lightning"] == 1) & (d0_df["forecast"] == "low")).astype(int)

# actually for now treat moderate like considerable
d0_df["TP"] = ((d0_df["dry_lightning"] == 1) & (d0_df["forecast"] == "moderate")).astype(int)
d0_df["FP"] = ((d0_df["dry_lightning"] == 0) & (d0_df["forecast"] == "moderate")).astype(int)

# %%
print(d0_df.head())

# remove and rows with country=USA, forecast only valid in Canada!
# however, keep International falls and Caribou

d0_df = d0_df[(d0_df["country"] == "Canada") | (d0_df["station"].isin(["INTERNATIONAL+FALLS,+FALLS+INTERNATI", "CARIBOU,+CARIBOU+MUNICIPAL+AIRPORT"]))]

# %%
TP = d0_df["TP"].sum()
FP = d0_df["FP"].sum()
TN = d0_df["TN"].sum()
FN = d0_df["FN"].sum()

POD = TP / (TP + FN) if (TP + FN) > 0 else None
FAR = FP / (TP + FP) if (TP + FP) > 0 else None
CSI = TP / (TP + FP + FN) if (TP + FP + FN) > 0 else None
BIAS = (TP + FP) / (TP + FN) if (TP + FN) > 0 else None
HSS = 2 * (TP * TN - FP * FN) / ((TP + FN) * (FN + TN) + (TP + FP) * (FP + TN)) if ((TP + FN) * (FN + TN) + (TP + FP) * (FP + TN)) > 0 else None    
stats_dict = {"POD": POD, "FAR": FAR, "CSI": CSI, "BIAS": BIAS, "HSS": HSS, "rep_date": d0_date}

# convert stats_dict to a dataframe named stats
stats = pd.DataFrame([stats_dict])

print(stats)

#%% save the two dataframe to a csv
d0_df.to_csv(f"./archive/d0_validation_data_{d0_date}.csv", index=False)
stats.to_csv(f"./archive/d0_validation_stats_{d0_date}.csv", index=False)
# %%
