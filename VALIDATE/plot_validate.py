"""

    Use output from validate_d0 and validate_d1 to create plots for my website
    Also calculate a running mean of the stats which will be displayed.

    We will have a plot for the most recent week, a plot for the running mean of stats,
    and finally a plot of the last 90 days of stats.

    Liam.Buchart@nrcan-rncan.gc.ca
    APril 17, 2026

"""

import glob
import json
import os

import pandas as pd
import plotly.express as px

ARCHIVE_DIR = os.path.join(os.path.dirname(__file__), "archive")
OUTPUT_DIR = os.path.join(ARCHIVE_DIR, "plots")
JSON_OUT = os.path.join(ARCHIVE_DIR, "validation_mean_stats.json")

STATS_COLUMNS = ["POD", "FAR", "CSI", "BIAS", "HSS"]
ROLLING_WINDOW = 7
RECENT_DAYS = 7
HISTORY_DAYS = 90


def load_validation_stats(archive_dir=ARCHIVE_DIR):
    pattern = os.path.join(archive_dir, "d*_validation_stats_*.csv")
    files = sorted(glob.glob(pattern))

    if not files:
        raise FileNotFoundError(f"No validation stats files found with pattern: {pattern}")

    rows = []
    for file_path in files:
        df = pd.read_csv(file_path, parse_dates=["rep_date"])
        df["type"] = "d0" if os.path.basename(file_path).startswith("d0_") else "d1"
        rows.append(df)

    stats = pd.concat(rows, ignore_index=True)
    stats = stats.dropna(subset=["rep_date"])
    stats = stats.sort_values("rep_date").reset_index(drop=True)

    return stats


def melt_stats(df):
    melted = df.melt(
        id_vars=["rep_date", "type"],
        value_vars=STATS_COLUMNS,
        var_name="metric",
        value_name="value",
    )
    return melted


def calculate_running_mean(stats, window=ROLLING_WINDOW):
    rolling = (
        stats.set_index("rep_date")[STATS_COLUMNS]
        .rolling(window=window, min_periods=1)
        .mean()
        .reset_index()
    )
    rolling["type"] = "rolling_mean"
    return rolling


def save_overall_mean_stats(stats, out_path=JSON_OUT):
    mean_values = {col: float(stats[col].mean()) for col in STATS_COLUMNS}
    summary = {
        "first_date": stats["rep_date"].min().strftime("%Y-%m-%d"),
        "last_date": stats["rep_date"].max().strftime("%Y-%m-%d"),
        "count": int(len(stats)),
        "mean_stats": mean_values,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


def make_plot(df, title, filename_html, filename_png=None, facet_row=None):
    fig = px.line(
        df,
        x="rep_date",
        y="value",
        color="metric",
        line_dash="type" if "type" in df.columns else None,
        facet_row=facet_row,
        markers=True,
        title=title,
        labels={"rep_date": "Date", "value": "Score", "metric": "Metric", "type": "Dataset"},
    )

    fig.update_layout(
        legend_title_text="Metric",
        hovermode="x unified",
        template="plotly_white",
        margin=dict(l=40, r=20, t=60, b=40),
    )
    fig.update_xaxes(tickformat="%Y-%m-%d")
    fig.update_yaxes(showgrid=True, gridcolor="#eaeaea")

    html_path = os.path.join(OUTPUT_DIR, filename_html)
    fig.write_html(html_path, include_plotlyjs="cdn")

    if filename_png:
        png_path = os.path.join(OUTPUT_DIR, filename_png)
        fig.write_image(png_path)

    return fig


def build_plots():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    stats = load_validation_stats()
    stats_long = melt_stats(stats)

    recent_cutoff = stats["rep_date"].max() - pd.Timedelta(days=RECENT_DAYS - 1)
    recent_week = stats_long[stats_long["rep_date"] >= recent_cutoff]
    make_plot(
        recent_week,
        title=f"Validation stats: most recent {RECENT_DAYS} days",
        filename_html="validation_recent_week.html",
        filename_png="validation_recent_week.png",
        facet_row="metric",
    )

    history_cutoff = stats["rep_date"].max() - pd.Timedelta(days=HISTORY_DAYS - 1)
    last_90_days = stats_long[stats_long["rep_date"] >= history_cutoff]
    make_plot(
        last_90_days,
        title=f"Validation stats: last {HISTORY_DAYS} days",
        filename_html="validation_last_90_days.html",
        filename_png="validation_last_90_days.png",
        facet_row="metric",
    )

    rolling_mean = calculate_running_mean(stats)
    rolling_long = melt_stats(rolling_mean)
    make_plot(
        rolling_long,
        title=f"{ROLLING_WINDOW}-day running mean of validation stats",
        filename_html="validation_running_mean.html",
        filename_png="validation_running_mean.png",
        facet_row="metric",
    )

    summary = save_overall_mean_stats(stats)
    print(f"Saved plot images and JSON summary to {OUTPUT_DIR} and {JSON_OUT}")
    print(json.dumps(summary, indent=2))


def main():
    build_plots()


if __name__ == "__main__":
    main()

