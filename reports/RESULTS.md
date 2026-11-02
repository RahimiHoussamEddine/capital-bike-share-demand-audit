# Results: Capital Bikeshare hourly demand audit

The UCI hourly file has 17,379 records spanning 2011-01-01 to 2012-12-31. The UCI catalog lists 17,389 instances; the archived file has ten fewer rows. The target is total hourly rentals.

## Chronological test block

| Model | MAE | RMSE | WAPE | Mean error | R-squared |
|---|---:|---:|---:|---:|---:|
| Histogram gradient boosting | 29.23 | 47.31 | 11.70% | -3.53 | 0.954 |
| Ridge regression | 53.48 | 80.58 | 21.40% | 1.29 | 0.866 |
| Previous-week same hour | 64.15 | 109.85 | 25.67% | 8.70 | 0.752 |
| Previous-day same hour | 78.92 | 132.55 | 31.58% | 1.10 | 0.638 |
| Last-hour naive | 85.21 | 129.50 | 34.09% | 0.37 | 0.655 |

The lowest test MAE came from **Histogram gradient boosting** (29.23 rentals). The test period follows the training period chronologically.

## Design notes

The train window contains 13,500 forecastable hours through 2012-08-08; the locked test contains 3,375 hours from 2012-08-08 to 2012-12-31.
There are 165 missing clock-hour slots in the source span. Forecastable rows with unavailable exact lags are excluded after reindexing to a complete hourly clock.
This is a rolling one-hour-ahead evaluation: after each hour is observed, its rental count can be used as lag history for the next forecast. Same-hour weather is excluded because it would require a weather forecast available at prediction time.
`casual` and `registered` sum to `cnt`; both components and the source row ID are excluded from predictors. The project reports system-wide rental demand, not station-level bike availability or causal effects of fleet changes.

Aggregate errors by hour and month are available in the companion CSVs. No row-level forecasts are published.

See [methodology](../docs/METHODOLOGY.md), [data dictionary](../docs/DATA_DICTIONARY.md), and [source notice](../NOTICE.md).
