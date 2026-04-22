# required functions to get everything that we need
import subprocess
import json
from datetime import datetime, timedelta
import cfgrib
import os
import xarray as xr
import requests
import shutil
import numpy as np

import pandas as pd

def set_filenames(model, date):
    """
        Set the filenames based on the model, run, year, month, day, and forecast length.
        Paramters are selected in other .py scripts - funciton also loads specific model variables from JSON files.

        model: str - the model name (e.g., 'rdps', 'hrdps')
        Returns a DataFrame with the full path, extension, and file name for variable.

        The dry lightning forecast only uses 12UTC analysis output to run
        so forecast length is inherenetly 0. 
    """    
    year = int(date[0:4])
    month = int(date[5:7])
    day = int(date[8:10])

    print(f"Selected Model: {model}")
    print(f"Selected Model Run: 12Z")
    print(f"Selected Date: {year}-{month}-{day}--12Z")

    file_list = pd.DataFrame(columns=['full_path', 'extension', 'file', 'variable', 'datetime'])
    # Create the filename based on the selections
    if str(model) == 'rdps':
        # load the rdps_vars.json file
        with open('rdps_vars.json', 'r') as f:
            model_vars = json.load(f)
    elif str(model) == 'hrdps':
        # load the hrdps_vars.json file
        with open('hrdps_vars.json', 'r') as f:
            model_vars = json.load(f)

    model_initialization = 12  # 12 UTC

    # full datamart extension - for 0h 12 UTV forecast
    extension = f"https://dd.weather.gc.ca/today/model_{model}/{model_vars['configuration']['resolution']}/12/000/"

    for ii in range(len(model_vars['wx_vars'])):  #model_vars['wx_vars'].values():
            var = list(model_vars['wx_vars'].values())[ii]
            quick_var = list(model_vars['grib_vars'].values())[ii]

            file = f"{year}{month:02d}{day:02d}T12Z_MSC_{model.upper()}_{var}_RLatLon{model_vars['configuration']['grid']}_PT000H.grib2"

            # get a datetime variable and add it to the dataframe - this moves it to the local time set by the user
            timestamp = datetime(int(year), int(month), int(day), 12)

            print(timestamp, file)

            # populate the file_list DataFrame
            new_row = {
                'full_path': extension + file,
                'extension': extension,
                'file': file,
                'variable': quick_var,
                'datetime': timestamp
            }
            file_list.loc[len(file_list)] = new_row

    return file_list


# function to download each file using requests
def download_data(full_path, file_name):
    try:
        # Send a GET request to download the file
        response = requests.get(full_path, stream=True)
        response.raise_for_status()  # Check for HTTP request errors

        # Write the content to a local file
        with open(file_name, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                file.write(chunk)

        print(f"File downloaded successfully: {file_name}, moving to /temp/ ...")    

        dst_dir = "./temp"
        # clear .grib2 files from the temp directory if there is one 
        if os.path.exists(dst_dir):
            for file in os.listdir(dst_dir):
                if file.endswith(".grib2"):
                    file_path = os.path.join(dst_dir, file)
                    os.remove(file_path)

            # move the file to the temp directory 
            shutil.move(file_name, os.path.join(dst_dir, file_name))

    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")