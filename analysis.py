"""
Exploratory trends + a simple forecasting model on top of the cleaned
resistance-rate table, run separately for each of the three pathogens.

Usage:
    python3 analysis.py

Produces:
    outputs/trend_<pathogen>.png     -- one chart per pathogen (top 8
                                         countries by latest resistance rate
                                         highlighted, rest shown faint gray)
    outputs/forecast_summary.csv     -- next-year predicted resistance rate
                                         per country/pathogen, ranked by
                                         which are rising fastest
"""
import os
import re
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

CLEANED_CSV = "data/cleaned_resistance_data.csv"
OUT_DIR = "outputs"
TOP_N_HIGHLIGHT = 8
os.makedirs(OUT_DIR, exist_ok=True)


def safe_filename(text: str) -> str:
    """Turn a pathogen label into something usable as a filename."""
    short = text.split(" - ")[0]  # drop the long resistance-type suffix
    return re.sub(r"[^a-zA-Z0-9]+", "_", short).strip("_").lower()


def plot_trends(df: pd.DataFrame, pathogen: str) -> None:
    """
    EDA: resistance rate over time for one pathogen. With 30 countries, a
    legend for every line is unreadable, so the top N by latest resistance
    rate are highlighted and labeled, the rest drawn faint gray to show
    overall spread without clutter.
    """
    subset = df[df["pathogen_antibiotic"] == pathogen]

    latest_year = subset["year"].max()
    latest_rates = (
        subset[subset["year"] == latest_year]
        .sort_values("resistance_pct", ascending=False)
    )
    highlight_countries = set(latest_rates["country"].head(TOP_N_HIGHLIGHT))

    fig, ax = plt.subplots(figsize=(9, 6))

    for country, group in subset.groupby("country"):
        group = group.sort_values("year")
        if country in highlight_countries:
            ax.plot(group["year"], group["resistance_pct"], marker="o",
                     label=country, linewidth=1.8, zorder=3)
        else:
            ax.plot(group["year"], group["resistance_pct"], color="lightgray",
                     linewidth=0.8, zorder=1)

    short_name = pathogen.split(" - ")[0]
    ax.set_title(f"Resistance rate over time\n{pathogen}", fontsize=10)
    ax.set_xlabel("Year")
    ax.set_ylabel("Resistant isolates (%)")
    ax.legend(fontsize=8, ncol=2, loc="upper left", title=f"Top {TOP_N_HIGHLIGHT} ({latest_year})")
    ax.grid(alpha=0.3)
    fig.tight_layout()

    filename = f"{OUT_DIR}/trend_{safe_filename(pathogen)}.png"
    fig.savefig(filename, dpi=150)
    plt.close(fig)
    print(f"Saved {filename}")


def forecast_next_year(df: pd.DataFrame, min_years: int = 5) -> pd.DataFrame:
    """
    Fit one linear regression per (country, pathogen) group, predicting
    resistance_pct from year. Deliberately simple, on purpose: it's fully
    explainable, and a defensible baseline beats an opaque model you can't
    describe in an interview. min_years guards against fitting a "trend"
    through 2-3 sparse points, which several countries have.
    """
    results = []
    for (country, pathogen), group in df.groupby(["country", "pathogen_antibiotic"]):
        group = group.sort_values("year")
        if len(group) < min_years:
            continue

        X = group[["year"]].values
        y = group["resistance_pct"].values
        model = LinearRegression().fit(X, y)

        next_year = group["year"].max() + 1
        predicted = model.predict([[next_year]])[0]
        slope_per_year = model.coef_[0]

        results.append({
            "country": country,
            "pathogen_antibiotic": pathogen,
            "years_of_data": len(group),
            "latest_year": group["year"].max(),
            "latest_resistance_pct": round(group["resistance_pct"].iloc[-1], 2),
            "predicted_next_year": next_year,
            "predicted_resistance_pct": round(max(0.0, predicted), 2),
            "trend_pct_per_year": round(slope_per_year, 2),
        })

    return pd.DataFrame(results).sort_values("trend_pct_per_year", ascending=False)


if __name__ == "__main__":
    df = pd.read_csv(CLEANED_CSV)

    for pathogen in df["pathogen_antibiotic"].unique():
        plot_trends(df, pathogen)

    forecast_df = forecast_next_year(df)
    forecast_df.to_csv(f"{OUT_DIR}/forecast_summary.csv", index=False)
    print(f"Saved {OUT_DIR}/forecast_summary.csv")

    print("\nFastest-rising country/pathogen combinations:")
    print(forecast_df.head(5).to_string(index=False))

    print("\nFastest-falling (most improved) combinations:")
    print(forecast_df.tail(5).to_string(index=False))
