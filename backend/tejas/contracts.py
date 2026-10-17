"""Stable API v1 envelopes and request correlation. Binary assets are never JSON-wrapped."""

from contextvars import ContextVar
from fastapi.responses import JSONResponse

request_id = ContextVar("request_id", default="")


class EnvelopeResponse(JSONResponse):
    def render(self, content):
        if isinstance(content, dict) and content.get("_enveloped"):
            content.pop("_enveloped", None)
            return super().render(content)
        return super().render(
            {
                "data": content,
                "error": None,
                "meta": {"api_version": "1", "request_id": request_id.get()},
            }
        )


def error_response(message, status, code="request_failed"):
    return EnvelopeResponse(
        {
            "_enveloped": True,
            "data": None,
            "error": {"code": code, "message": message},
            "meta": {"api_version": "1", "request_id": request_id.get()},
        },
        status_code=status,
    )
