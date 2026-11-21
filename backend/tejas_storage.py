"""Private platform object storage. All authorization is performed by API callers."""

import os, threading, time, hashlib
import requests
from tejas.cache import ByteCache

_source_cache = ByteCache(64 * 1024 * 1024)
_source_locks = [threading.Lock() for _ in range(32)]


def source_lock(path):
    return _source_locks[int.from_bytes(hashlib.sha256(path.encode()).digest()[:4], 'big') % len(_source_locks)]

BASE = (
    os.environ.get("INTEGRATION_PROXY_URL") or ""
).strip() or "https://integrations.emergentagent.com"
URL = BASE.rstrip("/") + "/objstore/api/v1/storage"
_key = None
_lock = threading.Lock()


class StorageError(Exception):
    pass


def init_storage(force=False):
    global _key
    with _lock:
        if _key and not force:
            return _key
        r = requests.post(
            URL + "/init",
            json={"emergent_key": os.environ.get("EMERGENT_LLM_KEY")},
            timeout=30,
        )
        if r.status_code != 200:
            raise StorageError(
                f"Private storage initialization unavailable ({r.status_code}). Check account storage access."
            )
        _key = r.json()["storage_key"]
        return _key


def request(method, path, data=None, content_type=None):
    # A storage hiccup (5xx) is retried with growing waits instead of failing a whole book on the first try.
    for attempt in range(4):
        try:
            r = requests.request(
                method,
                URL + "/objects/" + path,
                headers={
                    "X-Storage-Key": init_storage(),
                    "Content-Type": content_type or "application/octet-stream",
                },
                data=data,
                timeout=120,
            )
        except requests.RequestException:
            if attempt == 3:
                raise StorageError(
                    "Private storage connection interrupted. Retry this operation."
                )
            time.sleep(attempt + 1)
            continue
        if r.ok:
            return r
        if r.status_code in (401, 403, 404) and attempt == 0:
            init_storage(force=True)
            continue
        if r.status_code in (500, 502, 503, 504) and attempt < 3:
            time.sleep(2 ** attempt)
            continue
        raise StorageError(
            f"Private storage unavailable ({r.status_code}). Retry later or check account storage permissions and quota."
        )
    raise StorageError("Private storage could not complete this request.")


def put_object(path, data, content_type="application/pdf"):
    with source_lock(path):
        result = request('PUT', path, data, content_type).json()['path']
        _source_cache.remove(path)
        return result


def get_object(path):
    cached = _source_cache.get(path)
    if cached is not None:
        return cached
    with source_lock(path):
        cached = _source_cache.get(path)
        if cached is not None:
            return cached
        return _source_cache.put(path, request('GET', path).content)
