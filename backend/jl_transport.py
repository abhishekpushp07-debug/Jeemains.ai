"""Bounded, read-only upstream recovery. Never replay a potentially committed write."""
import asyncio
import logging
import time

import httpx

logger = logging.getLogger("canonical_transport")
TRANSIENT_READ_STATUS = {408, 500, 502, 503, 504, 520, 522, 524}


async def canonical_request(client, method, url, *, path, params, body, headers):
    category = "asset" if "/asset/" in path else "auth" if path.startswith("auth/") else "academic"
    readonly = method in {"GET", "HEAD"} and (category != "auth" or path == "auth/me")
    deadline = time.monotonic() + (22 if category == "asset" else 28)
    for attempt in range(2 if readonly else 1):
        remaining = max(0.1, deadline - time.monotonic())
        try:
            request = client.request(method, url, params=params, content=body, headers=headers,
                                     timeout=httpx.Timeout(connect=min(4, remaining), read=min(10 if readonly else 24, remaining), write=min(10, remaining), pool=min(3, remaining)))
            response = await asyncio.wait_for(request, timeout=remaining)
            if response.status_code in TRANSIENT_READ_STATUS:
                logger.warning("canonical_response method=%s category=%s status=%s attempt=%s", method, category, response.status_code, attempt + 1)
                hint = response.headers.get("retry-after", "")
                try:
                    pause = max(0.25, float(hint)) if hint else 0.25
                except ValueError:
                    return response  # An HTTP-date policy is left to the client, not ignored.
                if readonly and attempt == 0 and pause < min(2, deadline - time.monotonic() - 1):
                    await response.aclose()
                    await asyncio.sleep(pause)
                    continue
            return response
        except (httpx.RequestError, asyncio.TimeoutError) as error:
            # Never log the path, SID, body, cookies or the exception's private URL.
            logger.warning("canonical_transport_error method=%s category=%s error=%s attempt=%s", method, category, type(error).__name__, attempt + 1)
            if readonly and attempt == 0 and deadline - time.monotonic() > 1:
                await asyncio.sleep(0.25)
                continue
            raise