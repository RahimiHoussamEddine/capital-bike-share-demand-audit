"""Leakage-safe one-hour-ahead rolling features."""

from __future__ import annotations

import numpy as np
import pandas as pd

from bike_share_audit.constants import (
    FEATURES,
    TARGET,
    TIMESTAMP,
)


def make_supervised_frame(frame: pd.DataFrame) -> pd.DataFrame:
    observed = frame.set_index(TIMESTAMP).sort_index()
    full_index = pd.date_range(observed.index.min(), observed.index.max(), freq="h")
    target = observed[TARGET].reindex(full_index)
    features = pd.DataFrame(index=full_index)

    hour_angle = 2 * np.pi * full_index.hour / 24
    weekday_angle = 2 * np.pi * full_index.day_of_week / 7
    month_angle = 2 * np.pi * (full_index.month - 1) / 12
    features["hour_sin"] = np.sin(hour_angle)
    features["hour_cos"] = np.cos(hour_angle)
    features["weekday_sin"] = np.sin(weekday_angle)
    features["weekday_cos"] = np.cos(weekday_angle)
    features["month_sin"] = np.sin(month_angle)
    features["month_cos"] = np.cos(month_angle)
    features["year"] = full_index.year - full_index.year.min()
    features["holiday"] = observed["holiday"].reindex(full_index)
    features["workingday"] = observed["workingday"].reindex(full_index)

    previous = target.shift(1)
    features["lag_1"] = previous
    features["lag_24"] = target.shift(24)
    features["lag_168"] = target.shift(168)
    features["mean_24"] = previous.rolling(24, min_periods=18).mean()
    features["mean_168"] = previous.rolling(168, min_periods=126).mean()

    supervised = features.join(target.rename(TARGET))
    return supervised.dropna(subset=[*FEATURES, TARGET]).sort_index()
