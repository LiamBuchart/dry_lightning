import glob
import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px


# -----------------
# Configuration
# -----------------
BASE_DIR = Path(__file__).parent
ARCHIVE_DIR = BASE_DIR / "archive"
PLOTS_DIR = BASE_DIR / "plots"
PLOTS_DIR.mkdir(exist_ok=True)

STATS_COLUMNS = ["POD", "FAR", "CSI", "BIAS", "HSS"]
RECENT_DAYS = 7
HISTORY_DAYS = 90


# -----------------
# Loading utilities
# -----------------
def load_all_validation_stats():
    """Load all d0 and d1 validation CSV files into a single DataFrame."""
    files = sorted(ARCHIVE_DIR.glob("d*_validation_stats_*.csv"))
    if not files:
        raise FileNotFoundError("No validation stats CSV files found.")

    frames = []
    for path in files:
        df = pd.read_csv(path, parse_dates=["rep_date"])
        df["type"] = "d0" if path.name.startswith("d0_") else "d1"
        frames.append(df)

    stats = pd.concat(frames, ignore_index=True)
    return stats.sort_values("rep_date")


def melt_stats(df):
    """Convert wide-format stats into long format for plotting."""
    return df.melt(
        id_vars=["rep_date", "type"],
        value_vars=STATS_COLUMNS,
        var_name="metric",
        value_name="value",
    )


# -----------------
# Plotting
# -----------------
def plot_time_window(stats_long, days, filename, title):
    """Plot stats over the last N days."""
    latest_date = stats_long["rep_date"].max()
    cutoff = latest_date - pd.Timedelta(days=days - 1)

    subset = stats_long[stats_long["rep_date"] >= cutoff]

    fig = px.line(
        subset,
        x="rep_date",
        y="value",
        color="type",
        facet_row="metric",
        markers=True,
        title=title,
        labels={
            "rep_date": "Date",
            "value": "Score",
            "type": "Dataset",
            "metric": "Metric",
        },
    )

    fig.update_layout(
        template="plotly_white",
        hovermode="x unified",
        margin=dict(l=60, r=20, t=60, b=40),
        legend_title_text="Dataset",
    )
    fig.update_xaxes(tickformat="%Y-%m-%d")

    fig.write_image(PLOTS_DIR / filename)


# -----------------
# Statistics
# -----------------
def compute_mean_stats(stats):
    """Compute mean validation statistics for d0 and d1 separately."""
    output = {}

    for dataset in ["d0", "d1"]:
        subset = stats[stats["type"] == dataset]
        output[dataset] = {
            "count": int(len(subset)),
            "first_date": subset["rep_date"].min().strftime("%Y-%m-%d"),
            "last_date": subset["rep_date"].max().strftime("%Y-%m-%d"),
            "mean_stats": {
                col: float(subset[col].mean()) for col in STATS_COLUMNS
            },
        }

    return output


def save_mean_stats(mean_stats, filename="validation_mean_stats.json"):
    out_path = PLOTS_DIR / filename
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(mean_stats, f, indent=2)
    return out_path


# -----------------
# Main workflow
# -----------------
def main():
    stats = load_all_validation_stats()
    stats_long = melt_stats(stats)

    plot_time_window(
        stats_long,
        RECENT_DAYS,
        "validation_last_week.png",
        f"Validation statistics – last {RECENT_DAYS} days",
    )

    plot_time_window(
        stats_long,
        HISTORY_DAYS,
        "validation_last_90_days.png",
        f"Validation statistics – last {HISTORY_DAYS} days",
    )

    mean_stats = compute_mean_stats(stats)
    json_path = save_mean_stats(mean_stats)

    print(f"Saved plots to: {PLOTS_DIR}")
    print(f"Saved mean statistics to: {json_path}")


if __name__ == "__main__":
    main()