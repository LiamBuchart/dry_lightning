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
import joblib
from pathlib import Path

from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from sklearn.discriminant_analysis import LinearDiscriminantAnalysis
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, confusion_matrix
from context import utils_dir

#%%
##### USER INPUT #####
zone_select = "Taiga Shield East"
save_dir = "./FINAL_MODELS/"
##### END USER INPUT #####

# open the stations json file
with open(utils_dir + '/ecozone_stations.json', 'r') as f:
    all_zones_info = json.load(f)
all_zones = all_zones_info.keys()
print(all_zones)

if zone_select in all_zones:
    print(f"{zone_select} is a valid ecozone...")
    zone_info = all_zones_info[zone_select]
else: 
    print("please ensure zones matches one from the 'all_zones' variable...")

def zone_station_id(zone, json):
    # resturns all unique station ids for a given zone
    ids = set()
    for record in json[zone]:
        try:
            ids.add(record["id"])
        except KeyError:
            print("Missing 'id' key in record:", record)

    return list(ids)
    
#%%
zone_ids = zone_station_id(zone_select, all_zones_info)
print("Ids in the zone are: ", zone_ids)

#%%
# loop through each id, read the corresponding csv file and concatenate
dataset = pd.DataFrame()
for id in zone_ids:
    id_dataset = pd.read_csv(f"./CLEANED/{id}_combined_lightning_prediction_cleaned.csv")
    # combine the datasets
    dataset = pd.concat([dataset, id_dataset], ignore_index=True)
    print(dataset.shape)

# print all column names
#print(dataset.head())
#print(dataset.columns)

print("Lightning Days with full data...")
print(dataset[dataset['dry_lightning'] == 1].shape)
print(dataset[dataset['moist_lightning'] == 1].shape)

# %%
# prediction columns
#cols_predict = ["K_index_zscore", "mucape_log", "dTTd700_zscore"] 
#cols_predict = ["dTTd850", "dTTd700", "dT850-500", "K_index"]
cols_predict = ["dTTd850", "dTTd700", "dT850-500", "cape",
                "total_totals", "sweat", "lcl", 
                "K_index", "lifted_index"] # "T1000",
X = dataset[cols_predict + ["classifier"]].dropna()
y = X["classifier"]

# just need to ensure that things are the same size
X = X.drop(columns=["classifier"])
X = X.values

# Encode the target variable
le = LabelEncoder()
y = le.fit_transform(y)

print(y)

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
# Visualize the distribution of each feature using histograms.
# note this can be very slow
plt.figure(figsize=(12, 10))
for i, feature in enumerate(cols_predict):
    plt.subplot(5, 2, i + 1)
    sns.histplot(data=plot_set, x=feature, hue='classifier', kde=True)
    plt.title(f'{feature} Distribution')

plt.tight_layout()
plt.show()

# %%
correlation_matrix = plot_set.corr(numeric_only = True)
plt.figure(figsize=(8, 6))
# ensure the range on the colorbar is from -1 to 1 using seaborn
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', linewidths=0.5, 
            vmin=-1, vmax=1)
plt.title("Correlation Heatmap")
plt.show()

# %%
# Split the data set into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, stratify=y, random_state=42)

#%%
print(np.shape(X_test))

# %%
# Apply Linear Discriminant Analysis
lda = LinearDiscriminantAnalysis(n_components=2)
X_train = lda.fit_transform(X_train, y_train)
X_test = lda.transform(X_test)
print(np.shape(X_test))

# save the lda model 
joblib.dump(lda, 
            f"{save_dir}{zone_select.replace(" ", "_")}_lda_trained.joblib", 
            compress=3)

# %%
tmp_Df = pd.DataFrame(X_train, columns=['LDA Component 1', 'LDA Component 2'])
tmp_Df['Class'] = y_train

sns.FacetGrid(tmp_Df, hue ="Class",
              height = 6).map(plt.scatter,
                              'LDA Component 1',
                              'LDA Component 2')
plt.legend(loc='upper right')

# %%
# apply a random forest classifier to the data
rf_with_lda = RandomForestClassifier(max_depth=5, random_state=42)
rf_with_lda.fit(X_train, y_train)
y_pred = rf_with_lda.predict(X_test)

# also get probabilities
y_prob = rf_with_lda.predict_proba(X_test)

#%%
#Assume 'y_test' and 'y_pred' are already defined
accuracy = accuracy_score(y_test, y_pred)
conf_m = confusion_matrix(y_test, y_pred)

#Display the accuracy
print(f'Accuracy: {accuracy:.2f}')

#Display the confusion matrix as a heatmap
plt.figure(figsize=(6, 6))
sns.heatmap(conf_m, annot=True, fmt="d", cmap="Blues", cbar=False, square=True)
plt.xlabel("Predicted")
plt.ylabel("True")
plt.title("Confusion Matrix")
plt.show()

# save the rf model 
joblib.dump(rf_with_lda, 
            f"{save_dir}{zone_select.replace(" ", "_")}_rf_trained.joblib", 
            compress=3)

# %%
x_min, x_max = X_train[:,0].min() - 1, X_train[:,0].max() + 1
y_min, y_max = X_train[:,1].min() - 1, X_train[:,1].max() + 1
xx, yy = np.meshgrid(np.arange(x_min, x_max, 0.02),
                     np.arange(y_min, y_max, 0.02))

Z = rf_with_lda.predict(np.c_[xx.ravel(), yy.ravel()])
Z = Z.reshape(xx.shape)

from matplotlib.colors import ListedColormap
cmap_light = ListedColormap(['#FFAAAA', '#AAFFAA', '#AAAAFF'])

plt.figure(figsize=(7,5))
plt.contourf(xx, yy, Z, alpha=0.3, cmap=cmap_light)
plt.scatter(X_train[:,0], X_train[:,1], c=y_train, cmap='rainbow', edgecolors='b')
plt.xlabel('LDA Component 1')
plt.ylabel('LDA Component 2')
plt.legend()
plt.title('Random Forest Decision Boundary With LDA')
plt.show()

# %%
# y_prob: array shape (n_samples, n_classes)
probs = y_prob
print(np.shape(probs))
n_classes = probs.shape[1]
class_names = le.inverse_transform(np.arange(n_classes))

fig, axes = plt.subplots(n_classes+1, 1, sharex=True, figsize=(12, 2.5 * n_classes))
if n_classes == 1:
    axes = [axes]

x = np.arange(probs.shape[0])
for i, cname in enumerate(class_names):
    ax = axes[i]
    ax.plot(x, probs[:, i], marker='o', linestyle='-', alpha=0.8)
    ax.set_ylim(0.0, 1.0)
    ax.set_ylabel('Probability')
    ax.set_title(f'Predicted probability — class: {cname}')
    ax.grid(alpha=0.3)

# in the final plot just plot y-test
axes[-1].scatter(x, y_test, marker='o', linestyle='-', alpha=0.8)
axes[-1].set_ylabel('True Class')
# 0 - no lightning, 1 - moist lightning, 2 - dry lightning
axes[-1].set_yticks([0, 1, 2])

axes[-1].set_xlabel('Index')
# add lightning indices to the x-axis labels
#axes[-1].set_xticks(indices_lightning)
#axes[-1].set_xticklabels([f'{i}' for i in indices_lightning], rotation=45)

plt.tight_layout()
plt.show()

#%%
print(np.mean(y_prob[:, 1]), np.mean(y_prob[:, 2]))

# %%
# final bit is so save terciles for each prediction 
# class into a common dataframe
csv_path = Path("./FINAL_MODELS/pred_terciles.csv")
terciles = [65, 90]

new_row = {
    "eco_zone": f"{zone_select.replace(" ", "_")}",
    "no_lightning_terciles": [],
    "moist_lightning_terciles": [],
    "dry_lightning_terciles": []
    }

row = 0
for key in list(new_row.keys())[1:]:
    # y_prob is order in the same manner
    probs = y_prob[:, row]
    pred_terciles = []
    for terc in terciles:
        pred_terciles.append(np.round(np.percentile(probs, terc), 3))
    new_row[key] = pred_terciles
    print(key, new_row[key])

    row += 1

# %%
df_new = pd.DataFrame(new_row)
file_exists = csv_path.exists()

df_new.to_csv(
    csv_path,
    mode="a" if file_exists else "w",
    header=not file_exists,
    index=False
)

# %%
