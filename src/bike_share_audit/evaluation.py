"""Chronological rolling one-hour-ahead evaluation."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from bike_share_audit.constants import FEATURES, REPORTS_DIR, TARGET
from bike_share_audit.features import make_supervised_frame
from bike_share_audit.modeling import MODEL_LABELS, make_models


def forecast_metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    denominator = float(np.sum(np.abs(actual)))
    return {
        "mae": float(mean_absolute_error(actual, predicted)),
        "rmse": float(mean_squared_error(actual, predicted) ** 0.5),
        "wape": float(np.sum(np.abs(actual - predicted)) / denominator),
        "mean_error": float(np.mean(predicted - actual)),
        "r2": float(r2_score(actual, predicted)),
    }


def evaluate(
    frame: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    supervised = make_supervised_frame(frame)
    cut = int(0.80 * len(supervised))
    train = supervised.iloc[:cut]
    test = supervised.iloc[cut:]
    x_train, x_test = train[FEATURES], test[FEATURES]
    y_train = train[TARGET].to_numpy(dtype=float)
    y_test = test[TARGET].to_numpy(dtype=float)

    predictions: dict[str, np.ndarray] = {
        "last_hour": test["lag_1"].to_numpy(dtype=float),
        "daily_seasonal": test["lag_24"].to_numpy(dtype=float),
        "weekly_seasonal": test["lag_168"].to_numpy(dtype=float),
    }
    for model_name, model in make_models().items():
        model.fit(x_train, y_train)
        predictions[model_name] = model.predict(x_test)

    metric_rows: list[dict[str, object]] = []
    hourly_rows: list[dict[str, object]] = []
    monthly_rows: list[dict[str, object]] = []
    timestamps = test.index
    for model_name, predicted in predictions.items():
        metric_rows.append(
            {
                "model": model_name,
                "n_test": len(y_test),
                "test_start": timestamps.min().isoformat(),
                "test_end": timestamps.max().isoformat(),
                **forecast_metrics(y_test, predicted),
            }
        )
        errors = pd.DataFrame(
            {
                "timestamp": timestamps,
                "actual": y_test,
                "predicted": predicted,
                "absolute_error": np.abs(y_test - predicted),
                "error": predicted - y_test,
            }
        )
        for hour, group in errors.groupby(errors["timestamp"].dt.hour):
            hourly_rows.append(
                {
                    "model": model_name,
                    "hour": int(hour),
                    "n": len(group),
                    "mae": float(group["absolute_error"].mean()),
                    "mean_error": float(group["error"].mean()),
                }
            )
        errors["month"] = errors["timestamp"].dt.to_period("M").astype(str)
        for month, group in errors.groupby("month", sort=True):
            monthly_rows.append(
                {
                    "model": model_name,
                    "month": month,
                    "n": len(group),
                    **forecast_metrics(
                        group["actual"].to_numpy(dtype=float),
                        group["predicted"].to_numpy(dtype=float),
                    ),
                }
            )

    metrics = pd.DataFrame(metric_rows)
    hourly = pd.DataFrame(hourly_rows)
    monthly = pd.DataFrame(monthly_rows)
    split_summary = pd.DataFrame(
        [
            {
                "split": "train",
                "n": len(train),
                "timestamp_start": train.index.min().isoformat(),
                "timestamp_end": train.index.max().isoformat(),
                "mean_demand": float(train[TARGET].mean()),
            },
            {
                "split": "test",
                "n": len(test),
                "timestamp_start": test.index.min().isoformat(),
                "timestamp_end": test.index.max().isoformat(),
                "mean_demand": float(test[TARGET].mean()),
            },
        ]
    )
    return metrics, hourly, monthly, split_summary


def _write_results(
    metrics: pd.DataFrame,
    hourly: pd.DataFrame,
    split_summary: pd.DataFrame,
    quality: dict[str, object],
) -> None:
    ordered = metrics.sort_values("mae")
    best = ordered.iloc[0]
    train = split_summary[split_summary["split"] == "train"].iloc[0]
    test = split_summary[split_summary["split"] == "test"].iloc[0]
    lines = [
        "# Results: Capital Bikeshare hourly demand audit",
        "",
        (
            f"The UCI hourly file has {quality['rows']:,} records spanning "
            f"{quality['timestamp_start'][:10]} to {quality['timestamp_end'][:10]}. "
            f"The UCI catalog lists {quality['catalog_listed_rows']:,} "
            "instances; the archived file has ten fewer rows. The target is "
            "total hourly rentals."
        ),
        "",
        "## Chronological test block",
        "",
        "| Model | MAE | RMSE | WAPE | Mean error | R-squared |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in ordered.itertuples(index=False):
        lines.append(
            f"| {MODEL_LABELS[row.model]} | {row.mae:.2f} | {row.rmse:.2f} | "
            f"{row.wape:.2%} | {row.mean_error:.2f} | {row.r2:.3f} |"
        )
    lines.extend(
        [
            "",
            (
                f"The lowest test MAE came from **{MODEL_LABELS[best['model']]}** "
                f"({best['mae']:.2f} rentals). The test period follows the "
                "training period chronologically."
            ),
            "",
            "## Design notes",
            "",
            (
                f"The train window contains {int(train['n']):,} forecastable "
                f"hours through {train['timestamp_end'][:10]}; the locked test "
                f"contains {int(test['n']):,} hours from "
                f"{test['timestamp_start'][:10]} to {test['timestamp_end'][:10]}."
            ),
            (
                f"There are {quality['missing_hour_slots']} missing clock-hour "
                "slots in the source span. Forecastable rows with unavailable "
                "exact lags are excluded after reindexing to a complete hourly "
                "clock."
            ),
            (
                "This is a rolling one-hour-ahead evaluation: after each hour "
                "is observed, its rental count can be used as lag history for "
                "the next forecast. Same-hour weather is excluded because it "
                "would require a weather forecast available at prediction time."
            ),
            (
                "`casual` and `registered` sum to `cnt`; both components and "
                "the source row ID are excluded from predictors. The project "
                "reports system-wide rental demand, not station-level bike "
                "availability or causal effects of fleet changes."
            ),
            "",
            (
                "Aggregate errors by hour and month are available in the "
                "companion CSVs. No row-level forecasts are published."
            ),
            "",
            (
                "See [methodology](../docs/METHODOLOGY.md), "
                "[data dictionary](../docs/DATA_DICTIONARY.md), and "
                "[source notice](../NOTICE.md)."
            ),
            "",
        ]
    )
    (REPORTS_DIR / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


def build_report(
    frame: pd.DataFrame,
    quality: dict[str, object],
) -> dict[str, object]:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    metrics, hourly, monthly, split_summary = evaluate(frame)
    metrics.to_csv(REPORTS_DIR / "model_metrics.csv", index=False, float_format="%.8f")
    hourly.to_csv(REPORTS_DIR / "hourly_error.csv", index=False, float_format="%.8f")
    monthly.to_csv(
        REPORTS_DIR / "monthly_metrics.csv", index=False, float_format="%.8f"
    )
    split_summary.to_csv(
        REPORTS_DIR / "split_summary.csv", index=False, float_format="%.8f"
    )
    (REPORTS_DIR / "data_quality.json").write_text(
        json.dumps(quality, indent=2) + "\n", encoding="utf-8"
    )
    summary: dict[str, object] = {
        "dataset": "UCI Bike Sharing hourly file",
        "rows": len(frame),
        "catalog_listed_rows": quality["catalog_listed_rows"],
        "catalog_archive_row_count_difference": quality["archive_row_count_difference"],
        "target": TARGET,
        "target_components": ["casual", "registered"],
        "target_components_used_as_features": False,
        "same_hour_weather_used_as_feature": False,
        "forecast_mode": "rolling one-hour-ahead",
        "metrics": metrics.to_dict(orient="records"),
        "row_level_forecasts_published": False,
    }
    (REPORTS_DIR / "summary.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    _write_results(metrics, hourly, split_summary, quality)
    return summary
