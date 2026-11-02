"""Parse the pinned hourly dataset and produce aggregate source checks."""

from __future__ import annotations

import hashlib
import io
import json
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd

from bike_share_audit.constants import (
    ARCHIVE_EXPECTED_ROWS,
    CATALOG_LISTED_ROWS,
    COMPONENT_TARGETS,
    RAW_DIR,
    SOURCE_BYTES,
    SOURCE_DOI,
    SOURCE_ID,
    SOURCE_MEMBER,
    SOURCE_SHA256,
    SOURCE_URL,
    TARGET,
    TIMESTAMP,
)

EXPECTED_COLUMNS = [
    "instant",
    "dteday",
    "season",
    "yr",
    "mnth",
    "hr",
    "holiday",
    "weekday",
    "workingday",
    "weathersit",
    "temp",
    "atemp",
    "hum",
    "windspeed",
    "casual",
    "registered",
    "cnt",
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_archive(path: Path | None = None) -> pd.DataFrame:
    path = path or RAW_DIR / "bike-sharing.zip"
    if not path.is_file():
        raise FileNotFoundError(f"Missing {path}; run `make fetch` first")
    if path.stat().st_size != SOURCE_BYTES or sha256_file(path) != SOURCE_SHA256:
        raise ValueError("UCI archive differs from the pinned source snapshot")
    with zipfile.ZipFile(path) as archive:
        if SOURCE_MEMBER not in archive.namelist():
            raise ValueError(f"Expected CSV is missing: {SOURCE_MEMBER}")
        payload = archive.read(SOURCE_MEMBER)
    frame = pd.read_csv(io.BytesIO(payload))
    if frame.columns.tolist() != EXPECTED_COLUMNS:
        raise ValueError(f"Unexpected hourly columns: {frame.columns.tolist()}")
    frame[TIMESTAMP] = pd.to_datetime(
        frame["dteday"], errors="raise"
    ) + pd.to_timedelta(frame["hr"], unit="h")
    numeric = [column for column in EXPECTED_COLUMNS if column not in {"dteday"}]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
    if frame.isna().any().any():
        raise ValueError("UCI source contains missing values")
    if len(frame) != ARCHIVE_EXPECTED_ROWS:
        raise ValueError(
            f"Expected {ARCHIVE_EXPECTED_ROWS:,} hourly rows, received {len(frame)}"
        )
    if frame[SOURCE_ID].duplicated().any() or frame[TIMESTAMP].duplicated().any():
        raise ValueError("Source record ID and timestamp must be unique")
    if not frame[SOURCE_ID].is_monotonic_increasing:
        raise ValueError("Source record IDs are not monotonic")
    if not frame[TIMESTAMP].is_monotonic_increasing:
        raise ValueError("Hourly records are not chronological")
    return frame


def data_quality_report(frame: pd.DataFrame, path: Path) -> dict[str, Any]:
    expected_index = pd.date_range(
        frame[TIMESTAMP].min(), frame[TIMESTAMP].max(), freq="h"
    )
    component_mismatch = int(
        (frame[TARGET] != frame[COMPONENT_TARGETS].sum(axis=1)).sum()
    )
    return {
        "source": {
            "url": SOURCE_URL,
            "archive": "bike-sharing.zip",
            "member": SOURCE_MEMBER,
            "bytes": path.stat().st_size,
            "sha256": sha256_file(path),
            "doi": SOURCE_DOI,
            "license": "CC BY 4.0",
        },
        "rows": len(frame),
        "catalog_listed_rows": CATALOG_LISTED_ROWS,
        "archive_row_count_difference": CATALOG_LISTED_ROWS - len(frame),
        "feature_count_in_source": 13,
        "missing_cells": int(frame.isna().sum().sum()),
        "duplicate_record_ids": int(frame[SOURCE_ID].duplicated().sum()),
        "duplicate_timestamps": int(frame[TIMESTAMP].duplicated().sum()),
        "missing_hour_slots": int(len(expected_index) - frame[TIMESTAMP].nunique()),
        "target_components_match_total": component_mismatch == 0,
        "target_component_mismatch_rows": component_mismatch,
        "target_sum": int(frame[TARGET].sum()),
        "target_mean": float(frame[TARGET].mean()),
        "target_median": float(frame[TARGET].median()),
        "timestamp_start": frame[TIMESTAMP].min().isoformat(),
        "timestamp_end": frame[TIMESTAMP].max().isoformat(),
        "modeling": {
            "source_id_used_as_feature": False,
            "casual_or_registered_used_as_feature": False,
            "same_hour_weather_used_as_feature": False,
            "row_level_forecasts_published": False,
        },
    }


def write_source_manifest(path: Path, frame: pd.DataFrame) -> dict[str, Any]:
    manifest = {
        "dataset": "Bike Sharing",
        "source_url": SOURCE_URL,
        "doi": SOURCE_DOI,
        "citation": (
            "Fanaee-T, H. (2013). Bike Sharing [Dataset]. UCI Machine Learning "
            "Repository."
        ),
        "license": "Creative Commons Attribution 4.0 International (CC BY 4.0)",
        "archive_bytes": path.stat().st_size,
        "archive_sha256": sha256_file(path),
        "expected_sha256": SOURCE_SHA256,
        "hourly_member": SOURCE_MEMBER,
        "rows": len(frame),
        "catalog_listed_rows": CATALOG_LISTED_ROWS,
        "timestamp_start": frame[TIMESTAMP].min().isoformat(),
        "timestamp_end": frame[TIMESTAMP].max().isoformat(),
    }
    (RAW_DIR.parent / "source_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    return manifest
