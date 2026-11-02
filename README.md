# Capital Bikeshare Hourly Demand Audit

A leakage-safe, one-hour-ahead rolling forecast study using UCI's Capital
Bikeshare hourly records from 2011–2012. It compares seasonal-naive forecasts,
Ridge regression, and histogram gradient boosting under a chronological test
window.

The UCI catalog lists 17,389 instances; its downloaded `hour.csv` contains
17,379 rows. The project records this ten-row catalog/archive discrepancy.

The target is hourly system-wide rentals. The published `casual` and
`registered` columns add up to `cnt`, so both are excluded from predictors.
Same-hour weather is also excluded because the realized value is not known at
the forecast origin.

## Locked chronological result

| Model | MAE (rentals) | RMSE | WAPE |
|---|---:|---:|---:|
| Histogram gradient boosting | 29.23 | 47.31 | 11.70% |
| Ridge regression | 53.48 | 80.58 | 21.40% |
| Previous-week same hour | 64.15 | 109.85 | 25.67% |
| Previous-day same hour | 78.92 | 132.55 | 31.58% |
| Last-hour naive | 85.21 | 129.50 | 34.09% |

The final 3,375 forecastable hours are the chronological test block. The
gradient-boosting score is an offline result for this two-year source, not a
guarantee of current demand accuracy. See `reports/RESULTS.md` for the split,
missing-hour handling, and limits.

## Run locally

Use Python 3.12:

~~~bash
python3 -m venv .venv
make install-dev
make fetch
make build
make verify
make test
make quality
make check-deps
make app
~~~

The final 20% of forecastable timestamps is held out chronologically. The
forecast protocol is rolling one-step ahead: once an hour is observed, its
count can be used in the next hour's lag features. This is not a multi-hour
forecast or station-level inventory estimate.

Reports and API routes contain aggregate metrics by model, month, and hour.
Raw source rows and row-level forecasts remain local and are ignored by Git.
See `reports/RESULTS.md`, `docs/METHODOLOGY.md`, and `NOTICE.md` for the
evaluation, limitations, and attribution.

## API

~~~text
GET /health
GET /summary
GET /models
GET /hourly-error?model=hist_gradient_boosting
GET /monthly-metrics
GET /split-summary
~~~

Run the API with `make api`; launch the dashboard with `make app`.
