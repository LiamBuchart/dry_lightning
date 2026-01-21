"""

    Carry out LDA and Random Forest classification on the 
    combined and cleaned lightning prediction dataset.
    
    Input File: *stationid*_combined_lightning_prediction_cleaned.csv
    Output: LDA plots, Random Forest accuracy and confusion matrix

    Liam.Buchart@nrcan-rncan.gc.ca
    December 29, 2025

"""
#%%
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import json

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from context import utils_dir

#%%
##### USER INPUT #####
station_select = "Vernon"
##### END USER INPUT #####

# open the stations json file
with open(utils_dir + '/stations.json', 'r') as f:
    stations = json.load(f)
all_stations = stations.keys()

if station_select in all_stations:
    print(f"{station_select} is a valid station...")
    station_info = stations[station_select]
    id = station_info["id"]
    station = station_info["sounding_id"]
else: 
    print("please ensure stations matches one from the 'all_stations' variable...")

#%%
dataset = pd.read_csv(f"./{id}_combined_lightning_prediction_cleaned.csv")
print(dataset.head())

# print all column names
print(dataset.columns)

# %%
y = dataset["classifier"].values

# prediction columns
#cols_predict = ["dTTd850_zscore", "dTTd700_zscore", "dT850-500_zscore",
#                "K_index_zscore", "lcl_zscore", "pw_zscore", 
#                "mucape_log"]
cols_predict = ["K_index_zscore", "mucape_log", "dTTd700_zscore"] 
X = dataset[cols_predict].values

# Encode the target variable
le = LabelEncoder()
y = le.fit_transform(y)

#%%
# grab training variables and classifiers for plotting
plot_set = dataset[cols_predict + ["classifier"]]

# pair plot of the features colored by classifier
ax = sns.pairplot(plot_set, hue='classifier')
plt.suptitle("Pair Plot of Dry Lightning Dataset")
sns.move_legend(
    ax, "lower center",
    bbox_to_anchor=(.5, 1), ncol=3, title=None, frameon=False)
plt.tight_layout()
plt.show()

# %%
