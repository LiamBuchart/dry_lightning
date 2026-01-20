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

#%%
##### USER INPUT #####
station_select = "Stony Plain"
##### END USER INPUT #####

# open the stations json file
with open('./stations.json', 'r') as f:
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
dataset = pd.read_csv(f"./PROCESSED/{id}_combined_lightning_prediction_cleaned.csv")
print(dataset.head())

# print all column names
print(dataset.columns)

#%%
# see how many rows have 0 mucape
num_zero_mucape = len(dataset[dataset['mucape'] == 0 ])
num_zero_mucape_lightning = len(dataset[dataset["no_lightning"] == 0])
total_rows = len(dataset)
print(f"Number of rows with mucape = 0: {num_zero_mucape}")
print(f"Days with lightning: {num_zero_mucape_lightning}")
print(f"Out of {total_rows} total rows")

# only that have non-zero mucape
#dataset = dataset[dataset['mucape'] != 0]

# %%
# grab training variables and classifiers for plotting
# prediction columns
#cols_predict = ["dTTd850_zscore", "dTTd700_zscore", "dT850-500_zscore",
#                "K_index_zscore", "lcl_zscore", "pw_zscore", 
#                "mucape_log"]
cols_predict = ["dTTd850", "dTTd700", "dT850-500", "mucape_log", 
                "lcl", "pw", "below_cloud_rh", "K_index_zscore"] #, "lifted_index"]
#cols_predict = ["mucape_log", "dTTd850_zscore", "lcl_zscore", "pw_zscore"]
plot_set = dataset[cols_predict + ["classifier"]]

# remove nans
plot_set = plot_set.dropna()

y = plot_set["classifier"].values 
X = plot_set[cols_predict].values

# Encode the target variable
le = LabelEncoder()
y = le.fit_transform(y)

#%%
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
plt.figure(figsize=(12, 10))
for i, feature in enumerate(cols_predict):
    plt.subplot(4, 2, i + 1)
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
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# %%
# Apply Linear Discriminant Analysis
lda = LinearDiscriminantAnalysis(n_components=2)
X_train = lda.fit_transform(X_train, y_train)
X_test = lda.transform(X_test)

# %%
tmp_Df = pd.DataFrame(X_train, columns=['LDA Component 1', 'LDA Component 2'])
tmp_Df['Class']=y_train

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

# %%
# to do - create an artificial 2025 sounding launch data
# look at probabilities for that data
sample_data = pd.DataFrame(columns=cols_predict)
print(cols_predict)
print(dataset[cols_predict].head())

sample_inputs = [9, 7, 28, 90, 840, 14, 0.62, -0.5]

# Add sample_inputs as a row to sample_data
sample_data = pd.concat([sample_data, pd.DataFrame([sample_inputs], columns=cols_predict)], ignore_index=True)
print(sample_data)

# %%
# do a predict_proba on the sample data and plot
sample_data = lda.transform(sample_data)
sample_prob = rf_with_lda.predict_proba(sample_data)
print(sample_prob)

#%%
# Create a nice plot of sample probabilities with proper class labels
class_labels = ["No Lightning", "Moist Lightning", "Dry Lightning"]
sample_indices = np.arange(sample_prob.shape[0])

fig, ax = plt.subplots(figsize=(10, 6))
x_pos = np.arange(len(class_labels))
width = 0.25

for i, (idx, probs) in enumerate(zip(sample_indices, sample_prob)):
    offset = (i - len(sample_prob) / 2) * width
    bars = ax.bar(x_pos + offset, probs, width, label=f'Sample {idx+1}', alpha=0.8)

ax.set_xlabel('Lightning Class', fontsize=12, fontweight='bold')
ax.set_ylabel('Predicted Probability', fontsize=12, fontweight='bold')
ax.set_title('Random Forest Predicted Probabilities for Sample Data', fontsize=14, fontweight='bold')
ax.set_xticks(x_pos)
ax.set_xticklabels(class_labels)
ax.set_ylim(0, 1)
ax.legend(loc='upper right')
ax.grid(axis='y', alpha=0.3)
plt.tight_layout()
plt.show()

# %%
