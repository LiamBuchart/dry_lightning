""""

    Use the psycopg2 module to grab data from the CLDN data from the database
    tunnel onto the remote machine using paramiko and sshtunnel

    liam.buchart@nrcan-rncan.gc.ca
    September 3, 2025

"""
#%%
import psycopg2
import paramiko
import json
import csv
import sshtunnel

from sshtunnel import SSHTunnelForwarder
from context import utils_dir

## open the stations json file
#with open(utils_dir + '/stations.json', 'r') as f:
#    stations = json.load(f)
#
#all_stations = stations.keys()
#print(all_stations)

##### USER INPUT
#station_select = "Stony Plain"
#year = 2025
#start_date = f"{year}-05-01"  # YYYY-MM-DD
#end_date = f"{year}-09-30"  # YYYY-MM-DD

#if station_select in all_stations:
#    print("station is valid...")
#    station_info = stations[station_select]
#    id = station_info["id"]
#else: 
#    print("please ensure stations matches one from the 'all_stations' variable...")

#%%
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

def full_station_location_cldn_query(stat_info, dstart, dend):
    """
    Query the cldn_strikes table for strikes within ~20km (10km radius) 
    of a lat/lon point and between two dates

    Input:
           stat_info - station json object
           dstart - start date string 'YYYY-MM-DD'
           dend - end date string 'YYYY-MM-DD'
    """
    lat = stat_info['Lat']
    min_lat = lat-0.09
    max_lat = lat+0.09

    lon = stat_info['Lon']
    min_lon = lon-0.15
    max_lon = lon+0.15

    q1 = f"SELECT rep_date, lat, lon, peak_current, mult_flash FROM cldn_strikes "
    q2 = f"WHERE rep_date BETWEEN '{dstart} 00:00:00' and '{dend} 23:59:59' and "
    q3 = f"lat BETWEEN {min_lat} and {max_lat} and "
    q4 = f"lon BETWEEN {min_lon} and {max_lon} ORDER BY rep_date;"

    Query = q1 + q2 + q3 + q4

    return Query

#%%
#station_info = stations[station_select]
#query = full_station_location_cldn_query(stat_info=station_info, dstart=start_date, dend=end_date)
#db_query(query=query, csv_output=f"./OUTPUT/{id}_{year}_cldn_output.csv")
# %%
