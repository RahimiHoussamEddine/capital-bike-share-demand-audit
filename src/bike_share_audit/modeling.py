"""Fixed forecasting models and seasonal-naive baselines."""

from __future__ import annotations

from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

MODEL_LABELS = {
    "last_hour": "Last-hour naive",
    "daily_seasonal": "Previous-day same hour",
    "weekly_seasonal": "Previous-week same hour",
    "ridge": "Ridge regression",
    "hist_gradient_boosting": "Histogram gradient boosting",
}


def make_models() -> dict[str, Pipeline | HistGradientBoostingRegressor]:
    return {
        "ridge": Pipeline(
            [
                ("scale", StandardScaler()),
                ("model", Ridge(alpha=10.0)),
            ]
        ),
        "hist_gradient_boosting": HistGradientBoostingRegressor(
            max_iter=200,
            max_leaf_nodes=31,
            l2_regularization=5.0,
            random_state=2026,
        ),
    }
