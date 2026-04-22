"""
Docstring for UTILS.eco_zone_gridded
Create a grid based on the desired model ["HRDPS", "RDPS]

Read the "grid_id" for each ecozone and give this value the 
appropriate value to each grid cell
"""
#%%
# Modules importation
from datetime import datetime
import json
import math
from textwrap import fill

import cartopy.crs as ccrs
from cartopy.io.img_tiles import OSM
from matplotlib import pyplot as plt, dates as mdates
from osgeo import ogr, osr
from owslib.ogcapi.features import Features
import numpy as np
import pandas as pd
from tabulate import tabulate

#%%
# Get current date and time
now = datetime.now()

# Format as YYYY-MM-DD
current_date = now.strftime("%Y-%m-%d")

# ESPG code of the preferred projection to create the buffer
# NAD83 / Statistics
projection = 3347

# Formatting of the selected time period
time_ = f"{current_date}"