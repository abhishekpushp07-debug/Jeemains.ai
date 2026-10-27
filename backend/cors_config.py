"""Credentialed CORS uses configured app/site origins, never a wildcard."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values, load_dotenv

load_dotenv()


def allowed_origins():
    configured = os.environ.get('CORS_ORIGINS', '')
    try:
        extra = json.loads(configured) if configured.lstrip().startswith('[') else configured.split(',')
    except ValueError:
        extra = []
    candidates = list(extra) if isinstance(extra, list) else []
    candidates += [os.environ.get(key, '') for key in ('APP_URL', 'JEELIVE_API', 'EXPO_PUBLIC_BACKEND_URL', 'EXPO_PACKAGER_PROXY_URL')]
    frontend = Path(__file__).parent.parent / 'frontend' / '.env'
    if frontend.exists():
        env = dotenv_values(frontend)
        candidates += [env.get(key, '') for key in ('EXPO_PUBLIC_BACKEND_URL', 'EXPO_PACKAGER_PROXY_URL')]
    origins = set()
    for value in candidates:
        if not isinstance(value, str):
            continue
        try:
            parsed = urlsplit(value.strip())
            port = parsed.port
        except ValueError:
            continue
        if parsed.scheme in ('http', 'https') and parsed.hostname and not parsed.username and not parsed.password and '*' not in parsed.netloc:
            host = parsed.hostname.lower()
            host = f'[{host}]' if ':' in host else host
            if port and (parsed.scheme, port) not in (('http', 80), ('https', 443)):
                host += f':{port}'
            origins.add(f'{parsed.scheme}://{host}')
    return sorted(origins)