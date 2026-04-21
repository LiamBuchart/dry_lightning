# Create a comprehensive map with Canadian borders, rivers, cities, and lightning/precipitation data
#%%
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from shapely.geometry import Point
import glob
import os

# Set up the figure with a nice style
plt.style.use('seaborn-v0_8-darkgrid')
fig = plt.figure(figsize=(14, 10))
ax = plt.axes(projection=ccrs.PlateCarree())

# Set reasonable bounds for Canada FIRST
ax.set_xlim(-141, -52)
ax.set_ylim(41, 84)

# Load Canada census shapefile (borders)
census_shapefile = 'ca.shp'
census = gpd.read_file(census_shapefile)

print(census)

# Ensure census is in EPSG:4326
if census.crs is None:
    print("Warning: Census CRS is None, assuming EPSG:4326")
    census = census.set_crs("EPSG:4326")
elif census.crs != "EPSG:4326":
    print(f"Converting census from {census.crs} to EPSG:4326")
    census = census.to_crs("EPSG:4326")

# Add major Canadian cities
major_cities = {
    'Toronto': (43.6629, -79.3957),
    'Vancouver': (49.2827, -123.1207),
    'Montreal': (45.5017, -73.5673),
    'Calgary': (51.0447, -114.0719),
    'Edmonton': (53.5461, -113.4938),
    'Ottawa': (45.4215, -75.6972),
    'Winnipeg': (49.8844, -97.1477),
    'Quebec City': (46.8139, -71.2080),
    'Halifax': (44.6426, -63.2181),
    'Victoria': (48.4261, -123.3623),
}

# deal with upper air stations
station_info = pd.read_csv('../UTILS/upa_station_info.csv')

# create geometry column for stations
geometry = [Point(xy) for xy in zip(station_info['lon'], station_info['lat'])]
stations_gdf = gpd.GeoDataFrame(station_info, geometry=geometry, crs="EPSG:4326")

# plot census borders
census.plot(ax=ax, color='lightgray', edgecolor='black', 
            linewidth=1.0, alpha=0.8, zorder=0)

# Plot stations
stations_gdf.plot(ax=ax, color='blue', markersize=50, zorder=2, 
                  transform=ccrs.PlateCarree())

# plot the cities
for city_name, (lat, lon) in major_cities.items():
    ax.plot(lon, lat, 'r*', markersize=12, alpha=0.7, zorder=5)
    ax.annotate(city_name, xy=(lon, lat), xytext=(5, 5), textcoords='offset points',
                fontsize=8, alpha=0.8, bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.3))

# nice map features
ax.set_xlabel('Longitude', fontsize=12)
ax.set_ylabel('Latitude', fontsize=12)
ax.set_title('Canada: Upper Air Stations', fontsize=14, fontweight='bold')
ax.legend(loc='lower left', fontsize=10)
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

plt.savefig('./canada_map.png', dpi=300)
print("Map saved as canada_map.png")
# %%
