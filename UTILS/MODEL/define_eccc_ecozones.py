"""  

    Create a grid (using the model grid) which assigns the grid point center to the
    corresponding ecozone (see ../FIGURES/). These grids are a simple 1:n value corresponding the
    an ecozone id (see ../ecozone_stations.json).

    Liam.Buchart@nrcan-rncan.gc.ca
    February 5, 2026

"""
#%%
# Importation of Python modules 
import json
from datetime import datetime, timedelta
import re
import warnings

# The following modules must first be installed to use 
# this code out of Jupyter Notebook
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy
from owslib.wms import WebMapService
import pandas
from tabulate import tabulate
from file_funcs import set_filenames

#%%
# Ignore warnings from the OWSLib module
warnings.filterwarnings('ignore', module='owslib', category=UserWarning)

# bbox parameter
min_x, min_y, max_x, max_y = -135, 41, -45, 67  # lat, lons around canada

# Parameters choice
model_select = "REPS"  # [HRDPS, RDPS, GDPS, REPS]

# download a simple dataset from the model (any which cover the domain)
if not model_select == "HRDPS" or "REPS":
    layer = "DIAG.3_PRMM.ERMEAN"  #ETA_HPBL"
else:
    layer = "CONTINENTAL_HPBL"

# WMS service connection
wms = WebMapService(
    f"https://geo.weather.gc.ca/geomet?layers={model_select}.{layer}",
    version='1.3.0'
)

print(wms)

#%%
# Extraction of temporal information from metadata
def time_parameters(layer):
    start_time, end_time, interval = (wms[f"{model_select}.{layer}"]
                                      .dimensions['time']['values'][0]
                                      .split('/')
                                      )
    iso_format = '%Y-%m-%dT%H:%M:%SZ'
    start_time = datetime.strptime(start_time, iso_format)
    end_time = datetime.strptime(end_time, iso_format)
    interval = int(re.sub(r'\D', '', interval))
    return start_time, end_time, interval

start_time, end_time, interval = time_parameters(layer)

# To use specific starting and ending time, remove the #
# from the next lines and replace the start_time and
# end_time with the desired values:
# start_time = 'YYYY-MM-DDThh:00'
# end_time = 'YYYY-MM-DDThh:00'
# fmt = '%Y-%m-%dT%H:%M'
# start_time = datetime.strptime(start_time, fmt) - timedelta(hours=time_zone)
# end_time = datetime.strptime(end_time, fmt) - timedelta(hours=time_zone)

# Calculation of date and time for available predictions
# (the time variable represents time at UTC±00:00)
time = [start_time]
local_time = [start_time]  # + timedelta(hours=time_zone)] want full domain
while time[-1] < end_time:
    time.append(time[-1] + timedelta(hours=interval))
    local_time.append(time[-1])  # + timedelta(hours=time_zone)) # want full domain

print(time)
#%%
# Loop to carry out the requests and extract the mean
def request(layer):
    info = []
    pixel_value = []
    for timestep in time:
        # WMS GetFeatureInfo query
        info.append(wms.getfeatureinfo(layers=[layer],
                                       srs='EPSG:4326',
                                       bbox=(min_x, min_y, max_x, max_y),
                                       size=(100, 100),
                                       format='image/png',
                                       query_layers=[layer],
                                       info_format='application/json',
                                       xy=(50, 50),
                                       feature_count=1,
                                       time=str(timestep.isoformat()) + 'Z'
                                       ))
        # Probability extraction from the request's results
        text = info[-1].read().decode('utf-8')
        json_text = json.loads(text)
        pixel_value.append(
            float(json_text['features'][0]['properties']['value'])
            )
    
    return pixel_value

pixel_value = request(f"{model_select}.{layer}")

# %%
# visualize 
print(pixel_value)
print(type(pixel_value))
print(len(pixel_value))

# %%
