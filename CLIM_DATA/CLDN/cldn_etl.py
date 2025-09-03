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

from sshtunnel import SSHTunnelForwarder

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

#%%
# ssh tunnel into s-edm-daagan
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(hostname, port=portnum, username=user, password=pw)

#%%
def cldn_query(cursor, year, month, day):
    # all configuratation is based on testing inside the cldn_strikes table
    cursor.execute("set search_path to bt;")

#%%
conn = psycopg2.connect(
    host=d_hostname,
    port=5432,  # defauly postgreSQL port
    database=db_name,
    user=d_username,
    password=d_pw
)

# need a cursor to perform database operations
cur = conn.cursor()

#%%
# close the cursor and leave the database
cur.close()
conn.close()

#%%
# get out of the ssh tunnel
client.close()
