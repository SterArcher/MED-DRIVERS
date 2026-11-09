"""Check which 24 hours the ARSO daily precipitation of Maribor - letališče covers.

ARSO climate stations read the rain gauge at 07:00 CET (UTC+1, 08:00 local time in summer). ARSO's definition
(Razlaga meteoroloških spremenljivk) dates the 24-hour total by the reading day; the yearly exports do not say so.
This script checks it independently against ERA5 hourly precipitation (Open-Meteo archive, same grid cell as
notebook 01), summed three ways:

- calendar day 00-24 local time,
- 07:00 CET (d) -> 07:00 CET (d+1), dated d (start day),
- 07:00 CET (d-1) -> 07:00 CET (d), dated d (reading day; ARSO definition: "24-urna akumulacija padavin ob 7 h").

Result (run 2026-11-09, 2021-01-01 to 2026-06-29): Pearson r 0.35 / 0.14 / 0.77, consistent with the definition.
Notebook 01 therefore shifts precipitation and new snow back one day (see section 2.1).

Usage (from the repository root):
    python scripts/check_arso_precip_dating.py

Downloads ERA5 to a temporary folder (not data/raw/, so the data manifest is not affected).
"""
import json
import tempfile
from pathlib import Path

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
ARSO = ROOT / "data/raw/arso_weather/maribor_weather_2019_2026_merged.csv"
START, END = "2021-01-01", "2026-06-29"
PARAMS = dict(latitude=46.5541, longitude=15.6447, models="era5", hourly="precipitation",
              start_date="2020-12-30", end_date="2026-07-01", timezone="GMT")


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        r = requests.get("https://archive-api.open-meteo.com/v1/archive", params=PARAMS, timeout=300)
        r.raise_for_status()
        f = Path(tmp) / "era5_precip.json"
        f.write_text(r.text)
        d = json.loads(f.read_text())

    # Hour-ending values in UTC -> hour-starting
    t_utc = pd.DatetimeIndex(pd.to_datetime(d["hourly"]["time"])).tz_localize("UTC")
    h_utc = pd.Series(d["hourly"]["precipitation"], index=t_utc, dtype=float).shift(-1, freq="h")

    local = h_utc.copy()
    local.index = local.index.tz_convert("Europe/Ljubljana").tz_localize(None)
    calendar = local.resample("D").sum()                         # 00-24 local time

    # ARSO reads the gauge at 07:00 CET = 06:00 UTC all year (08:00 local time in summer)
    from_07 = h_utc.copy()
    from_07.index = from_07.index.tz_localize(None) - pd.Timedelta(hours=6)
    start_day = from_07.resample("D").sum()                      # 07 CET (d) -> 07 CET (d+1), dated d
    reading_day = start_day.copy()
    reading_day.index = reading_day.index + pd.Timedelta(days=1)  # 07(d-1) -> 07(d), dated d

    arso = pd.read_csv(ARSO, parse_dates=["date"]).set_index("date")["precip_mm"].loc[START:END]
    rows = {}
    for name, s in {"calendar day 00-24": calendar, "07-07 dated by start day": start_day,
                    "07-07 dated by reading day": reading_day}.items():
        j = pd.concat([arso, s], axis=1, join="inner").dropna()
        j.columns = ["arso", "era5"]
        rows[name] = {"pearson": j.corr().iat[0, 1], "spearman": j.corr("spearman").iat[0, 1],
                      "wet-day agreement (>= 1 mm)": ((j["arso"] >= 1) == (j["era5"] >= 1)).mean(), "days": len(j)}
    print(pd.DataFrame(rows).T.round(3).to_string())


if __name__ == "__main__":
    main()
