"""Tests for source decomposition, lag timing, and aggregate API outputs."""

import asyncio

import httpx
import numpy as np

from bike_share_audit.api import app
from bike_share_audit.constants import (
    COMPONENT_TARGETS,
    FEATURES,
    RAW_DIR,
    SOURCE_ID,
    TARGET,
    TIMESTAMP,
)
from bike_share_audit.data import parse_archive
from bike_share_audit.evaluation import forecast_metrics
from bike_share_audit.features import make_supervised_frame


def test_parser_and_target_decomposition():
    frame = parse_archive(RAW_DIR / "bike-sharing.zip")
    assert frame.shape == (17_379, 18)
    assert frame[SOURCE_ID].is_unique
    assert frame[TIMESTAMP].is_monotonic_increasing
    assert not frame.isna().any().any()
    assert frame[TARGET].equals(frame[COMPONENT_TARGETS].sum(axis=1))


def test_features_use_only_prior_target_history():
    frame = parse_archive(RAW_DIR / "bike-sharing.zip")
    supervised = make_supervised_frame(frame)
    timestamp = supervised.index[500]
    prior = frame.set_index(TIMESTAMP)[TARGET]
    assert (
        supervised.loc[timestamp, "lag_1"]
        == prior.loc[timestamp - np.timedelta64(1, "h")]
    )
    assert (
        supervised.loc[timestamp, "lag_24"]
        == prior.loc[timestamp - np.timedelta64(24, "h")]
    )
    assert not set(FEATURES).intersection(
        {SOURCE_ID, TARGET, *COMPONENT_TARGETS, "temp", "atemp", "hum", "windspeed"}
    )


def test_forecast_metrics_known_values():
    result = forecast_metrics(np.array([10.0, 20.0]), np.array([12.0, 18.0]))
    assert result["mae"] == 2.0
    assert result["rmse"] == 2.0
    assert np.isclose(result["wape"], 4.0 / 30.0)
    assert result["mean_error"] == 0.0
    assert np.isclose(result["r2"], 0.84)


def test_api_only_returns_aggregate_artifacts():
    async def request_api():
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
        ) as client:
            assert (await client.get("/health")).json() == {"status": "ok"}
            assert len((await client.get("/models")).json()) == 5
            hourly = await client.get(
                "/hourly-error", params={"model": "hist_gradient_boosting"}
            )
            assert hourly.status_code == 200
            assert len(hourly.json()) == 24
            assert all("forecast" not in row for row in hourly.json())
            assert len((await client.get("/monthly-metrics")).json()) >= 5
            assert len((await client.get("/split-summary")).json()) == 2

    asyncio.run(request_api())
