"""Build aggregate forecasts and quality reports from the pinned source."""

from __future__ import annotations

import json

from bike_share_audit.constants import RAW_DIR
from bike_share_audit.data import (
    data_quality_report,
    parse_archive,
    write_source_manifest,
)
from bike_share_audit.evaluation import build_report


def main() -> None:
    archive = RAW_DIR / "bike-sharing.zip"
    frame = parse_archive(archive)
    quality = data_quality_report(frame, archive)
    manifest = write_source_manifest(archive, frame)
    summary = build_report(frame, quality)
    print(
        json.dumps(
            {
                "rows": len(frame),
                "archive_sha256": manifest["archive_sha256"],
                "model_rows": len(summary["metrics"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
