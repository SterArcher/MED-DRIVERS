# MED-DRIVERS
Analysis code for a PhD study on external and internal drivers of emergency department attendance at UMC Maribor. Daily time series of eTriage/HIS arrivals linked to weather, warnings, air quality, respiratory illness (ERVISS), Google Trends and SBI TOP, using quasi-Poisson DLNM and lagged cross-correlation in Python.

## Preregistration

The study is preregistered on OSF: https://osf.io/6mcbd/overview

## Data sources

To be completed as data are obtained. Status: ⬜ not requested · 🟨 requested · ✅ obtained.

### Outcomes

| Source | Variables | Provider | Resolution | Period | Access / link | Status |
|---|---|---|---|---|---|---|
| eTriaža | Arrivals by stream (injuries, diseases, fast track), Manchester triage category, time of arrival | UKC Maribor | Per visit → daily | TBD | Internal | ⬜ |
| HIS | ICD-10 diagnosis, age, sex, hospital admission | UKC Maribor | Per visit → daily | TBD | Internal | ⬜ |

### Exposures

| Source | Variables | Provider | Resolution | Period | Access / link | Status |
|---|---|---|---|---|---|---|
| Weather | Temperature, humidity, precipitation, wind, pressure, snow | ARSO | Daily | TBD | TBD | ✅ |
| Weather warnings | Warning type and level | ARSO / Meteoalarm | Daily | TBD | TBD | ✅ |
| Air quality | PM10, PM2.5, NO2, O3 | ARSO | Daily | TBD | TBD | ✅ |
| Respiratory illness | ILI, ARI, influenza and RSV positivity (Slovenia) | ECDC ERVISS | Weekly | TBD | https://erviss.org | ✅ |
| Google Trends | Search terms TBD | Google | Daily / weekly | TBD | https://trends.google.com | ✅ |
| SBI TOP | Daily index return | Ljubljana Stock Exchange | Trading days | TBD | https://ljse.si | ✅ |
| NDVI | Mean NDVI over the UKC Maribor catchment | Copernicus Sentinel-2 | 5–16 days | TBD | TBD | ✅ |
| Calendar | Public holidays, bridge days, school holidays | Official calendar | Daily | TBD | TBD | ⬜ |
