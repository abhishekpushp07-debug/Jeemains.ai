"""Baseline benchmark report verification (read-only)."""

import json
from pathlib import Path


REPORT = Path("/app/test_reports/api_speed_before.json")


def test_api_speed_before_report_exists_and_is_well_formed():
    assert REPORT.exists(), "Expected baseline report at /app/test_reports/api_speed_before.json"
    data = json.loads(REPORT.read_text(encoding="utf-8"))

    assert data.get("label") == "before"
    assert data.get("benchmarks", {}).get("fresh_deck", {}).get("n") == 15
    assert data.get("benchmarks", {}).get("fresh_deck", {}).get("all_valid_30_unique") is True

    local = data.get("benchmarks", {}).get("public_api_local_internal_n10", [])
    external = data.get("benchmarks", {}).get("public_api_external_preview_n8", [])
    assert len(local) == 2
    assert len(external) == 2

    for section, expected_n in ((local, 10), (external, 8)):
        for endpoint in section:
            assert endpoint.get("n") == expected_n
            assert endpoint.get("status_counts", {}).get("200", 0) == expected_n
            assert endpoint.get("payload_hash_unique_count") == 1

    guard = data.get("protected_rf_snapshot", {})
    assert guard.get("unchanged") is True
