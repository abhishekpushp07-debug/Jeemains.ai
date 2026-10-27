"""Iteration 46 probe: Redis namespace safety + controlled outage fail-open checks."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from redis import Redis


load_dotenv('/app/frontend/.env')
BASE_URL = (os.environ.get('EXPO_PUBLIC_BACKEND_URL') or '').rstrip('/')


def run(cmd: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, check=False, text=True, capture_output=True)


def endpoint(path: str) -> requests.Response:
    return requests.get(f"{BASE_URL}{path}", timeout=20)


def main() -> int:
    if not BASE_URL:
        print('Missing EXPO_PUBLIC_BACKEND_URL')
        return 2

    cfg = json.loads(Path('/app/backend/redis_runtime.json').read_text(encoding='utf-8'))
    prefix = cfg['namespace'] + ':'
    sock = cfg['socket_path']
    r = Redis(unix_socket_path=sock, decode_responses=True)

    # Warm public metadata cache keys.
    catalog = endpoint('/api/rf/catalog?exam=JEE')
    cards = endpoint('/api/rf/cards?exam=JEE&subject=Physics&page=1&limit=20')
    print('warm_catalog', catalog.status_code, catalog.headers.get('X-Cache'))
    print('warm_cards', cards.status_code, cards.headers.get('X-Cache'))
    if catalog.status_code != 200 or cards.status_code != 200:
        print('Warmup failed; aborting probe.')
        return 1

    # Namespace scan + privacy checks.
    keys = [k.decode() if isinstance(k, bytes) else k for k in r.scan_iter(match=prefix + '*', count=200)]
    print('namespace_key_count', len(keys))
    forbidden_key_tokens = ('auth', 'cookie', 'wallet', 'coin', 'attempt', 'history', 'canonicalresponse')
    bad_keys = [k for k in keys if any(tok in k.lower() for tok in forbidden_key_tokens)]
    print('forbidden_named_keys', bad_keys)

    bad_payload_hits = []
    for key in keys[:20]:
        raw = r.get(key)
        if raw is None:
            continue
        text = raw if isinstance(raw, str) else raw.decode(errors='ignore')
        lowered = text.lower()
        if any(token in lowered for token in ('"answer":', '"explain":', '"formula":', 'access_token', 'set-cookie')):
            bad_payload_hits.append(key)
    print('forbidden_payload_keys', bad_payload_hits)

    stop_res = run(['supervisorctl', 'stop', 'jeelive-redis'])
    print('stop_redis_rc', stop_res.returncode)
    print('stop_redis_out', stop_res.stdout.strip())
    if stop_res.stderr.strip():
        print('stop_redis_err', stop_res.stderr.strip())

    fail_open_ok = False
    try:
        time.sleep(0.4)
        # Keep catalog alive check + cold cards variant to avoid L1 masking.
        out_catalog = endpoint('/api/rf/catalog?exam=JEE')
        out_cards = endpoint('/api/rf/cards?exam=JEE&subject=Chemistry&page=2&limit=19')
        print('outage_catalog', out_catalog.status_code, out_catalog.headers.get('X-Cache'))
        print('outage_cards', out_cards.status_code, out_cards.headers.get('X-Cache'))
        fail_open_ok = out_catalog.status_code == 200 and out_cards.status_code == 200
    finally:
        start_res = run(['supervisorctl', 'start', 'jeelive-redis'])
        print('start_redis_rc', start_res.returncode)
        print('start_redis_out', start_res.stdout.strip())
        if start_res.stderr.strip():
            print('start_redis_err', start_res.stderr.strip())
        time.sleep(0.5)

    status_res = run(['supervisorctl', 'status', 'jeelive-redis'])
    print('redis_status', status_res.stdout.strip())

    restarted_catalog = endpoint('/api/rf/catalog?exam=JEE')
    print('post_restart_catalog', restarted_catalog.status_code, restarted_catalog.headers.get('X-Cache'))

    ok = (
        fail_open_ok
        and not bad_keys
        and not bad_payload_hits
        and status_res.returncode in (0, 3)
        and restarted_catalog.status_code == 200
    )
    print('probe_pass', ok)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
