"""
Docstring for UTILS.dry_lightning_ecozone
Create a map of the ecozones in Canada and plot
the sounding launc locations

Create json file with ecozone and station infomation

Liam.Buchart@nrcan-rncan.gc.ca
January 22, 2026
"""
#%%
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
import json

import cartopy.crs as ccrs
import cartopy.feature as cfeature

# load ecozone shapefile
ecozone_shapefile = 'ecozones_FuelLayer.shp'
ecozones = gpd.read_file(ecozone_shapefile)

# Ensure ecozones are in EPSG:4326
if ecozones.crs is None:
    print("Warning: Ecozones CRS is None, assuming EPSG:4326")
    ecozones = ecozones.set_crs("EPSG:4326")
elif ecozones.crs != "EPSG:4326":
    print(f"Converting ecozones from {ecozones.crs} to EPSG:4326")
    ecozones = ecozones.to_crs("EPSG:4326")

# combine geometries if ZONE_NAME is duplicated
#ecozones = ecozones.dissolve(by='ZONE_NAME').reset_index()
print(ecozones)

# load stations information
station_info = pd.read_csv('upa_station_info.csv')

# create geometry column for stations
geometry = [Point(xy) for xy in zip(station_info['lon'], station_info['lat'])]
stations_gdf = gpd.GeoDataFrame(station_info, geometry=geometry, crs="EPSG:4326")

#%%
# plot ecozones and stations with map features
fig = plt.figure(figsize=(14, 10))
ax = plt.axes(projection=ccrs.PlateCarree())

# Plot ecozones
ecozones.plot(ax=ax, column='Name', legend=True, cmap='Set3', alpha=0.5, 
              zorder=1, transform=ccrs.PlateCarree()) # 'ZONE_NAME'

# Plot stations
stations_gdf.plot(ax=ax, color='red', markersize=50, zorder=2, 
                  transform=ccrs.PlateCarree())

# Add map features
ax.coastlines(resolution='50m', linewidth=1.2, color='black', zorder=5)
ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=1.2, 
               edgecolor='black', zorder=6)
ax.add_feature(cfeature.LAKES.with_scale('50m'), facecolor='none', 
               edgecolor='black', linewidth=0.9, zorder=7)

# Add provincial boundaries
provinces = cfeature.NaturalEarthFeature('cultural', 'admin_1_states_provinces_lines', '50m')
ax.add_feature(provinces, edgecolor='gray', facecolor='none', linewidth=0.8, zorder=8)

ax.set_title('Canadian Ecozones and Sounding Launch Stations', fontsize=16)
ax.gridlines(draw_labels=True, zorder=0)
ax.set_extent([-142, -55, 40, 70], crs=ccrs.PlateCarree())
plt.tight_layout()
plt.show()

# save the figure
fig.savefig('./FIGURES/ecozones_sounding_stations_map.png', dpi=300)

# %%
# for each ecozone, find stations within it and create a json file
# additionally if the station is within a buffer of the ecozone, include it as well
from shapely.geometry import Point
def stations_in_ecozone(ecozones_gdf, stations_gdf, buffer_km=250):
    ecozone_stations = {}

    for _, ecozone in ecozones_gdf.iterrows():
        zone_name = ecozone['Name'] # 'ZONE_NAME'
        ecozone_geom = ecozone['geometry']
        
        print(f"\nProcessing ecozone: {zone_name}")
        
        # First, try stations within the actual ecozone geometry
        stations_within_geom = stations_gdf[stations_gdf.geometry.intersects(ecozone_geom)]
        print(f"  Stations within geometry: {len(stations_within_geom)}")
        
        # Create a buffer around the ecozone for nearby stations
        ecozone_buffer = ecozone_geom.buffer(buffer_km / 111)  # Approximate conversion from km to degrees
        stations_within_buffer = stations_gdf[stations_gdf.geometry.intersects(ecozone_buffer)]
        print(f"  Stations within {buffer_km}km buffer: {len(stations_within_buffer)}")
        
        # Combine both: stations within geometry OR within buffer
        stations_within = pd.concat([stations_within_geom, stations_within_buffer])  #.drop_duplicates(subset=['aes'])

        # Store station info
        station_list = []
        for _, station in stations_within.iterrows():
            station_list.append({
                'name': station['name'].strip(),
                'sounding_id': station['aes'].strip(),
                'id': station['wmo'],
                'lat': station['lat'],
                'lon': station['lon'],
                'elevation_m': station['elevp']
            })
        
        print(f"  Total stations for {zone_name}: {len(station_list)}")
        ecozone_stations[zone_name] = station_list

    return ecozone_stations

# %%
ecozone_stations = stations_in_ecozone(ecozones, stations_gdf, buffer_km=150)

# save to json file
with open('./ecozone_stations.json', 'w') as f:
    json.dump(ecozone_stations, f, indent=4)

# %%
# loop through each ecozone and plot as above with stations
# reopen the ecozone_stations.json file
with open('./ecozone_stations.json', 'r') as f:
    ecozone_stations = json.load(f)

for zone_name, stations in ecozone_stations.items():
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())

    # Plot the specific ecozone
    ecozone_geom = ecozones[ecozones['Name'] == zone_name] # 'ZONE_NAME'
    ecozone_geom.plot(ax=ax, color='lightgreen', alpha=0.5, zorder=1, 
                      transform=ccrs.PlateCarree())

    # Plot stations in this ecozone
    for station in stations:
        ax.plot(station['lon'], station['lat'], marker='o', color='red', 
                markersize=8, transform=ccrs.PlateCarree(), zorder=2)
        ax.text(station['lon'] + 0.1, station['lat'] + 0.1, station['name'], 
                fontsize=9, transform=ccrs.PlateCarree(), zorder=3)

    # Add map features
    ax.coastlines(resolution='50m', linewidth=1.2, color='black', zorder=5)
    ax.add_feature(cfeature.BORDERS.with_scale('50m'), linewidth=1.2, 
                   edgecolor='black', zorder=6)
    ax.add_feature(cfeature.LAKES.with_scale('50m'), facecolor='none', 
                   edgecolor='black', linewidth=0.9, zorder=7)

    ax.set_title(f'Ecozone: {zone_name} with Sounding Stations', fontsize=14)
    ax.gridlines(draw_labels=True, zorder=0)
    plt.tight_layout()
    plt.show()

    # save the figure
    fig.savefig(f'./FIGURES/{zone_name}_sounding_stations_map.png', dpi=300)

# %%
# loop through the ecozone_stations .json file and crete a .json 
# with each unique station and associated information and ecozone
unique_stations = {}
for zone_name, stations in ecozone_stations.items():
    for station in stations:
        station_name = station['name']
        if station_name not in unique_stations:
            unique_stations[station_name] = {
                'name': station['name'],
                'id': station['id'],
                'sounding_id': station['sounding_id'],
                'lat': station['lat'],
                'lon': station['lon'],
                'elevation_m': station['elevation_m'],
                'ecozones': [zone_name]
            }
        else:
            unique_stations[station_name]['ecozones'].append(zone_name)

# save to json file
with open('./unique_ecozone_stations.json', 'w') as f:
    json.dump(unique_stations, f, indent=4)
# %%
