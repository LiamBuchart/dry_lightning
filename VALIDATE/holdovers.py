""" 

    Plot the lighting that occurs over the last 20 days inside the "Considerable" forecast for the day. 
    Color the stikes by the date on which they occur. Cooler colors for further out. 
    Days 1-2 (red), 3-5 (orange), 6-9 (yellow), 10-14 (green), 15-20 (blue) 

"""
#%%
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import cartopy.feature as cfeature

import folium

from pathlib import Path
from scipy.spatial import cKDTree
from datetime import datetime, timedelta
from sshtunnel import SSHTunnelForwarder

from context import forecast_dir
from file_funcs import db_query, all_stn_cldn_query

#%%
BASE_DIR = Path(__file__).parent
PLOTS_DIR = BASE_DIR / "plots"
TEMP_DIR = BASE_DIR / "temp"
PLOTS_DIR.mkdir(exist_ok=True)

extension = "lightning_forecast.gpkg"
holdover_days = 20 # number of forecasts to pull up

date_base = datetime.today()

#%%
def plot_color(ii):
    # assign color of plots for a forecast day based 
    # on an interger ii
    if ii <= 2:  
        pcolor = "firebrick"
        ptext = "Day 1-2"
    elif ii < 6 and ii > 2:
        pcolor = "Orange"
        ptext = "Day 3-5"
    elif ii < 10 and ii >= 6:
        pcolor = "Yellow"
        ptext = "Day 6-9"
    elif ii < 14 and ii >= 10:
        pcolor = "limegreen"
        ptext = "Day 10-14"
    else:
        pcolor = "cornflowerblue"
        ptext = "Day 15-20"

    return pcolor, ptext

#%%
def assign_bin_to_strike(ldf, fcst_df):
    # ldf is a loaded csv file with lightning strike data
    # fcst_df is a loaded .gpkg of the days forecast
    # add a column to ldf named "category" that pulls the nearest
    # forecast point from fcst_df and assigns it
    # Use a KDTree on (lat, lon) to find nearest forecast point for each strike.
    # Expect ldf to have columns 'lat' and 'lon'
    # and fcst_df to have forecast values in a column named 'text' and either
    forecast_col = 'text'
    out_col = 'category'

    # operate on a copy
    result = ldf.copy()

    # prepare fcst coordinate columns
    if 'latitude' not in fcst_df.columns or 'longitude' not in fcst_df.columns:
        # try to extract from geometry if available
        if 'geometry' in fcst_df.columns:
            try:
                result_fcst = fcst_df.copy()
                result_fcst['latitude'] = fcst_df.geometry.y
                result_fcst['longitude'] = fcst_df.geometry.x
            except Exception:
                raise KeyError("fcst_df must contain 'latitude'/'longitude' or a valid 'geometry' column")
        else:
            raise KeyError("fcst_df must contain 'latitude' and 'longitude' columns or a 'geometry' column")
    else:
        result_fcst = fcst_df.copy()

    if forecast_col not in result_fcst.columns:
        raise KeyError(f"Forecast column '{forecast_col}' not found in fcst_df")

    # ensure ldf has lat/lon
    if ('lat' not in result.columns) or ('lon' not in result.columns):
        # try common alternatives
        if ('latitude' in result.columns) and ('longitude' in result.columns):
            result['lat'] = result['latitude']
            result['lon'] = result['longitude']
        else:
            raise KeyError("ldf must contain 'lat' and 'lon' or 'latitude' and 'longitude' columns")

    # build KDTree from forecast points
    tree = cKDTree(result_fcst[['latitude', 'longitude']].values)

    strike_coords = result[['lat', 'lon']].values
    _, idx = tree.query(strike_coords)

    # assign forecast text for nearest forecast point to each strike
    nearest_vals = result_fcst.iloc[idx][forecast_col].values
    result[out_col] = nearest_vals

    # now just return the rows that are considerable
    result = result[result[out_col] == "considerable"]

    return result

# %%
# NRCan Projection information
plot_projection = ccrs.PlateCarree()  # 3978

fig = plt.figure(figsize=(12, 12))
ax = plt.axes(projection=plot_projection)

ax.set_extent(
    [-142, -52, 41, 71],   # lon_min, lon_max, lat_min, lat_max
    crs=ccrs.PlateCarree()
)

# --------------------------------------
# Base map
# --------------------------------------
ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor="#e6f2ff", zorder=0)
ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor="#f7f7f7", zorder=1)
ax.add_feature(cfeature.LAKES.with_scale("50m"), facecolor="#e6f2ff", edgecolor="black", linewidth=0.3, zorder=2)
ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.8, edgecolor="black", zorder=5)
ax.add_feature(cfeature.BORDERS.with_scale("50m"), linewidth=0.8, edgecolor="black", zorder=5)
ax.add_feature(cfeature.RIVERS.with_scale("50m"), edgecolor="black", linewidth=0.4, alpha=0.8, zorder=6)
ax.add_feature(
    cfeature.NaturalEarthFeature(
        category="cultural",
        name="admin_1_states_provinces_lines",
        scale="50m",
        facecolor="none",
        zorder=7
    ),
    edgecolor="black",
    linewidth=1
)
ax.add_feature(cfeature.LAKES.with_scale("50m"), facecolor="none", edgecolor="#2e6eb5", linewidth=0.35, zorder=7)

# track which colors were used so we can build a legend
_colors_seen = {}

#%%
# open the corresponding forecasts with geopandas
# furthest back forecast day
# ii also is counting the number of days so we can plot with perty colors

# single dataframe with each day
all_plot_df = []
all_pos_df = []
all_neg_df = []
count = 1
for ii in range(-1*holdover_days, 0):
    # start with todays forecast output and work backwards
    date = (date_base + timedelta(days=ii)).strftime("%Y-%m-%d")

    # get the end of the d0 forecast period for lightning query
    date_end = (date_base + timedelta(days=ii+1)).strftime("%Y-%m-%d")

    # open the d0 forecast at "date"
    full_file = f"d0_{date}_{extension}"
    path = f"{forecast_dir}RESOURCES/{full_file}"
    print(path)

    # now go to next date before we might step out of the loop
    count = count + 1
    try:
        fcst = gpd.read_file(path)

    except Exception as e:
        print(f"No forecast for {path}: {e}")
        print("Skipping this forecast day")
        continue

    # skip if file read but contains no features
    if fcst is None or len(fcst) == 0:
        print(f"Forecast file empty: {path}")
        continue
    #print(fcst.head())
 
    # query the db for lightning in the forecast period
    query = all_stn_cldn_query(date, date_end)
    outfile = f"{TEMP_DIR}/holdover_lightning.csv"
    db_query(query, csv_output=outfile)

    lightning_df = pd.read_csv(outfile)
    
    # append a column called Holdover Days
    lightning_df["Holdover Days"] = abs(ii)

    plot_df = assign_bin_to_strike(lightning_df,
                                   fcst)

    # ***** NOTE ***** just looking
    # plot just the positive strikes
    pos_df = plot_df[plot_df["peak_current"] > 0]
    # and just the negative strikes
    neg_df = plot_df[plot_df["peak_current"] < 0]

    print(plot_df.head())

    if not plot_df.empty:
        all_plot_df.append(plot_df)
    if not pos_df.empty:
        all_pos_df.append(pos_df)
    if not plot_df.empty:
        all_neg_df.append(neg_df)

    pcolor, ptext = plot_color(abs(ii))
    # plot strikes for this iteration onto the shared axes
    try:
        pcolor_l = pcolor.lower()
        if not plot_df.empty:
            ax.scatter(plot_df['lon'], plot_df['lat'], c=pcolor_l, marker='x', s=3, linewidths=0.8, transform=ccrs.PlateCarree(), alpha=0.75, zorder=2)
            # record the display label for this color
            _colors_seen[pcolor_l] = ptext
    except Exception as e:
        print('Plotting error:', e)

# build legend from seen colors and show plot
handles = [mpatches.Patch(color=color, label=label) for color, label in _colors_seen.items()]
if handles:
    ax.legend(handles=handles,
              title="Lightning Strike Day", 
              loc='upper right',
              frameon=True,
              framealpha=0.95)

# --------------------------------------
# Graticules
# --------------------------------------
gl = ax.gridlines(
    draw_labels=True,
    linewidth=0.3,
    linestyle="--",
    color="gray",
    alpha=0.5
)
gl.top_labels = False
gl.right_labels = False  

# --------------------------------------
# Titles 
# --------------------------------------
dplot = date_base.strftime("%Y-%m-%d")
ax.set_title(
    f"Potential Holdover Lightning Strikes in the Last 20 Days From {dplot}",
    fontsize=14,
    fontweight="bold",
    loc="left",
    pad=12
)
fig.subplots_adjust(top=0.92)

out_path = PLOTS_DIR / "holdover_potential.png"
try:
    fig.savefig(str(out_path), dpi=300, bbox_inches="tight")
    print(f"Figure saved to {out_path}")
except Exception as e:
    print("Error saving figure:", e)

plt.show()
plt.close(fig)

print("Complete")

# %%
# now create a similar interative map
# combine all collected data
if all_plot_df:
    plot_df_all = pd.concat(all_plot_df, ignore_index=True)
else:
    plot_df_all = pd.DataFrame(columns=["lat", "lon", "category", "peak_current"])

if all_pos_df:
    pos_df_all = pd.concat(all_pos_df, ignore_index=True)
else:
    pos_df_all = pd.DataFrame(columns=["lat", "lon", "category", "peak_current"])

if all_neg_df:
    neg_df_all = pd.concat(all_neg_df, ignore_index=True)
else: 
    neg_df_all = pd.DataFrame(columns=["lat", "lon", "category", "peak_current"])
print(plot_df_all.tail())

# remove all data below 41.7N
plot_df_all = plot_df_all[plot_df_all["lat"] >= 41.7]
pos_df_all = pos_df_all[pos_df_all["lat"] >= 41.7]
neg_df_all = neg_df_all[neg_df_all["lat"] >= 41.7]

# open the corresponding forecasts with geopandas
# start with yesterdays forecast hence days = -1
# ii also is counting the number of days so we can plot with perty colors
# however we have already gathered the dataframes
# use a loop to get the date
#if all_plot_df.empty:
#    raise ValueError("No strike data available to plot.")

#%%
center_lat = plot_df_all["lat"].mean()
center_lon = plot_df_all["lon"].mean()

m = folium.Map(location=[center_lat, center_lon], zoom_start=5, tiles="OpenStreetMap")

# Main layer: all strikes from plot_df
main_fg = folium.FeatureGroup(name="All strikes", show=True)

for _, row in plot_df_all.iterrows():
    category = row.get("Holdover Days", "unknown")
    pday = row.get("rep_date", "unknown")
    lat = row["lat"]
    lon = row["lon"]
    pcolor, ptext = plot_color(int(category))

    folium.CircleMarker(
        location=[lat, lon],
        radius=0.7,
        color=pcolor,
        fill=True,
        fill_opacity=0.8,
        popup=(
            f"<b>{ptext}<br>"
            f"<b>Occurred {pday}<br>"
            f"<b>Peak current:</b> {row.get('peak_current', 'n/a')}<br>"
            f"<b>Lat:</b> {lat:.3f}<br>"
            f"<b>Lon:</b> {lon:.3f}"
        ),
    ).add_to(main_fg)

main_fg.add_to(m)

# Add layer control and fit bounds
folium.LayerControl(position="topright").add_to(m)

bounds = [
    [plot_df_all["lat"].min()+10, plot_df_all["lon"].min()],
    [plot_df_all["lat"].max()+2, plot_df_all["lon"].max()-2],
]
m.fit_bounds(bounds)

# Save to HTML
outpath = PLOTS_DIR / "interactive_holdover_map.html"
m.save(outpath)
print("Saved holdover_map.html")
# %%
