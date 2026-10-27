"""Read-only API benchmark baseline for Rapid Fire endpoints and fresh_deck selection.

Usage:
  python /app/backend/tests/perf_api_benchmark.py --label before
  python /app/backend/tests/perf_api_benchmark.py --label after

Outputs:
  /app/test_reports/api_speed_<label>.json
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

ROOT = Path("/app")
BACKEND_DIR = ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

BACKEND_ENV = ROOT / "backend" / ".env"
FRONTEND_ENV = ROOT / "frontend" / ".env"
PORTRAIT_REPORT = ROOT / "backend" / "rapidfire" / "portrait_cleanup_report.json"
OUTPUT_DIR = ROOT / "test_reports"


def load_env() -> None:
    load_dotenv(BACKEND_ENV)
    load_dotenv(FRONTEND_ENV)


def parse_frontend_env_value(key: str) -> str | None:
    if not FRONTEND_ENV.exists():
        return None
    for line in FRONTEND_ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == key:
            return v.strip().strip('"').strip("'")
    return None


def stable_hash(data: Any) -> str:
    # Keep identical hashing style to existing guard scripts for direct comparability.
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode("utf-8")).hexdigest()


def percentile_sorted(values: list[float], p: float) -> float:
    if not values:
        return 0.0
    if len(values) == 1:
        return values[0]
    idx = max(0, min(len(values) - 1, int(round((p / 100) * (len(values) - 1)))))
    return values[idx]


def summarize(samples: list[dict[str, Any]]) -> dict[str, Any]:
    durations = sorted(s["duration_ms"] for s in samples)
    return {
        "n": len(samples),
        "p50_ms": round(statistics.median(durations), 3) if durations else None,
        "p95_ms": round(percentile_sorted(durations, 95), 3) if durations else None,
        "min_ms": round(min(durations), 3) if durations else None,
        "max_ms": round(max(durations), 3) if durations else None,
    }


def normalize_prompt(prompt: str) -> str:
    return re.sub(r"\s+", " ", prompt.strip().casefold())


def protected_snapshot(client: AsyncIOMotorClient, db_name: str) -> dict[str, Any]:
    # Sync helper called through to_thread wrapper.
    from pymongo import MongoClient  # local import to keep benchmark deps minimal

    mongo_url = os.environ["MONGO_URL"].strip().strip('"')
    sync_client = MongoClient(mongo_url)
    try:
        db = sync_client[db_name]
        profiles = list(db.rf_profiles.find({}, {"_id": 0}).sort("uid", 1))
        fields = ("uid", "coins", "owned", "equipped", "avatar", "freezes")
        wallet_ownership = stable_hash([{k: p[k] for k in fields if k in p} for p in profiles])
        neet_profiles = [{p.get("uid"): (p.get("exam_stats", {}) or {}).get("NEET")} for p in profiles]
        return {
            "profiles": len(profiles),
            "coins_sum": sum(int(p.get("coins") or 0) for p in profiles),
            "wallet_ownership": wallet_ownership,
            "neet_profile_stats": stable_hash(neet_profiles),
        }
    finally:
        sync_client.close()


async def benchmark_fresh_deck(db, n: int = 15, count: int = 30) -> dict[str, Any]:
    from rapid_deck import fresh_deck

    # Warm-up call for DB/cache path.
    _ = await fresh_deck(db, "JEE", "Physics", None, count)

    samples: list[dict[str, Any]] = []
    for i in range(n):
        t0 = time.perf_counter()
        cards = await fresh_deck(db, "JEE", "Physics", None, count)
        duration_ms = (time.perf_counter() - t0) * 1000

        prompts = [normalize_prompt(c.get("prompt", "")) for c in cards]
        uniq = len(set(prompts))
        samples.append(
            {
                "run": i + 1,
                "duration_ms": round(duration_ms, 3),
                "card_count": len(cards),
                "unique_prompt_count": uniq,
                "valid_cardcount_30unique": bool(len(cards) == count and uniq == count),
            }
        )

    return {
        "name": "fresh_deck_internal_db_selection",
        "exam": "JEE",
        "subject": "Physics",
        "n": n,
        "warmup_runs": 1,
        "db_reads_per_run": 1,
        "notes": [
            "Warm selection: cached public metadata plus one authoritative indexed read for30cards; cold metadata read separately.",
            "Deck content is randomized by shuffle; payload hash equality is not expected for this section.",
        ],
        "summary": summarize(samples),
        "all_valid_30_unique": all(s["valid_cardcount_30unique"] for s in samples),
        "samples": samples,
    }


async def benchmark_http(client: httpx.AsyncClient, base_url: str, path: str, n: int) -> dict[str, Any]:
    samples: list[dict[str, Any]] = []
    payload_hashes: list[str] = []
    status_counts: dict[str, int] = {}

    for i in range(n):
        t0 = time.perf_counter()
        error = None
        status = None
        size = 0
        payload_hash = None
        timing = cache = wire_bytes = None
        try:
            r = await client.get(base_url.rstrip("/") + path)
            status = r.status_code
            timing, cache, wire_bytes = r.headers.get('server-timing'), r.headers.get('x-cache'), r.headers.get('content-length')
            size = len(r.content)
            payload_hash = hashlib.sha256(r.content).hexdigest()
            payload_hashes.append(payload_hash)
            status_counts[str(status)] = status_counts.get(str(status), 0) + 1
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"
            status_counts[type(exc).__name__] = status_counts.get(type(exc).__name__, 0) + 1

        duration_ms = (time.perf_counter() - t0) * 1000
        samples.append(
            {
                "run": i + 1,
                "duration_ms": round(duration_ms, 3),
                "status": status,
                "size_bytes": size,
                "payload_hash": payload_hash,
                "error": error,
                "server_timing": timing, "cache": cache, "wire_content_length": wire_bytes,
            }
        )

    successful = [s for s in samples if isinstance(s.get("status"), int)]
    result = {
        "path": path,
        "n": n,
        "summary": summarize(samples),
        "status_counts": status_counts,
        "samples": samples,
        "successful_sample_count": len(successful),
        "payload_hash_unique_count": len(set(payload_hashes)),
    }
    if payload_hashes:
        result["payload_hash_first"] = payload_hashes[0]
    return result


async def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only RF baseline benchmark")
    parser.add_argument("--label", default="before", help="Output suffix label, e.g., before/after")
    parser.add_argument("--internal-base-url", default="http://localhost:8001", help="Internal backend base URL")
    args = parser.parse_args()

    load_env()
    mongo_url = os.environ["MONGO_URL"].strip().strip('"')
    db_name = os.environ["DB_NAME"].strip().strip('"')
    public_base = os.environ.get("EXPO_PUBLIC_BACKEND_URL") or parse_frontend_env_value("EXPO_PUBLIC_BACKEND_URL")
    if not public_base:
        raise RuntimeError("EXPO_PUBLIC_BACKEND_URL is required in frontend/.env")
    public_base = public_base.rstrip("/")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / f"api_speed_{args.label}.json"

    client = AsyncIOMotorClient(mongo_url)
    db = client[db_name]

    try:
        # Read-only protected snapshot before benchmark
        protected_before = await asyncio.to_thread(protected_snapshot, client, db_name)

        # Internal function benchmark (no server startup)
        fresh_deck_result = await benchmark_fresh_deck(db, n=15, count=30)

        # HTTP benchmarks
        endpoints = [
            "/api/rf/catalog?exam=JEE",
            "/api/rf/cards?exam=JEE&subject=Physics&page=1&limit=20",
        ]

        timeout = httpx.Timeout(30.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as http_client:
            local_results = []
            for ep in endpoints:
                local_results.append(await benchmark_http(http_client, args.internal_base_url, ep, n=10))

            external_results = []
            for ep in endpoints:
                external_results.append(await benchmark_http(http_client, public_base, ep, n=8))

        protected_after = await asyncio.to_thread(protected_snapshot, client, db_name)
        reference_protected_after = {}
        if PORTRAIT_REPORT.exists():
            try:
                reference_protected_after = json.loads(PORTRAIT_REPORT.read_text(encoding="utf-8")).get("protected_after", {})
            except Exception:  # noqa: BLE001
                reference_protected_after = {}

        report = {
            "label": args.label,
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "scope": "readonly_actual_api_measurements",
            "targets": {
                "local_internal": {
                    "name": "internal_service",
                    "base_url_redacted": "INTERNAL_SERVICE_URL_REDACTED",
                },
                "external_preview": {
                    "name": "public_preview",
                    "base_public_url": public_base,
                },
            },
            "benchmarks": {
                "fresh_deck": fresh_deck_result,
                "public_api_local_internal_n10": local_results,
                "public_api_external_preview_n8": external_results,
            },
            "protected_rf_snapshot": {
                "reference_from_portrait_cleanup_report": {
                    k: reference_protected_after.get(k)
                    for k in ("profiles", "coins_sum", "wallet_ownership", "neet_profile_stats")
                    if k in reference_protected_after
                },
                "before": protected_before,
                "after": protected_after,
                "unchanged": protected_before == protected_after,
            },
            "notes": [
                "Read-only benchmark: no create/update/delete actions.",
                "No canonical auth writes attempted.",
                "API hashes are provided to compare before/after implementation with identical payload expectations.",
            ],
        }

        out_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(f"Wrote benchmark report: {out_path}")
    finally:
        client.close()
        from metadata_cache import metadata_cache
        await metadata_cache.close()


if __name__ == "__main__":
    asyncio.run(main())
