"""

    Similar to categorical_plot_validate but instead opens categorical_d*_verification_table_*.csv
    Produces a historgram comparing the observed and forecasted distribution for the last 14 days and for the full season (200 days)

    Liam.Buchart@NRCan-RNCan.gc.ca
    June 5, 2026

"""
#%%
import json
from pathlib import Path
from datetime import datetime, timedelta

import pandas as pd
import matplotlib.pyplot as plt

#%%
BASE_DIR = Path(__file__).parent
ARCHIVE_DIR = BASE_DIR / "categorical"
PLOTS_DIR = BASE_DIR / "plots"
PLOTS_DIR.mkdir(exist_ok=True)

STATS_COLUMNS = ["accuracy", "HSS", "HK"]
CAT_COLUMNS = ["no lightning", "moist lightning", "dry lightning"]

def load_all_validation_stats():
    """
    Load all validation CSV files and attach d0/d1 type from filename.
    """
    files = sorted(ARCHIVE_DIR.glob("categorical_d*_validation_stats_*.csv"))
    if not files:
        raise FileNotFoundError("No validation stats CSV files found.")

    dfs = []
    for f in files:
        df = pd.read_csv(f, parse_dates=["rep_date"])
        df["type"] = extract_type_from_filename(f)
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)

def melt_stats(df):
    """
    Convert wide-format stats into long format for plotting.
    """
    return df.melt(
        id_vars=["rep_date", "type"],
        value_vars=STATS_COLUMNS,
        var_name="metric",
        value_name="value",
    )

def extract_type_from_filename(filepath):
    """
    Extract lead time (d0 / d1) from filename.
    """
    name = filepath.name.lower()
    if name.startswith("categorical_d0"):
        return "d0"
    elif name.startswith("categorical_d1"):
        return "d1"
    else:
        raise ValueError(f"Cannot determine type from filename: {filepath.name}")

def list_all_validation_tables(n_days):
    """
    Return d0 and d1 verification table files from the last n_days.

    Parameters:
        n_days (int): number of days to look back from today, inclusive.

    Returns:
        dict: {'d0': [Path, ...], 'd1': [Path, ...]}
    """
    files = sorted(ARCHIVE_DIR.glob("categorical_d*_verification_table_*.csv"))
    if not files:
        raise FileNotFoundError("No validation stats CSV files found.")

    cutoff_date = (datetime.today().date() - timedelta(days=max(n_days - 1, 0)))

    recent_files = {"d0": [], "d1": []}
    for filepath in files:
        try:
            date_text = filepath.stem.split("_")[-1]
            file_date = datetime.strptime(date_text, "%Y-%m-%d").date()
        except ValueError:
            continue

        if file_date >= cutoff_date:
            data_type = extract_type_from_filename(filepath)
            recent_files[data_type].append(filepath)

    if not recent_files["d0"] and not recent_files["d1"]:
        raise FileNotFoundError(f"No validation files found in the last {n_days} days.")

    return recent_files

def sum_dataframes(df1: pd.DataFrame, df2: pd.DataFrame) -> pd.DataFrame:
    """
    Returns the element-wise sum of two DataFrames of the same shape.
    Missing values are treated as 0.
    """
    # Validate inputs
    if not isinstance(df1, pd.DataFrame) or not isinstance(df2, pd.DataFrame):
        raise TypeError("Both inputs must be pandas DataFrames.")
    
    if df1.shape != df2.shape:
        raise ValueError(f"DataFrames must have the same shape. Got {df1.shape} and {df2.shape}.")
    
    # Align indexes and columns just in case
    df1, df2 = df1.align(df2, join='outer', fill_value=0)
    
    # Perform element-wise sum, treating NaN as 0
    return df1.add(df2, fill_value=0)

def combine_dataframes(file_dict, fcst):
    # sum the dataframes together to get a total count in each cell
    all_files = file_dict[fcst]

    fdf = pd.read_csv(all_files[0])
    cols = fdf.columns.to_list()
    hist_df = pd.DataFrame(columns=CAT_COLUMNS, 
                           index=["low", "moderate", "considerable"])
    # fill with zeros
    hist_df = hist_df.fillna(0)

    count = 0
    for file in all_files:
        fdf = pd.read_csv(file)
        fdf = fdf.set_index(cols[0])
        hist_df = sum_dataframes(hist_df, fdf)

    return hist_df

def create_distributions(df):
    # save an obs dateframe that is the column sums of the ver_df for each observed category
    count_df = pd.DataFrame(columns = ["obs_count", "forecast_count"])
    count_df["obs_count"] = df.sum(axis=0).to_list()
    count_df["forecast_count"] = df.sum(axis=1).to_list()

    return count_df

def plot_histogram(df1, df2, title_suffix, filename):
    # produce a histogram of the necessary data for forecast and observed
    # df1 is the forecast dataframe 
    # dataframes are d1, and d0 over same time period
    CLASS_COLORS = {
        1: "#2756D6",   # Observed
        2: "#e0d531",   # Forecast
    }
    # figures
    fig, (ax0, ax2) = plt.subplots(1, 2, figsize=(10, 10))
    ax1 = ax0.twinx()

    ax3 = ax2.twinx()
    width = 0.4
    x = df1.index

    # double bar chart for observed and forecast
    df1["obs_count"].plot(kind="bar", 
                          width=width, 
                          ax=ax0, position=0, 
                          color=CLASS_COLORS[1], label="Observed")
    df1["forecast_count"].plot(kind="bar", 
                               width=width, 
                               ax=ax0, position=1, 
                               color=CLASS_COLORS[2], label="Forecast")

    # add horizontal grid lines
    ax1.grid(axis="y", linestyle="--", alpha=0.7)

    # add legends and labels
    ax0.set_xlabel("Forecast Categories", fontsize=14)
    ax0.set_ylabel("Count", fontsize=14)
    ax0.set_title(f"D0 Distribution: {title_suffix}", fontsize=16)
    ax0.legend(loc="upper right", fontsize=15)

    # second historgram
    df2["obs_count"].plot(kind="bar", 
                          width=width, ax=ax2, 
                          position=0, 
                          color=CLASS_COLORS[1], 
                          label="Observed")
    df2["forecast_count"].plot(kind="bar", 
                          width=width, 
                          ax=ax2, position=1, 
                          color=CLASS_COLORS[2], 
                          label="Forecast")

    # add horizontal grid lines
    ax3.grid(axis="y", linestyle="--", alpha=0.7)

    # add legends and labels
    ax2.set_xlabel("Forecast Categories", fontsize=14)
    # label opposite y axis as frquency
    ax3.set_ylabel("Frequency", fontsize=14)
    ax2.set_title(f"D1 Distribution: {title_suffix}", fontsize=16)

    out_path = PLOTS_DIR / filename
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

def compute_mean_stats(stats):
    """
    Compute mean validation statistics for d0 and d1.
    """
    return (
        stats
        .groupby("type")[STATS_COLUMNS]
        .mean()
        .round(2)
        .to_dict(orient="index")
    )

def save_mean_stats(mean_stats, filename="cat_validation_mean_stats.json"):
    out_path = PLOTS_DIR / filename
    # save as .csv without headers 
    df = pd.DataFrame(mean_stats).T.reset_index().rename(columns={"index": "type"})
    df.to_csv(out_path.with_suffix(".csv"), index=False, header=False)

#%%
## main
def main():
    stats = load_all_validation_stats()
    stats_long = melt_stats(stats)

    files_season = list_all_validation_tables(200)
    print(files_season)

    d0_dff = combine_dataframes(files_season, "d0")
    d1_dff = combine_dataframes(files_season, "d1")

    d0 = create_distributions(d0_dff)
    d1 = create_distributions(d1_dff)

    plot_histogram(d0, d1, "Full Season", "full_season_distribution")

    # Mean stats
    save_mean_stats(compute_mean_stats(stats))


if __name__ == "__main__":
    main()

# %%
