"""Fetch and checksum the official UCI Bike Sharing archive."""

from __future__ import annotations

import hashlib
import urllib.request

from bike_share_audit.constants import RAW_DIR, SOURCE_BYTES, SOURCE_SHA256, SOURCE_URL


def fetch_source() -> dict[str, str | int]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        SOURCE_URL,
        headers={"User-Agent": "capital-bike-share-demand-audit/0.1.0"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if len(payload) != SOURCE_BYTES or digest != SOURCE_SHA256:
        raise ValueError(f"UCI source mismatch: {len(payload)} bytes, SHA-256 {digest}")
    path = RAW_DIR / "bike-sharing.zip"
    path.write_bytes(payload)
    return {"path": str(path), "bytes": len(payload), "sha256": digest}


if __name__ == "__main__":
    print(fetch_source())
