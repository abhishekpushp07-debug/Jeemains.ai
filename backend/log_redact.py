"""PINs, passwords, tokens, cookies and phone numbers never reach a log line or an error answer (Phase 3, Level 7).

- Every log record (ours, uvicorn's, httpx's, aiohttp's, tracebacks included) passes a filter on the log handlers that
  masks them before the line is written.
- A request that fails validation (422) answers which field was wrong and why, never the value that was sent: FastAPI's
  default answer echoes the input (for the Forgot PIN form that was the new PIN itself)."""
import logging
import re

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

SECRET_NAMES = r"pin|new_pin|old_pin|confirm_pin|password|passcode|otp|access_token|refresh_token|token|access_cookie|jl_access|jl_refresh"
RULES = (
    (re.compile(r'(["\']?\b(?:' + SECRET_NAMES + r')\b["\']?\s*[:=]\s*)("[^"]*"|\'[^\']*\'|[^\s,;&}\]]+)', re.I), r"\1***"),
    (re.compile(r"(\b(?:cookie|set-cookie|authorization)\b[\"']?\s*[:=]\s*)[^\n]+", re.I), r"\1***"),
    (re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.I), "Bearer ***"),
    (re.compile(r"(?<![\d.])(?:\+?91[\s-]?)?[6-9]\d{9}(?![\d.])"), "<phone>"),
)


def redact(text: str) -> str:
    for pattern, replacement in RULES:
        text = pattern.sub(replacement, text)
    return text


class Redact(logging.Filter):
    _formatter = logging.Formatter()

    def filter(self, record: logging.LogRecord) -> bool:
        try:
            message = record.getMessage()
        except Exception:  # noqa: BLE001 - a broken format string is logged as it is
            return True
        clean = redact(message)
        if clean != message:
            record.msg, record.args = clean, None
        if record.exc_info and not record.exc_text:
            record.exc_text = redact(self._formatter.formatException(record.exc_info))
        return True


def install():
    """On every handler of the root and uvicorn loggers (filters on handlers also see records of child loggers)."""
    shared = next((f for h in logging.getLogger().handlers for f in h.filters if isinstance(f, Redact)), None) or Redact()
    for name in ("", "uvicorn", "uvicorn.error", "uvicorn.access"):
        for handler in logging.getLogger(name).handlers:
            if not any(isinstance(f, Redact) for f in handler.filters):
                handler.addFilter(shared)


async def validation_error(_: Request, exc: RequestValidationError):
    errors = [{k: v for k, v in e.items() if k in ("type", "loc", "msg")} for e in exc.errors()]
    return JSONResponse({"detail": errors}, status_code=422, headers={"Cache-Control": "no-store"})
