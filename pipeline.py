# takes raw data through to a clean, analysis-ready table 

import glob
import sqlite3
import pandas as pd

RAW_CSVS = sorted(glob.glob("data/raw/*.csv"))
DB_PATH = "amr.db"
OUTPUT_CSV = "data/cleaned_resistance_data.csv"

def load_raw_data(csv_paths: list, db_path: str) -> None:
    """Read every raw Atlas export and load them into one SQLite table."""
    frames = [pd.read_csv(path) for path in csv_paths]
    df = pd.concat(frames, ignore_index=True)
    conn = sqlite3.connect(db_path)
    df.to_sql("raw_resistance", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Loaded {len(df)} raw rows from {len(csv_paths)} file(s) into {db_path}")


def clean_with_sql(db_path: str) -> pd.DataFrame:
    """
    Clean and reshape in SQL, not pandas: split the country/pathogen/year
    grain out of the raw export and drop ECDC's '-' missing-value
    placeholder before it gets cast to a number (SQLite casts non-numeric
    strings to 0 silently, which would fake a 0% resistance rate).
    """
    conn = sqlite3.connect(db_path)

    query = """
    SELECT
        RegionName                          AS country,
        RegionCode                          AS country_code,
        REPLACE(Population, '|', ' - ')     AS pathogen_antibiotic,
        Time                                 AS year,
        ROUND(AVG(CAST(NumValue AS REAL)), 2) AS resistance_pct
    FROM raw_resistance
    WHERE TRIM(NumValue) != '-'
    GROUP BY RegionName, RegionCode, Population, Time
    ORDER BY country, pathogen_antibiotic, year;
    """

    cleaned = pd.read_sql_query(query, conn)

    excluded = pd.read_sql_query(
        "SELECT COUNT(*) AS n FROM raw_resistance WHERE TRIM(NumValue) = '-'", conn
    )["n"].iloc[0]

    cleaned.to_sql("resistance_clean", conn, if_exists="replace", index=False)
    conn.close()

    if excluded:
        print(f"Excluded {excluded} row(s) with missing data (marked '-' by ECDC)")

    return cleaned


if __name__ == "__main__":
    if not RAW_CSVS:
        raise SystemExit("No files found in data/raw/ -- add your ECDC export(s) there first.")

    load_raw_data(RAW_CSVS, DB_PATH)
    cleaned_df = clean_with_sql(DB_PATH)
    cleaned_df.to_csv(OUTPUT_CSV, index=False)
    print(f"Wrote {len(cleaned_df)} cleaned rows to {OUTPUT_CSV}")
    print(cleaned_df.head())
