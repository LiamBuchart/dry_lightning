""""

    Use the psycopg2 module to grab data from the station precip date 
    data from the database tunnel onto the remote machine 
    using paramiko and sshtunnel

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

# open the stations json file
with open(utils_dir + '/stations.json', 'r') as f:
    stations = json.load(f)

all_stations = stations.keys()
print(all_stations)

##### USER INPUT
station_select = "Stony Plain" 
year = 2025
start_date = f"{year}-05-01"  # YYYY-MM-DD
end_date = f"{year}-09-30"  # YYYY-MM-DD

if station_select in all_stations:
    print("station is valid...")
    station_info = stations[station_select]
    id = station_info["id"]
else: 
    print("please ensure stations matches one from the 'all_stations' variable...")

#%%
def set_query(start, end, stationid):
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
    Q2 = f"wmo = '{stationid}' AND rep_date BETWEEN '{start} 00:00:00' AND '{end} 23:00:00' "
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

#%%
station_info = stations[station_select]
query = set_query(start=start_date, end=end_date, stationid=id)
db_query(query=query, csv_output=f"./OUTPUT/{id}_{year}_precip_output.csv")

# %%
