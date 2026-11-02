# Data dictionary

## UCI hourly source fields

| Source column | Role in this project | Handling |
|---|---|---|
| instant | Source ID | Excluded from predictors |
| dteday, hr | Timestamp | Combined to hourly datetime; used for order/calendar |
| season, yr, mnth, weekday | Calendar descriptors | Calendar encoding or audit only |
| holiday, workingday | Known calendar features | Included |
| weathersit, temp, atemp, hum, windspeed | Same-hour observed weather | Excluded from one-hour-ahead predictors |
| casual, registered | Components of target | Excluded from predictors; checked against total |
| cnt | Target | Total hourly rental count |

## Aggregate reports

- `reports/model_metrics.csv`: pooled chronological test metrics by model.
- `reports/hourly_error.csv`: aggregate test error by model and hour of day.
- `reports/monthly_metrics.csv`: aggregate test metrics by month and model.
- `reports/split_summary.csv`: train/test windows and aggregate demand levels.
- `reports/data_quality.json`: provenance, sequence gaps, and target checks.
- `reports/summary.json`: forecast scope and aggregate model results.
