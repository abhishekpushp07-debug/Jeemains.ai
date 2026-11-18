"""The website (jeelive.ai) client: one pooled aiohttp session per process, bounded read-only retry.
Never replay a potentially committed write.

aiohttp instead of httpx: under load httpx spent ~25% of the proxy's CPU in its connection-pool bookkeeping; the same
proxy on aiohttp served 6.7x more requests per CPU-second (tools/proto_proxy.py, memory/AUDIT_2026_06.md L1).
"""
import asyncio
import json
import logging
import os
import time

import aiohttp

logger = logging.getLogger("canonical_transport")
TRANSIENT_READ_STATUS = {408, 500, 502, 503, 504, 520, 522, 524}
UpstreamError = (aiohttp.ClientError, asyncio.TimeoutError)


class Upstream:
    """A fully read website answer: status, headers (case-insensitive, repeated Set-Cookie kept) and body."""
    __slots__ = ("status_code", "headers", "content")

    def __init__(self, status_code, headers, content):
        self.status_code, self.headers, self.content = status_code, headers, content

    @property
    def is_success(self):
        return 200 <= self.status_code < 300

    def json(self):
        return json.loads(self.content)


def make_client() -> aiohttp.ClientSession:
    # No cookie jar on the shared session: every student's cookies come from their own jar (no cross-user leak).
    return aiohttp.ClientSession(
        connector=aiohttp.TCPConnector(limit=int(os.environ.get("JL_MAX_CONNECTIONS", "400")), keepalive_timeout=45, ttl_dns_cache=300),
        cookie_jar=aiohttp.DummyCookieJar(), timeout=aiohttp.ClientTimeout(total=None))


async def canonical_request(client, method, url, *, path, params, body, headers):
    category = "asset" if "/asset/" in path else "auth" if path.startswith("auth/") else "academic"
    readonly = method in {"GET", "HEAD"} and (category != "auth" or path == "auth/me")
    deadline = time.monotonic() + (22 if category == "asset" else 28)
    query = list(params.multi_items()) if hasattr(params, "multi_items") else params
    for attempt in range(2 if readonly else 1):
        remaining = max(0.1, deadline - time.monotonic())
        timeout = aiohttp.ClientTimeout(total=remaining, connect=min(4, remaining), sock_read=min(10 if readonly else 24, remaining))
        try:
            async with client.request(method, url, params=query, data=body, headers=headers, timeout=timeout, allow_redirects=False) as r:
                response = Upstream(r.status, r.headers, await r.read())
            if response.status_code in TRANSIENT_READ_STATUS:
                logger.warning("canonical_response method=%s category=%s status=%s attempt=%s", method, category, response.status_code, attempt + 1)
                hint = response.headers.get("retry-after", "")
                try:
                    pause = max(0.25, float(hint)) if hint else 0.25
                except ValueError:
                    return response  # An HTTP-date policy is left to the client, not ignored.
                if readonly and attempt == 0 and pause < min(2, deadline - time.monotonic() - 1):
                    await asyncio.sleep(pause)
                    continue
            return response
        except UpstreamError as error:
            # Never log the path, SID, body, cookies or the exception's private URL.
            logger.warning("canonical_transport_error method=%s category=%s error=%s attempt=%s", method, category, type(error).__name__, attempt + 1)
            if readonly and attempt == 0 and deadline - time.monotonic() > 1:
                await asyncio.sleep(0.25)
                continue
            raise
