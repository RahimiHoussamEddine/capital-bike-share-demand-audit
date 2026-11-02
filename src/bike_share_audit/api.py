"""Read-only API for aggregate forecast artifacts."""

from __future__ import annotations

import json

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

from bike_share_audit.constants import REPORTS_DIR
from bike_share_audit.modeling import MODEL_LABELS

app = FastAPI(
    title="Capital Bikeshare Demand Audit API",
    version="0.1.0",
    description="Aggregate-only hourly demand forecast results.",
)


@app.get("/health")
async def health() -> dict[str, str]:
    ready = (REPORTS_DIR / "summary.json").is_file()
    return {"status": "ok" if ready else "not_ready"}


@app.get("/summary")
async def summary() -> dict[str, object]:
    path = REPORTS_DIR / "summary.json"
    if not path.is_file():
        raise HTTPException(status_code=503, detail="Run `make build` first")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/models")
async def models() -> list[dict[str, object]]:
    path = REPORTS_DIR / "model_metrics.csv"
    if not path.is_file():
        raise HTTPException(status_code=503, detail="Run `make build` first")
    return pd.read_csv(path).to_dict(orient="records")


@app.get("/hourly-error")
async def hourly_error(model: str = Query(...)) -> list[dict[str, object]]:
    path = REPORTS_DIR / "hourly_error.csv"
    if not path.is_file():
        raise HTTPException(status_code=503, detail="Run `make build` first")
    if model not in MODEL_LABELS:
        raise HTTPException(
            status_code=404,
            detail={"available_models": sorted(MODEL_LABELS)},
        )
    table = pd.read_csv(path)
    return table[table["model"] == model].to_dict(orient="records")


@app.get("/monthly-metrics")
async def monthly_metrics() -> list[dict[str, object]]:
    path = REPORTS_DIR / "monthly_metrics.csv"
    if not path.is_file():
        raise HTTPException(status_code=503, detail="Run `make build` first")
    return pd.read_csv(path).to_dict(orient="records")


@app.get("/split-summary")
async def split_summary() -> list[dict[str, object]]:
    path = REPORTS_DIR / "split_summary.csv"
    if not path.is_file():
        raise HTTPException(status_code=503, detail="Run `make build` first")
    return pd.read_csv(path).to_dict(orient="records")
