"""21 Nov 2026 live incident: the website's origin answered 520 for ~1 minute and the app showed Cloudflare's text.
The proxy now hands the app one plain line (503 website_unavailable + Retry-After) for the website's own 5xx trouble,
and keeps the website's plain 500/503 messages and every non-5xx answer as they are."""
import json

from jl_transport import Upstream
from multidict import CIMultiDict

import jl_proxy

CF_520 = ("The origin web server sent a response that Cloudflare could not parse. This may indicate the origin returned an "
          "empty response, malformed HTTP headers, or an otherwise invalid response.")


def up(status, body, ctype="application/json"):
    content = body if isinstance(body, bytes) else json.dumps(body).encode()
    return Upstream(status, CIMultiDict({"content-type": ctype}), content)


def test_cloudflare_and_gateway_errors_are_replaced():
    assert jl_proxy.website_trouble(up(520, {"data": None, "error": {"code": "http_520", "message": CF_520}}))
    assert jl_proxy.website_trouble(up(520, b"<html><title>520</title></html>", "text/html"))
    for status in (502, 504, 521, 522, 524, 530):
        assert jl_proxy.website_trouble(up(status, b"", "text/plain"))
    assert jl_proxy.website_trouble(up(503, b"<html>busy</html>", "text/html"))
    assert jl_proxy.website_trouble(up(500, {"detail": "Internal Server Error"}))
    assert jl_proxy.website_trouble(up(503, {"error": {"message": ""}}))


def test_plain_answers_pass_through():
    assert not jl_proxy.website_trouble(up(200, {"data": {"ok": True}}))
    assert not jl_proxy.website_trouble(up(401, {"error": {"message": "Sign in again with your current credentials. Saved work is retained."}}))
    assert not jl_proxy.website_trouble(up(409, {"error": {"message": "This attempt is already submitted."}}))
    assert not jl_proxy.website_trouble(up(503, {"error": {"message": "Results are being prepared. Please check again shortly."}}))
    assert not jl_proxy.website_trouble(up(500, {"error": {"message": "Grading is still running. Your answers are safe."}}))


def test_plain_line_never_mentions_the_server():
    assert "cloudflare" not in jl_proxy.WEBSITE_BUSY.lower() and "safe" in jl_proxy.WEBSITE_BUSY
