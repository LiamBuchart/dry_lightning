import json
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt

# -------------------------------------------------
# Configuration
# -------------------------------------------------

BASE_DIR = Path(__file__).parent
ARCHIVE_DIR = BASE_DIR / "archive"
PLOTS_DIR = BASE_DIR / "plots"
PLOTS_DIR.mkdir(exist_ok=True)

STATS_COLUMNS = ["POD", "FAR", "CSI", "BIAS", "HSS"]

# -------------------------------------------------
# Loading utilities
# -------------------------------------------------

def extract_type_from_filename(filepath):
    """
    Extract lead time (d0 / d1) from filename.
    """
    name = filepath.name.lower()
    if name.startswith("d0"):
        return "d0"
    elif name.startswith("d1"):
        return "d1"
    else:
        raise ValueError(f"Cannot determine type from filename: {filepath.name}")

def load_all_validation_stats():
    """
    Load all validation CSV files and attach d0/d1 type from filename.
    """
    files = sorted(ARCHIVE_DIR.glob("d*_validation_stats_*.csv"))
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

def filter_last_n_days(df, n_days):
    """
    Return subset of data from the last n_days based on rep_date.
    """
    max_date = df["rep_date"].max()
    start_date = max_date - pd.Timedelta(days=n_days)
    return df[df["rep_date"] >= start_date]

# -------------------------------------------------
# Plotting: single metric
# -------------------------------------------------

def plot_metrics(stats_long):
    """
    Produce single-panel PNGs for each metric over the full period.
    """
    for metric in STATS_COLUMNS:
        fig, ax = plt.subplots(figsize=(10, 5))
        subset = stats_long[stats_long["metric"] == metric]

        for vtype, g in subset.groupby("type"):
            ax.plot(
                g["rep_date"],
                g["value"],
                marker="o",
                linewidth=1.5,
                label=vtype,
                color="k" if vtype == "d0" else "red",
            )

        ax.set_title(f"Recent {metric}", fontsize=16)
        ax.set_xlabel("Date", fontsize=14)
        ax.set_ylabel(metric, fontsize=14)
        ax.legend(fontsize=12)
        ax.grid(True)

        fig.autofmt_xdate()

        out_file = PLOTS_DIR / f"{metric.lower()}_timeseries.png"
        plt.savefig(out_file, dpi=150, bbox_inches="tight")
        plt.close(fig)

# -------------------------------------------------
# Plotting: multi-panel
# -------------------------------------------------

def plot_multipanel(stats_long, title_suffix, filename):
    """
    Create a stacked multi-panel plot with one subplot per metric.
    """
    fig, axes = plt.subplots(
        nrows=len(STATS_COLUMNS),
        ncols=1,
        figsize=(12, 2.8 * len(STATS_COLUMNS)),
        sharex=True,
    )

    for ax, metric in zip(axes, STATS_COLUMNS):
        subset = stats_long[stats_long["metric"] == metric]

        for vtype, g in subset.groupby("type"):
            ax.plot(
                g["rep_date"],
                g["value"],
                marker="o",
                linewidth=2,
                label=vtype,
                color="k" if vtype == "d0" else "green",
            )

        ax.set_ylabel(metric, fontsize=14)
        #ax.grid(True)

        if ax is axes[0]:
            ax.legend(fontsize=15)

    axes[-1].set_xlabel("Date", fontsize=14)
    fig.suptitle(f"Validation Metrics {title_suffix}", fontsize=18)

    fig.autofmt_xdate()
    plt.tight_layout(rect=[0, 0, 1, 0.97])

    out_path = PLOTS_DIR / filename
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

# -------------------------------------------------
# Statistics
# -------------------------------------------------

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

def save_mean_stats(mean_stats, filename="validation_mean_stats.json"):
    out_path = PLOTS_DIR / filename
    # save as .csv without headers 
    df = pd.DataFrame(mean_stats).T.reset_index().rename(columns={"index": "type"})
    df.to_csv(out_path.with_suffix(".csv"), index=False, header=False)
    #with open(out_path, "w", encoding="utf-8") as f:
    #    json.dump(mean_stats, f, indent=2)

# -------------------------------------------------
# Main
# -------------------------------------------------

def main():
    stats = load_all_validation_stats()
    stats_long = melt_stats(stats)

    # Full-period single-metric plots
    plot_metrics(stats_long)

    # Multi-panel plots for recent windows
    for label, ndays in {"last_90_days": 90, "last_14_days": 14}.items():
        subset = filter_last_n_days(stats, ndays)
        subset_long = melt_stats(subset)

        plot_multipanel(
            subset_long,
            title_suffix=f"(Last {ndays} days)",
            filename=f"validation_multipanel_{label}.png",
        )

    # Mean stats
    save_mean_stats(compute_mean_stats(stats))

if __name__ == "__main__":
    main()