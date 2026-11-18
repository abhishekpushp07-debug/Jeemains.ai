"""The student's own internet address, as far as it can be trusted.

Three proxies stand in front of this server and each one appends the address it received the request from to
X-Forwarded-For: the CDN edge (Cloudflare) adds the student, the load balancer adds the edge, the ingress adds the
load balancer. Measured on the preview (June 2026): "<student>, 104.22.x.x (edge), 34.160.127.70 (balancer)".
So the LAST entry is the same balancer for every student, and the student is the entry TRUSTED_PROXY_HOPS (2) places
before it. Entries further left are written by the caller and can be forged."""
import os

from starlette.requests import Request

HOPS = int(os.environ.get("TRUSTED_PROXY_HOPS", "2"))


def client_ip(request: Request) -> str:
    chain = [p.strip() for p in request.headers.get("x-forwarded-for", "").split(",") if p.strip()]
    if len(chain) > HOPS:
        return chain[-(HOPS + 1)]
    # Called without the full proxy chain (on this machine, or a direct test): the nearest address there is.
    return chain[-1] if chain else (request.client.host if request.client else "")
