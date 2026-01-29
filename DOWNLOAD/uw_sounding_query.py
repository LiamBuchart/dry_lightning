"""

    Download sounding launch date for a specifie period at a
    specific launch site (right now just 00 or 12Z)

    Liam.Buchart@nrcan-rncan.gc.ca
    December 16, 2025

"""
#%%
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import json
import time

import metpy.calc as mpcalc
from metpy.units import units
from siphon.simplewebservice.wyoming import WyomingUpperAir
from context import utils_dir

# open the stations json file
#with open(utils_dir + '/stations.json', 'r') as f:
#    stations = json.load(f)

#all_stations = stations.keys()

def daterange(dstart, dend):
    # create a list of the dates between start and end spacing one day
    # converts all times to 12z rather than 00Z
    delta = dend - dstart
    diff = delta.days
    for n in range(int(diff)):
        yield dstart + timedelta(n)

##### USER INPUT #####
#station_select = "Port+Hardy+UA" 
#year = 2025
##### END USER INPUT #####

#start_date = datetime(year, 5, 1, 12)  # start of the fire season
#end_date = datetime(year, 9, 30, 12)  # end of the fire season
#time_step = 1  # iterate every day
#time = 12  # which sounding do we want: 12Z
##### END USER INPUT

#if station_select in all_stations:
#    print(f"{station_select} is a valid station...")
#    station_info = stations[station_select]
#    id = station_info["id"]
#    station = station_info["sounding_id"]
#else: 
#    print("please ensure stations matches one from the 'all_stations' variable...")

#mstart = 5  # defining the month in which the fire season starts
#mend = 9  # defining the month in which the fire season ends

#delta = end_date - start_date
#print("Number of Days: ", delta.days)

#%%
def check_file(id, year):
    # check and see if we have downloaded any soundings before if not create a dataframe for them
    # or can be used similarly if you move the all soundings file out and then can create new
    try:   
        all_soundings = pd.read_csv(f"./OUTPUT/{id}_{year}_all_soundings.csv", sep=",")
        print("file exists - openings")
    except IOError:
        print("file does not exist or is not accesible, create")
        all_soundings = pd.DataFrame()  # empty datframe to store all data in

    print(all_soundings)

    result = all_soundings.dtypes   
    print("Output: ")
    print(result)

    return all_soundings

#%%
def download_soundings(year, mstart, mend, station, id):
    # download the soundings for the specified date range and station
    import time
    max_retries = 3  # max number of retries to get the data from the server

    start_date = datetime(year, 5, 1, 12)  # start of the fire season
    end_date = datetime(year, 9, 30, 12)  # end of the fire season

    # get the all_soundings dataframe
    all_soundings = check_file(id, year)

    for date in daterange(start_date, end_date):
        # loop through dates and append sounding info to the all_soundings dataframess
        month = str(date)[5:7]
        year = str(date)[0:4]
        day = str(date)[8:10]
        duse = int( day+month+year )
        month = int(month)
        

        if month < mstart or month > mend or duse in all_soundings.values:
            # dont want to make our wind profile from outside of fire season
            print("Already there or out of season")
            pass
        else:  # get months inside the fire season
            for attempt in range(max_retries):
                try: 
                    df = WyomingUpperAir.request_data(date, id)

                    df["ddmmyyyy"] = duse
                    all_soundings = pd.concat([all_soundings, df])

                    print(str(date), " - ", len(all_soundings["height"])) 
                    all_soundings.to_csv(f"./OUTPUT/{id}/{id}_{year}_all_soundings.csv", sep=',')
                    break

                except Exception as e:
                    print("Attempt", attempt+1, "failed:", e)
                    time.sleep(2)
                    print("Possibly No Sounding Data Today")
                    pass
            else:
                print("Giving up on: ", str(date))

    # one more save
    all_soundings.to_csv(f"./OUTPUT/{id}/{id}_{year}_all_soundings.csv", sep=',')  
    print("Complete")
# %%
