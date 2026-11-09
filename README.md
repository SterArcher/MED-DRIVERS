# MED-DRIVERS
Analysis code for a PhD study on external and internal drivers of emergency department attendance at UMC Maribor. Daily time series of eTriage/HIS arrivals linked to weather, warnings, air quality, respiratory illness (ERVISS), Google Trends and SBI TOP, using quasi-Poisson DLNM and lagged cross-correlation in Python.

## Preregistration

The study is preregistered on OSF: https://osf.io/6mcbd/overview

Deviations from the preregistration are documented and will be reported with the results.

## Repository

```
MED-DRIVERS/
├── notebooks/
│   ├── 01_data_aggregation.ipynb   builds the daily panel from all sources
│   ├── 02_lag_variables.ipynb      adds lags, leads and moving averages to the panel
│   └── 03_analysis.ipynb           (planned) analysis of the daily panel
├── scripts/
│   └── merge_arso_weather.py       merges the yearly ARSO weather exports (reproduces the merged file byte for byte)
├── data/        (not on GitHub)    raw/ inputs, processed/ analysis-ready panel + codebook, data_manifest.csv
├── outputs/     (not on GitHub)    01_data_aggregation/ and 02_lag_variables/ reports, 03_analysis/ results
├── docs/        (not on GitHub)    study documents (deviations log)
├── requirements.txt                direct dependencies
├── requirements-lock.txt           all dependencies with pinned versions (uv pip compile --universal)
└── .python-version                 tested Python version
```

Only code and setup files are public. Data, outputs and study documents stay local (`.gitignore`).

> [!WARNING]
> **TEMPORARY – notebook outputs are stripped from every commit.** The notebooks contain charts and tables of hospital data, so a git filter ([nbstripout](https://github.com/kynan/nbstripout), configured in `.gitattributes`) removes all outputs before they reach GitHub. Local notebooks keep their outputs. See [Before publishing](#before-publishing) to turn this off.

## Setup

Python 3.12 is the tested version (`.python-version`); 3.14.0rc1 also works.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
```

Or select `.venv` as the notebook kernel in VS Code and run the **Install packages** cell at the top of `notebooks/01_data_aggregation.ipynb`, then restart the kernel. Notebooks find the project root themselves, so they run from `notebooks/` or from the root.

For the official weather warnings, put the MeteoGate API key in `.env` (gitignored): `METEOALARM_API_KEY=...`

The output-stripping git filter is registered in this clone's `.git/config` and points to `.venv/bin/python`. After recreating `.venv` (or in a new clone), register it again:

```bash
.venv/bin/python -m nbstripout --install --attributes .gitattributes
```

If the filter cannot run, git refuses to commit notebooks (`filter.nbstripout.required = true`), so outputs are never committed by accident.

## Before publishing

> [!IMPORTANT]
> **Remove the temporary output stripping** once the results may be public:
> 1. Delete the line `*.ipynb filter=nbstripout diff=ipynb` from `.gitattributes` (and the TEMPORARY comment above it).
> 2. Run `.venv/bin/python -m nbstripout --uninstall`.
> 3. Remove `nbstripout` from `requirements.txt` and regenerate `requirements-lock.txt`.
> 4. Delete the TEMPORARY warning at the top of this README and this section.
> 5. Check that the notebook outputs contain no small counts that identify patients before committing them.

To regenerate the lock file after changing `requirements.txt`:

```bash
uv pip compile requirements.txt --universal --python-version 3.12 -o requirements-lock.txt
```

## Outputs

`notebooks/01_data_aggregation.ipynb` writes the analysis-ready data to `data/processed/`:

| File | Content |
|---|---|
| `daily_panel.parquet` | One row per day, 2021-01-01 to 2026-06-29: all outcomes and exposures |
| `daily_panel_codebook.csv` | Definition, unit, source, use (primary, secondary, sensitivity, forecasting, exploratory, descriptive, technical), hypothesis and coverage of every column |

and its reports to `outputs/01_data_aggregation/`:

| File | Content |
|---|---|
| `daily_panel_columns.csv` | First and last day with data and % missing per column |
| `dataset_coverage.csv` | Start, end and completeness of every source dataset |
| `holidays_crossref.csv` | Official holiday list vs Nager.Date |
| `warnings_validation.csv` | ARSO text warnings vs official warnings |
| `run_info.json` | Date, git commit, Python and package versions, manifest and panel checksums |

The run stops if a raw file differs from `data/data_manifest.csv`. After a deliberate data update, set `MANIFEST_UPDATE = True` once in the notebook.

## Data sources

All raw data live in `data/raw/<source>/` and are gitignored. Provenance details per source are in the notebook (section "Data provenance").

Status: ⬜ not obtained · 🟨 partial · ✅ obtained

### Outcomes

| Source | Folder | Variables | Provider | Resolution | Coverage | Status |
|---|---|---|---|---|---|---|
| HIS | `his/` | ED unit (KPP, Enota za bolezni, INP, Hitri pregledi), Manchester category, ICD-10 diagnosis, age, sex, **hospital admission** (admitting unit and time; daily `adm_*` columns), death in ED, pseudonymised patient ID | UKC Maribor | Per visit | 2021-01-01 – 2026-06-29 | ✅ |
| eTriaža | `etriaza/` | Arrival time and mode, triage algorithm; linked to HIS by `eTriazaId` = `id` (complete wherever both exist) | UKC Maribor | Per visit | 2018-08-31 – 2026-04-22 | ✅ |

### Exposures

| Source | Folder | Variables | Provider | Resolution | Coverage | Status |
|---|---|---|---|---|---|---|
| Weather | `arso_weather/` | Temperature (mean/min/max), precipitation, snow, sunshine, cloud, storm flags; station Maribor – letališče. Raw yearly exports in `raw_yearly/`. Derived temperature events (hot day, heatwave, frost day, …) | ARSO | Daily | 2019-01-01 – 2026-07-31 | ✅ |
| Reanalysis weather | `era5/` | Temperature, relative humidity, dew point (ERA5-Land, 0.1°), wind and surface pressure (ERA5, 0.25°); apparent temperature (Steadman) and feels-like temperature (NWS heat index / wind chill) computed. Downloaded by the notebook | Copernicus ERA5 via Open-Meteo (CC BY 4.0) | Hourly | 2020-12 – 2026-07 | ✅ |
| Air quality (Maribor) | `arso_air/` | PM10, PM2.5, NO2, O3; EEA station SI0059A (Maribor). European Air Quality Index (revised EEA bands) computed hourly | ARSO / EEA | Hourly / daily | 2013 – 2026 | ✅ |
| Air quality (Maribor stations) | `arso_air/` | PM10, PM2.5 at E407 MB Titova and E408 MB Vrbanski; the other 20 stations in Slovenia in the extract are not used | ARSO | Hourly | 2021-01 – 2025-12 | ✅ |
| Respiratory illness | `erviss/` | ILI/ARI rates, sentinel positivity, detections (Slovenia) | ECDC ERVISS | Weekly | 2022-W25 – 2026-W40 | 🟨 starts mid-2022 |
| COVID-19 (Štajerska) | `covid_sledilnik/` | New cases, active cases and deaths for Podravska + Savinjska; COVID-19 patients, ICU and admissions at UKC Maribor; SARS-CoV-2 in Maribor wastewater. Downloaded by the notebook | [Sledilnik API](https://api.sledilnik.org/api/) | Daily (wastewater ~weekly) | 2020-03 – 2023-04 | ✅ |
| PCR testing | `PCR testing/` | Positive SARS-CoV-2, influenza A/B, RSV tests, Maribor. Spliced with ERVISS into a combined influenza index for the whole period | NLZOH, Maribor | Daily | 2021-01-01 – 2024-02-29 | 🟨 no test totals |
| Weather warnings (official) | `meteoalarm/` | Official ARSO warnings with level and region, from the MeteoAlarm archive via the MeteoGate API (key in `.env`); also validates the text warnings | MeteoAlarm / ARSO | Per message | 2025-04-12 – | ✅ |
| Google Trends | `google_trends/` | "urgenca maribor" | Google | Monthly | 2004 – 2026-10 | 🟨 monthly, one term |
| SBI TOP | `sbi_top/` | Close, daily log return | Ljubljana Stock Exchange | Trading days | 2018-01-03 – 2026-11-06 | ✅ |
| NDVI | `ndvi/` | Mean NDVI, Maribor box and Štajerska (Podravska + Savinjska); downloaded by the notebook | Copernicus Sentinel-2 (Planetary Computer) | Per clear scene | from 2020-07 | ✅ |
| COVID-19 restrictions | `oxcgrt/` | Daily stringency index for Slovenia (Oxford COVID-19 Government Response Tracker); alternative to the 0/1 COVID indicator. Downloaded by the notebook | [OxCGRT](https://github.com/OxCGRT/covid-policy-dataset) (CC BY 4.0) | Daily | 2020-01-01 – 2022-12-31 | ✅ |
| Calendar | `calendar/` | Work-free public holidays (official list cross-referenced with Nager.Date), Martinovo, bridge days, school holidays (OpenHolidays, eastern region) | Official calendar, Nager.Date, OpenHolidays | Daily | 2021 – 2026 | ✅ |

### Other (exploratory, not preregistered)

| Source | Folder | Variables | Coverage | Status |
|---|---|---|---|---|
| Weather warnings (text) | `arso_warnings/` | Warning type, area, validity period from ARSO forecast texts; no levels, 41% of dates assumed; broad and strict versions. Extraction script not in the repository | 1995 – 2026-08 | 🟨 |
| EMS dispatch | `EMS/` | Calls per day (roll-out until 2024-09-06 dropped) | 2024-09-07 – 2026-10-13 | ✅ |
| Football fixtures | `NZS/` | MNZ Maribor matches per day | 2021-04-24 – 2024-05-24 | ✅ |
| Hospital occupancy | `hospital capacity/` | Hourly occupancy by department (55 departments) | 2021-01-01 – 2024-10-31 | ✅ |
| Pollen | `pollen/` | 13 taxa + total, Maribor | 2021 – 2023 | ✅ |
| Moon phase | `moon/` | Illumination and moon age (calculated, Meeus); full and new moon days from the US Naval Observatory API (cached). Negative-control exposure | 2021 – 2026 | ✅ |
