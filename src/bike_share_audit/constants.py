"""Pinned source snapshot and modeling contract."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw"
REPORTS_DIR = ROOT / "reports"
SOURCE_URL = (
    "https://archive.ics.uci.edu/static/public/275/bike%2Bsharing%2Bdataset.zip"
)
SOURCE_SHA256 = "b70182d0d0508e9abbb79306ce5c0cec34869000f8220175ac83d11dbe845401"
SOURCE_BYTES = 279_992
ARCHIVE_EXPECTED_ROWS = 17_379
CATALOG_LISTED_ROWS = 17_389
SOURCE_MEMBER = "hour.csv"
SOURCE_DOI = "10.24432/C5W894"
TARGET = "cnt"
COMPONENT_TARGETS = ["casual", "registered"]
SOURCE_ID = "instant"
TIMESTAMP = "timestamp"
CALENDAR_FEATURES = [
    "hour_sin",
    "hour_cos",
    "weekday_sin",
    "weekday_cos",
    "month_sin",
    "month_cos",
    "year",
    "holiday",
    "workingday",
]
LAG_FEATURES = ["lag_1", "lag_24", "lag_168", "mean_24", "mean_168"]
FEATURES = [*CALENDAR_FEATURES, *LAG_FEATURES]
RANDOM_STATE = 2026
