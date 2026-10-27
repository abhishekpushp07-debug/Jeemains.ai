"""Response timing with no body buffering, identity logging or public diagnostics."""
import time
from starlette.datastructures import MutableHeaders
from starlette.middleware.gzip import GZipMiddleware


class AssetAwareCompression:
    """Don't spend CPU recompressing original PNG/WebP/JPEG image bytes."""
    def __init__(self, app, **kwargs):
        self.app, self.compressed = app, GZipMiddleware(app, **kwargs)

    async def __call__(self, scope, receive, send):
        path = scope.get('path', '')
        original_image = '/asset/' in path or path.startswith(('/api/brand/', '/api/avatars/'))
        await (self.app if original_image else self.compressed)(scope, receive, send)


class ServerTiming:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        started = time.perf_counter()

        async def timed_send(message):
            if message['type'] == 'http.response.start':
                headers = MutableHeaders(scope=message)
                headers['Server-Timing'] = f'app;dur={(time.perf_counter() - started) * 1000:.2f}'
            await send(message)

        await self.app(scope, receive, timed_send)