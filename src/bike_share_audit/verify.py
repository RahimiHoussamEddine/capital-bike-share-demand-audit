"""Check source provenance, lock closure, and aggregate report safety."""

from __future__ import annotations

import importlib.metadata
import json
import re
from pathlib import Path

import pandas as pd

from bike_share_audit.constants import (
    ARCHIVE_EXPECTED_ROWS,
    COMPONENT_TARGETS,
    RAW_DIR,
    REPORTS_DIR,
    SOURCE_BYTES,
    SOURCE_ID,
    SOURCE_SHA256,
    TARGET,
)
from bike_share_audit.data import parse_archive, sha256_file

EXPECTED_REPORTS = {
    "RESULTS.md",
    "data_quality.json",
    "hourly_error.csv",
    "model_metrics.csv",
    "monthly_metrics.csv",
    "split_summary.csv",
    "summary.json",
}
DISALLOWED_COLUMNS = {
    SOURCE_ID,
    TARGET,
    *COMPONENT_TARGETS,
    "prediction",
    "forecast",
    "y_pred",
}


def _verify_lock(root: Path) -> int:
    lock = root / "requirements.lock"
    if not lock.is_file():
        raise ValueError("requirements.lock is missing")
    count = 0
    for line in lock.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z0-9_.-]+)==([A-Za-z0-9_.+!-]+)", line.strip())
        if match is None:
            raise ValueError(f"Unpinned lock entry: {line!r}")
        name, expected = match.groups()
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError as error:
            raise ValueError(f"Locked distribution is not installed: {name}") from error
        if actual != expected:
            raise ValueError(f"Version mismatch for {name}: {expected} != {actual}")
        count += 1
    if count < 20:
        raise ValueError(f"Lock contains too few distributions: {count}")
    return count


def verify(root: Path | None = None) -> dict[str, int | str]:
    root = root or Path(__file__).resolve().parents[2]
    archive = RAW_DIR / "bike-sharing.zip"
    if archive.stat().st_size != SOURCE_BYTES or sha256_file(archive) != SOURCE_SHA256:
        raise ValueError("Raw archive differs from the pinned UCI source")
    frame = parse_archive(archive)
    manifest = json.loads((RAW_DIR.parent / "source_manifest.json").read_text())
    if manifest["archive_sha256"] != SOURCE_SHA256 or manifest["rows"] != len(frame):
        raise ValueError("Source manifest does not match the downloaded archive")

    actual_reports = {path.name for path in REPORTS_DIR.iterdir() if path.is_file()}
    if actual_reports != EXPECTED_REPORTS:
        raise ValueError(
            f"Unexpected report files: {sorted(actual_reports ^ EXPECTED_REPORTS)}"
        )
    summary = json.loads((REPORTS_DIR / "summary.json").read_text(encoding="utf-8"))
    if (
        summary["rows"] != ARCHIVE_EXPECTED_ROWS
        or summary["target_components_used_as_features"]
    ):
        raise ValueError("Summary row count or target-component exclusion is invalid")
    if summary["catalog_archive_row_count_difference"] != 10:
        raise ValueError("Catalog/archive row-count discrepancy was not recorded")
    if summary["same_hour_weather_used_as_feature"]:
        raise ValueError("Same-hour weather must remain excluded")
    if summary["row_level_forecasts_published"]:
        raise ValueError("Row-level forecasts must not be published")
    if not frame[TARGET].equals(frame[COMPONENT_TARGETS].sum(axis=1)):
        raise ValueError("UCI target decomposition check failed")

    tables = {
        "model_metrics": pd.read_csv(REPORTS_DIR / "model_metrics.csv"),
        "hourly_error": pd.read_csv(REPORTS_DIR / "hourly_error.csv"),
        "monthly_metrics": pd.read_csv(REPORTS_DIR / "monthly_metrics.csv"),
        "split_summary": pd.read_csv(REPORTS_DIR / "split_summary.csv"),
    }
    for name, table in tables.items():
        exposed = DISALLOWED_COLUMNS.intersection(table.columns)
        if exposed:
            raise ValueError(f"{name} expose disallowed columns: {sorted(exposed)}")
    if len(tables["model_metrics"]) != 5 or len(tables["hourly_error"]) != 120:
        raise ValueError("Model or hour-of-day report has an unexpected row count")
    if len(tables["split_summary"]) != 2 or len(tables["monthly_metrics"]) < 5:
        raise ValueError("Split/monthly report row count is invalid")
    lock_count = _verify_lock(root)
    return {
        "source_sha256": SOURCE_SHA256,
        "source_bytes": SOURCE_BYTES,
        "source_rows": len(frame),
        "model_rows": len(tables["model_metrics"]),
        "hourly_aggregate_rows": len(tables["hourly_error"]),
        "locked_distributions": lock_count,
    }


def main() -> None:
    print(json.dumps(verify(), indent=2))


if __name__ == "__main__":
    main()
