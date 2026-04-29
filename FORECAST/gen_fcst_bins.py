"""

    Generate the forecast bins for breakpoint
    weighted mean of dry lightning strikes 

    Liam.Buchart@nrcan-rncan.gc.ca
    March 17, 2026

"""
#%%
import numpy as np
import pandas as pd
import json

from context import utils_dir, process_dir

#%%
# grab the csv file sitting in the ../PROCESS/FINAL_MODELS.
data_dir = "../PROCESS/FINAL_MODELS"
pred_df = pd.read_csv(f"{data_dir}/pred_terciles.csv")

# %%
# loop through each ecozone and get the 
# number of dry strikes
def zone_station_id(zone, json):
    # resturns all unique station ids for a given zone
    ids = set()
    for record in json[zone]:
        try:
            ids.add(record["id"])
        except KeyError:
            print("Missing 'id' key in record:", record)

    return list(ids)

# grab the rows from the df and get tercile information
# open the stations json file
with open(utils_dir + '/ecozone_stations.json', 'r') as f:
    all_zones_info = json.load(f)
all_zones = list( all_zones_info.keys() )
print(all_zones)

#%%
bin_df = pd.DataFrame(columns=["ecozone", 
                               "dry_lightning_days"])
# get a wrighted mean of the lower and upper terciles
# weighted number of dry strike days
for zone in all_zones:
    dataset = pd.DataFrame()
    zone_ids = zone_station_id(zone, all_zones_info)
    print("Ids in the zone are: ", zone_ids)

    # get daily information
    for id in zone_ids:
        id_dataset = pd.read_csv(f"{process_dir}CLEANED/{id}_combined_lightning_prediction_cleaned.csv")
        # combine the datasets
        dataset = pd.concat([dataset, id_dataset], ignore_index=True)
        #print(dataset.shape)

    y = dataset["classifier"]
    count_of_2 = list(y).count(2)  # two is the dry lightning counter

    # append the ecozone and count to bin_df
    zone = zone.replace(" ", "_")
    bin_df.loc[len(bin_df)] = [zone, count_of_2]

# %%
print(bin_df)
print(pred_df)

# %%
for zone in list(pred_df["eco_zone"].unique()):
    print("Processing ", zone)
    edges = pred_df[pred_df["eco_zone"] == zone]
    #print(edges["dry_lightning_terciles"])
    lbin = min(edges["dry_lightning_terciles"])
    hbin = max(edges["dry_lightning_terciles"])
    idx = bin_df.index[bin_df["ecozone"] == zone]

    bin_df.loc[idx, "low"] = lbin
    bin_df.loc[idx, "moderate"] = hbin

# %%
print(bin_df)

# %%
def weighted_average(dataframe, value, weight):
    val = dataframe[value]
    wt = dataframe[weight]
    return (val * wt).sum() / wt.sum()

# %%
lower = weighted_average(bin_df, 
                         "low", 
                         "dry_lightning_days")
upper = weighted_average(bin_df,
                         "moderate",
                         "dry_lightning_days")
print(round(lower, 3))
print(round(upper, 3))

#%%
# add these to a small dataframe
nationwide = pd.DataFrame(columns=["low-mod", "mod-con"])
nationwide.loc[0, "low-mod"] = round(lower, 3)
nationwide.loc[0, "mod-con"] = round(upper, 3)

print(nationwide)

# %%
# save the dataframes
bin_df.to_csv("all_ecozone_bins.csv")
nationwide.to_csv("nationwide_bins.csv")
# %%
