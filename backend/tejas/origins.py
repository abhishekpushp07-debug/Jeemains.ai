import logging
from urllib.parse import urlsplit
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)


def normalise_origin(value):
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError('Origin cannot contain control characters.')
    raw = value.strip()
    if not raw or any(c.isspace() or ord(c) < 32 for c in raw) or any(c in raw for c in ('*', '\\', '?', '#')):
        raise ValueError('Use an explicit HTTP(S) origin.')
    parsed = urlsplit(raw)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username is not None or parsed.password is not None or parsed.path not in ('', '/'):
        raise ValueError('Origin must contain only a scheme, hostname and optional port.')
    port = parsed.port
    if port is not None and not 1 <= port <= 65535:
        raise ValueError('Invalid origin port.')
    host = parsed.hostname.lower()
    if ':' in host:
        host = '[' + host + ']'
    if port is not None and port != {'http': 80, 'https': 443}[parsed.scheme]:
        host += ':' + str(port)
    return parsed.scheme + '://' + host


def configured_origins(frontend_url, additional=None):
    try:
        allowed = [normalise_origin(frontend_url)]
        for value in (additional or '').split(','):
            if not value.strip():
                continue
            if value.strip() == '*':
                logger.warning('Wildcard CORS_ORIGINS ignored; only explicitly configured origins are trusted.')
                continue
            origin = normalise_origin(value)
            if origin not in allowed:
                allowed.append(origin)
        return allowed
    except ValueError as exc:
        raise RuntimeError('FRONTEND_URL and CORS_ORIGINS must contain explicit HTTP(S) origins without paths, credentials or wildcard hosts.') from exc


def origin_allowed(value, allowed):
    try:
        return normalise_origin(value) in allowed
    except (ValueError, TypeError):
        return False


class ExplicitOriginCORS(CORSMiddleware):
    def is_allowed_origin(self, origin):
        return origin_allowed(origin, self.allow_origins)
