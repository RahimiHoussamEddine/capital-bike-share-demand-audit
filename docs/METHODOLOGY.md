# Methodology

## Scope

This project forecasts total hourly rental counts for the Capital Bikeshare
system in the UCI dataset. It does not estimate station-level availability,
fleet size, causal impact of expansion, or current demand in Washington, DC.

## Source and feature checks

- Download the official UCI archive and validate byte count and SHA-256.
- Parse the hourly file, require the exact schema, unique increasing record
  IDs and timestamps, and no missing source values.
- Record the UCI catalog's 17,389-instance figure and compare it with the
  17,379 rows in the pinned hourly CSV.
- Check the identity `cnt = casual + registered`. Exclude both components and
  the source record ID from model features.
- Exclude same-hour observed weather from predictors. Such values are not
  available at a one-hour-ahead forecast origin unless supplied by a separate
  weather forecast.
- Reindex to a complete hourly clock before constructing exact time lags.
  Rows without required prior-hour history are omitted from evaluation.

## Forecast protocol

Forecast each observed hour using information available through the prior
hour. Baselines use the previous hour, the previous day's same hour, and the
previous week's same hour. The fixed models use cyclic calendar features,
known holiday/working-day fields, exact demand lags, and trailing historical
averages.

The first 80% of forecastable observations is training data; the final 20% is
the locked chronological test. This is a rolling one-step-ahead evaluation:
after a test hour is observed, it may serve as history for the next hour. It
does not evaluate a fixed-origin 24-hour or weekly forecast.

## Models and measures

- Last-hour naive.
- Previous-day same-hour naive.
- Previous-week same-hour naive.
- Standardized Ridge regression with alpha 10.
- Histogram gradient boosting with fixed tree/regularization settings.

Report MAE, RMSE, WAPE, mean signed error, and R-squared. Error is also
aggregated by hour of day and month. Test predictions are used only in memory
to create aggregate reports and are not published.

## Limits

- The data cover one system and historical years 2011–2012.
- The source has gaps in its hourly sequence; missing clock slots are counted
  and lag availability is handled explicitly.
- Weather is omitted, so a weather-informed forecast could perform differently.
- The one-step rolling protocol uses observed test-period demand after each
  hour has elapsed; results do not apply to longer fixed-origin horizons.
- Aggregate system-wide rentals are not a direct measure of bikes available at
  any station or of customer unmet demand.
