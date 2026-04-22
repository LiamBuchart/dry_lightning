"""

    Carry out the lda-rf probability forecast
    on download eccc data

    Forecast maps are valid from:
    12UTC today to 12UTC tomorrow (d0)

    Note: as of now just doing hrdps data not rdps
          flexible to extend to d1 forecast


"""
#%%
import os
import numpy as np
import pandas as pd
import geopandas as gpd
import json
import joblib

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import cartopy.crs as ccrs
import cartopy.feature as cfeature

from datetime import datetime, timedelta
from shapely.geometry import Point
from context import process_dir

##### User Input #####
date_base = datetime.today()
date = date_base.strftime("%Y-%m-%d")
d1 = (date_base + timedelta(days=1)).strftime("%Y-%m-%d")
print(date)

model_select = "hrdps"  # ["rdps", "hrdps"]

#%%
if str(model_select) == 'rdps':
    # load the rdps_vars.json file
    with open('rdps_vars.json', 'r') as f:
        model_vars = json.load(f)
elif str(model_select) == 'hrdps':
    # load the hrdps_vars.json file
    with open('hrdps_vars.json', 'r') as f:
        model_vars = json.load(f)
pred_vars = model_vars["predict_vars"]

#%%
# read the two required dataframes
bins = pd.read_csv("nationwide_bins.csv")
d0_data = pd.read_csv(f"./temp/{model_select}_d0_full.csv")
# d1_date = 

#%%
# requires variables/functions to loop and generate the pixel
# dry lightning probability

# first remove the No Ecozone column values
d0_data = d0_data[~d0_data["ecozone"].isin(["No Ecozone"])]

# get the unique ecozones
ecozones = list(d0_data["ecozone"].unique())
print(ecozones)

all_text_fcst = ["low", "moderate", "considerable"]
all_fcst_class = [1, 2, 3]
def fcst_bins(df, prob):
    # takes the nationwide bins limits dataframes
    lower_limit = df["low-mod"].values[0]
    upper_limit = df["mod-con"].values[0]

    if prob <= lower_limit:
        text_fcst = "low"
        fcst_class = 1
    elif lower_limit < prob <= upper_limit:
        text_fcst = "moderate"
        fcst_class = 2
    else: 
        text_fcst = "considerable"
        fcst_class = 3

    return text_fcst, fcst_class 

def find_files(directory, substring):
    """
    Search for files in the given directory whose names contain the substring.
    Returns a list of matching file paths.
    """
    if not os.path.isdir(directory):
        raise ValueError(f"Directory '{directory}' does not exist or is not accessible.")

    matches = []
    substring_lower = substring.lower()

    try:
        for entry in os.listdir(directory):
            full_path = os.path.join(directory, entry)
            if os.path.isfile(full_path) and substring_lower in entry.lower():
                matches.append(full_path)
    except PermissionError:
        print(f"Permission denied while accessing '{directory}'.")
    except OSError as e:
        print(f"Error reading directory '{directory}': {e}")

    return matches

#%%
# --------------------------------------------------
# Collect rows here (instead of appending to gdf)
# --------------------------------------------------
records = []

#ecozones = ecozones[0:3]  #TEST
for zone in ecozones:
    print(zone)

    # ----------------------------------------------
    # Load model ONCE per ecozone
    # ----------------------------------------------
    file_zone = zone.replace(" ", "_")
    file_pred_model = find_files(
        f"{process_dir}FINAL_MODELS",
        file_zone
    )

    lda_model = joblib.load(file_pred_model[0])    
    rf_model = joblib.load(file_pred_model[1])

    # ----------------------------------------------
    # Subset data 
    # ----------------------------------------------
    d0_zone = d0_data[d0_data["ecozone"] == zone].copy()

    # ----------------------------------------------
    # STEP 1: Batched model prediction 
    # ----------------------------------------------
    X = d0_zone[pred_vars].to_numpy()

    fitted = lda_model.transform(X)
    probs = rf_model.predict_proba(fitted)
    
    # for now just grab the last probability (for dry lightning)
    probs = probs[:, -1]

    # ----------------------------------------------
    # STEP 3: Vectorized geometry creation
    # ----------------------------------------------
    geometries = gpd.GeoSeries(
        gpd.points_from_xy(d0_zone["lon"], d0_zone["lat"]),
        index=d0_zone.index,
        crs="EPSG:4326"
    )

    # ----------------------------------------------
    # STEP 2 & 4: Build rows in Python list
    # ----------------------------------------------
    for i, (idx, row) in enumerate(d0_zone.iterrows()):
        prob = probs[i]
        geom = geometries.loc[idx]

        # Forecast classification row
        text_fcst, fcst_class = fcst_bins(bins, prob)

        records.append({
            "id": idx,
            "name": f"{zone}_fcst",
            "latitude": row["lat"],
            "longitude": row["lon"],
            "probability": prob,
            "text": text_fcst,
            "class": fcst_class,
            "geometry": geom
        })

# --------------------------------------------------
# STEP 4: Create the GeoDataFrame 
# --------------------------------------------------
gdf = gpd.GeoDataFrame(
    records,
    geometry="geometry",
    crs="EPSG:4326"
)

gdf.to_file(f"./RESOURCES/d0_{date}_lightning_forecast.gpkg", driver="GPKG")

# %%
print(gdf)

# standardized colors
CLASS_MAP = {
    1: "Low",
    2: "Moderate",
    3: "Considerable"
}

CLASS_COLORS = {
    1: "#a4a6a8",   # Low
    2: "#f3f348",   # Moderate
    3: "#d6820b"    # Considerable
}

gdf = gdf[
    gdf.geometry.notna() &
    (~gdf.geometry.is_empty)
].copy()

# NRCan Projection information
plot_projection = ccrs.PlateCarree()  # 3978
target_crs = "EPSG:3978"
gdf_proj = gdf.to_crs(target_crs)

gdf_proj = gdf_proj[
    gdf_proj.geometry.notna() &
    (~gdf_proj.geometry.is_empty)
].copy()

if gdf_proj.empty:
    raise ValueError("gdf_proj is empty — no valid geometries to rasterize")

#%%
# ----------
# BEGIN MAPPING
# ----------
import rasterio
from rasterio.features import rasterize
from rasterio.transform import from_origin
from shapely.validation import make_valid

# -------------------------------------
# Raster grid definition (keep base projection: EPSG:4326)
# -------------------------------------
# Ensure CRS is defined
if gdf.crs is None:
    gdf = gdf.set_crs("EPSG:4326")

# Make geometries valid
gdf["geometry"] = gdf.geometry.apply(
    lambda g: make_valid(g) if g is not None else None
)

# Drop invalid / empty / non-finite points
gdf = gdf[
    gdf.geometry.notna() &
    (~gdf.geometry.is_empty) &
    np.isfinite(gdf.geometry.x) &
    np.isfinite(gdf.geometry.y) &
    np.isfinite(gdf["probability"])
].copy()

# Enforce class column cleanliness (optional but recommended)
gdf = gdf[
    gdf["class"].notna() &
    np.isfinite(gdf["class"])
].copy()

gdf["class"] = gdf["class"].astype("uint8")

target_crs = "EPSG:4326"
gdf_proj = gdf  # No reprojection to keep base projection

# Drop any points that failed reprojection (though none since no reprojection)
gdf_proj = gdf_proj[
    np.isfinite(gdf_proj.geometry.x) &
    np.isfinite(gdf_proj.geometry.y)
].copy()

if gdf_proj.empty:
    raise ValueError("No valid points remain after filtering")

# Manual bounds from finite geometry bounds
bounds = gdf_proj.geometry.bounds
bounds = bounds.replace([np.inf, -np.inf], np.nan).dropna()

if bounds.empty:
    raise ValueError("No finite geometry bounds available")

xmin = bounds.minx.min()
ymin = bounds.miny.min()
xmax = bounds.maxx.max()
ymax = bounds.maxy.max()

from rasterio.transform import from_origin

resolution = 0.09  # Approximately 10 km in degrees (since EPSG:4326 is geographic)

width  = int(np.ceil((xmax - xmin) / resolution))
height = int(np.ceil((ymax - ymin) / resolution))

transform = from_origin(xmin, ymax, resolution, resolution)

prob_shapes = (
    (geom, float(val))
    for geom, val in zip(
        gdf_proj.geometry,
        gdf_proj["probability"]
    )
)

prob_raster = rasterize(
    prob_shapes,
    out_shape=(height, width),
    transform=transform,
    fill=np.nan,
    dtype="float32"
)

class_shapes = (
    (geom, cls)
    for geom, cls in zip(
        gdf_proj.geometry,
        gdf_proj["class"]
    )
)

class_raster = rasterize(
    class_shapes,
    out_shape=(height, width),
    transform=transform,
    fill=0,
    dtype="uint8"
)

output_tif = f"./RESOURCES/d0_{date}_lightning_forecast.tif"
today_tif = f"./RESOURCES/d0.tif"

with rasterio.open(
    output_tif,
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=2,
    crs=target_crs,
    transform=transform,
    dtype="float32",
    nodata=np.nan,
    compress="lzw"
) as dst:

    dst.write(prob_raster, 1)
    dst.write(class_raster.astype("float32"), 2)

    dst.set_band_description(1, "Dry Lightning Probability")
    dst.set_band_description(2, "Forecast Class")

    dst.update_tags(
        CLASS_1="Low",
        CLASS_2="Moderate",
        CLASS_3="Considerable",
        CRS="EPSG:4326"
    )

with rasterio.open(
    today_tif,
    "w",
    driver="GTiff",
    height=height,
    width=width,
    count=2,
    crs=target_crs,
    transform=transform,
    dtype="float32",
    nodata=np.nan,
    compress="lzw"
) as dst:

    dst.write(prob_raster, 1)
    dst.write(class_raster.astype("float32"), 2)

    dst.set_band_description(1, "Dry Lightning Probability")
    dst.set_band_description(2, "Forecast Class")

    dst.update_tags(
        CLASS_1="Low",
        CLASS_2="Moderate",
        CLASS_3="Considerable",
        CRS="EPSG:4326"
    )

#%%
# ----------
# STATIC MAP
# -----------
fig = plt.figure(figsize=(12, 12))
ax = plt.axes(projection=plot_projection)

xmin, ymin, xmax, ymax = gdf_proj.total_bounds

ax.set_extent(
    #[xmin, xmax, ymin, ymax],
    [-142, -52, 41, 71],   # lon_min, lon_max, lat_min, lat_max
    crs=ccrs.PlateCarree()
)

# --------------------------------------
# Base map
# --------------------------------------
ax.add_feature(cfeature.LAND.with_scale("50m"), facecolor="#f7f7f7")
ax.add_feature(cfeature.OCEAN.with_scale("50m"), facecolor="#e6f2ff")
ax.add_feature(cfeature.COASTLINE.with_scale("50m"), linewidth=0.8)
ax.add_feature(cfeature.BORDERS.with_scale("50m"), linewidth=0.6)
ax.add_feature(cfeature.LAKES.with_scale("50m"), facecolor="#e6f2ff", edgecolor="black", linewidth=0.3)
ax.add_feature(cfeature.RIVERS.with_scale("50m"), linewidth=0.3, alpha=0.6)

ax.add_feature(
    cfeature.NaturalEarthFeature(
        category="cultural",
        name="admin_1_states_provinces_lines",
        scale="50m",
        facecolor="none"
    ),
    edgecolor="black",
    linewidth=1
)

# --------------------------------------
# Plot forecast points
# --------------------------------------

gdf_fcst = gdf[gdf["class"].notna()]

for cls, label in CLASS_MAP.items():
    subset = gdf_fcst[gdf_fcst["class"] == cls]

    ax.scatter(
        subset.longitude,
        subset.latitude,
        s=6,
        c=CLASS_COLORS[cls],
        transform=plot_projection, 
        label=label,
        alpha=0.85,
        linewidths=0
    )

# scale map around the data
#ax.autoscale_view()

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
# Legend
# --------------------------------------
legend_handles = [
    mpatches.Patch(color=CLASS_COLORS[1], label="Low"),
    mpatches.Patch(color=CLASS_COLORS[2], label="Moderate"),
    mpatches.Patch(color=CLASS_COLORS[3], label="Considerable")
]

ax.legend(
    handles=legend_handles,
    title="Dry Lightning Probability",
    loc="lower left",
    frameon=True,
    framealpha=0.95
)

# --------------------------------------
# Titles & attribution
# --------------------------------------
plt.title(
    "D0: Dry Lightning Forecast\n"
    f"Valid: 12 UTC {date} to 12 UTC {d1}",
    fontsize=16,
    weight="bold",
    loc="left"
)

plt.text(
    0.99, 0.99,
    f"Model: {model_select.upper()} | Point-based classification\n"
    "Weighted 50th and 80th percentile",
    transform=ax.transAxes,
    ha="right",
    va="top",
    fontsize=9,
    alpha=0.7
)

plt.savefig(
    f"./MAPS/d0_{date}_lightning_forecast_points.png",
    dpi=300,
    bbox_inches="tight"
)

plt.savefig(
    f"./MAPS/d0.png",
    dpi=300,
    bbox_inches="tight"
)
plt.close()

# %%
