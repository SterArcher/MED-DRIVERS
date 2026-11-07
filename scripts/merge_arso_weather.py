"""Merge the yearly ARSO daily climate exports for Maribor - letališče into one CSV.

Original script: written for the 2026-08 forecasting project (202604_etriaža MB/vreme/Maribor 2019-2026/merge_arso.py).
Only the input and output paths were changed; the processing is identical.

Usage (from the repository root):
    python scripts/merge_arso_weather.py
    python scripts/merge_arso_weather.py --src data/raw/arso_weather/raw_yearly --out data/raw/arso_weather

Input:  one ARSO export per year, files named 2019 ... 2026 (CSV with Slovene headers)
Output: maribor_weather_2019_2026_merged.csv and maribor_weather_yearly_summary.csv in --out
"""
import argparse
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
parser.add_argument("--src", type=Path, default=ROOT / "data/raw/arso_weather/raw_yearly")
parser.add_argument("--out", type=Path, default=ROOT / "data/raw/arso_weather")
args = parser.parse_args()
SRC = args.src
OUT = args.out
OUT.mkdir(parents=True, exist_ok=True)

YEARS = [str(y) for y in range(2019, 2027)]

RENAME = {
    "station id": "station_id",
    "station name": "station_name",
    "valid": "date",
    "povp. dnevna T [°C]": "t_avg_c",
    "max. T [°C]": "t_max_c",
    "min. T [°C]": "t_min_c",
    "količina padavin [mm]": "precip_mm",
    "višina snežne odeje [cm]": "snow_depth_cm",
    "višina novega snega [cm]": "new_snow_cm",
    "trajanje sonca [h]": "sunshine_h",
    "oblačnost [%]": "cloud_pct",
    "nevihta": "storm",
    "grmenje": "thunder",
    "bliskanje": "lightning",
    "toča": "hail",
    "viharni veter": "gale",
}
NUMERIC = ["t_avg_c", "t_max_c", "t_min_c", "precip_mm", "snow_depth_cm",
           "new_snow_cm", "sunshine_h", "cloud_pct"]
BOOL = ["storm", "thunder", "lightning", "hail", "gale"]

frames = []
raw_counts = {}
for y in YEARS:
    text = (SRC / y).read_text(encoding="utf-8")
    # ARSO export uses "\n\r" as the record separator -> strip stray CRs
    text = text.replace("\r", "")
    from io import StringIO
    df = pd.read_csv(StringIO(text), dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.rename(columns=RENAME)
    df["source_file"] = y
    raw_counts[y] = len(df)
    frames.append(df)

df = pd.concat(frames, ignore_index=True)

# --- clean ---
df["station_id"] = df["station_id"].str.strip()
df["station_name"] = df["station_name"].str.strip()
df["date"] = pd.to_datetime(df["date"], format="%Y-%m-%d")

for c in NUMERIC:
    df[c] = pd.to_numeric(df[c].str.strip().replace({"": None}), errors="coerce")

for c in BOOL:
    s = df[c].str.strip().str.lower()
    df[c] = s.map({"da": True, "ne": False})

# derived
df["year"] = df["date"].dt.year
df["month"] = df["date"].dt.month
df["doy"] = df["date"].dt.dayofyear
df["t_range_c"] = (df["t_max_c"] - df["t_min_c"]).round(1)

cols = (["station_id", "station_name", "date", "year", "month", "doy"]
        + NUMERIC + ["t_range_c"] + BOOL + ["source_file"])
df = df[cols].sort_values("date").reset_index(drop=True)

# --- QC ---
print("rows per source file:", raw_counts)
print("merged rows:", len(df))
print("stations:", df[["station_id", "station_name"]].drop_duplicates().to_dict("records"))
print("date span:", df["date"].min().date(), "->", df["date"].max().date())
print("duplicate dates:", int(df["date"].duplicated().sum()))

full = pd.date_range(df["date"].min(), df["date"].max(), freq="D")
missing = full.difference(df["date"])
print("calendar gaps:", len(missing), list(missing[:20].date))

print("\nmissing values per column:")
print(df[NUMERIC + BOOL].isna().sum().to_string())

print("\ncloud_pct availability by year:")
print(df.groupby("year")["cloud_pct"].apply(lambda s: f"{s.notna().sum()}/{len(s)}").to_string())

print("\nsanity: t_min > t_max rows:", int((df["t_min_c"] > df["t_max_c"]).sum()))
print("negative precip rows:", int((df["precip_mm"] < 0).sum()))
print("sunshine > 16h rows:", int((df["sunshine_h"] > 16).sum()))

print("\nnumeric summary:")
print(df[NUMERIC].describe().T.to_string())

print("\nyearly summary:")
yearly = df.groupby("year").agg(
    days=("date", "size"),
    t_avg=("t_avg_c", "mean"),
    t_max_abs=("t_max_c", "max"),
    t_min_abs=("t_min_c", "min"),
    precip_total_mm=("precip_mm", "sum"),
    rain_days=("precip_mm", lambda s: int((s >= 1).sum())),
    sunshine_total_h=("sunshine_h", "sum"),
    summer_days_30c=("t_max_c", lambda s: int((s >= 30).sum())),
    frost_days=("t_min_c", lambda s: int((s < 0).sum())),
    storm_days=("storm", "sum"),
    hail_days=("hail", "sum"),
).round(1)
print(yearly.to_string())

# --- write ---
df.to_csv(OUT / "maribor_weather_2019_2026_merged.csv", index=False)
yearly.to_csv(OUT / "maribor_weather_yearly_summary.csv")
print("\nwritten.")

gaps = df[df[["t_max_c","t_min_c","snow_depth_cm","new_snow_cm","sunshine_h"]].isna().any(axis=1)]
print("\nrows with any missing core value:", len(gaps))
print(gaps[["date","t_avg_c","t_max_c","t_min_c","snow_depth_cm","new_snow_cm","sunshine_h"]].to_string(index=False))
