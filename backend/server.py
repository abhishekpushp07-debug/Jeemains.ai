from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")
import os, uuid, time
import tejas.reports  # noqa: F401  fail fast on report syntax errors (it is otherwise imported lazily)
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from starlette.datastructures import MutableHeaders
from fastapi.exceptions import RequestValidationError
from tejas.origins import ExplicitOriginCORS, configured_origins, origin_allowed
from tejas import (
    auth,
    content,
    attempts,
    jobs,
    reviewers,
    phone,
    profiles,
    corrections,
    answers,
    engineering,
    imports,
    competitions,
    reviews,
    chapter_books,
    ai_solutions,
    cohorts,
    smart_imports,
    exam_navigation,
    mock_books,
    mock_solutions,
    manual_solutions,
    question_reports,
    learning_progress,
    my_tests,
    historical_rank,
    bitsat_branches,
    live_series,
    series_streak,
    jee_transfer,
    attempt_status,
    pyq,
    pyq_import,
    students,
    book_imports,
    structure,
    integrity,
    library,
    master,
    written,
    series_admin,
    chapter_split,
    draft_preview,
    qa_cleanup,
    timeline,
    analysis_api,
    names,
    media,
    rank_predictor,
    dreams,
    mission,
)
from tejas.db import indexes, client
from tejas.contracts import EnvelopeResponse, error_response, request_id
from tejas_storage import StorageError


@asynccontextmanager
async def lifespan(app):
    await indexes()
    await auth.seed_owner()
    await structure.seed()
    import asyncio
    asyncio.create_task(library.run_cleanups())
    from tejas.live_window import apply_to_upcoming
    await apply_to_upcoming()
    from tejas.mock_solutions import solutions
    from tejas.db import SafeIndexes
    solutions = SafeIndexes(solutions)
    await solutions.create_index('id', unique=True)
    await solutions.create_index([('state', 1), ('order', 1)])
    await solutions.create_index('set_id')
    yield
    client.close()


app = FastAPI(
    title="jeemains.ai API",
    version="1.0.0",
    lifespan=lifespan,
    default_response_class=EnvelopeResponse,
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)
from tejas.http_limits import JsonBodyLimits
from tejas.safety import ContentSafetyHold
app.add_middleware(JsonBodyLimits, contracts_owner=app)
app.add_middleware(ContentSafetyHold)
from tejas.import_guard import ImportGuard
app.add_middleware(ImportGuard)
from tejas.admission import AdmissionGate
app.add_middleware(AdmissionGate, owner=app)
origins = configured_origins(os.environ['FRONTEND_URL'], os.environ.get('CORS_ORIGINS'))
app.add_middleware(
    ExplicitOriginCORS,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)


class Protections:
    """Pure ASGI (no BaseHTTPMiddleware task hop): request id, cross-origin write guard and security headers."""

    HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "same-origin",
        "Cache-Control": "private, no-store",
        "X-Frame-Options": "DENY",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }
    # Public CDN pictures set their own Cache-Control; anything else on /api/media stays private, no-store.
    MEDIA_HEADERS = {
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "same-origin",
        "X-Frame-Options": "DENY",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }

    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        rid = str(uuid.uuid4())
        ctx = request_id.set(rid)
        started = time.perf_counter()

        sent = False

        async def stamped(message):
            nonlocal sent
            if message["type"] == "http.response.start":
                sent = True
                headers = MutableHeaders(scope=message)
                media = scope["path"].startswith("/api/media/")
                headers.update({**(self.MEDIA_HEADERS if media else self.HEADERS), "X-Request-ID": rid,
                                "Server-Timing": f"app;dur={(time.perf_counter()-started)*1000:.1f}"})
                if media and "cache-control" not in headers:
                    headers["Cache-Control"] = "private, no-store"
            await send(message)

        try:
            origin = next((v.decode("latin-1") for k, v in scope["headers"] if k == b"origin"), None)
            if scope["method"] in ("POST", "PUT", "PATCH", "DELETE") and origin is not None and not origin_allowed(origin, origins):
                return await error_response("Cross-origin write rejected.", 403, "origin_denied")(scope, receive, stamped)
            await self.app(scope, receive, stamped)
        except Exception:
            if not sent:  # keep the {data,error,meta} envelope and headers; the error is re-raised for the server log
                await error_response("Something went wrong on our side. Saved answers are unchanged; please try again.", 500, "server_error")(scope, receive, stamped)
            raise
        finally:
            request_id.reset(ctx)


app.add_middleware(Protections)


@app.exception_handler(HTTPException)
async def http_error(request, exc):
    response = error_response(exc.detail, exc.status_code, "http_" + str(exc.status_code))
    if exc.headers:
        response.headers.update(exc.headers)
    if exc.status_code in (429, 503) and "Retry-After" not in response.headers:
        response.headers["Retry-After"] = "3"
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    return error_response(
        "; ".join(e["msg"] for e in exc.errors()), 422, "validation_error"
    )


@app.exception_handler(StorageError)
async def storage_error(request, exc):
    response = error_response("Private content is temporarily unavailable. Please retry shortly.", 503, "vault_unavailable")
    response.headers["Retry-After"] = "3"
    return response


async def database_busy(request, exc):
    response = error_response("The service is busy. Keep pending drafts and retry using the same request identifier.", 503, "database_busy")
    response.headers["Retry-After"] = "3"
    return response


from pymongo.errors import ConnectionFailure, ExecutionTimeout, WTimeoutError
for failure in (ConnectionFailure, ExecutionTimeout, WTimeoutError):
    app.add_exception_handler(failure, database_busy)


from tejas.canonical import CanonicalIntegrityError


@app.exception_handler(CanonicalIntegrityError)
async def integrity_error(request, exc):
    import logging
    logging.getLogger(__name__).error('Canonical content check failed request_id=%s', request_id.get())
    return error_response('This content could not be verified. Saved answers are unchanged; contact support.', 503, 'integrity_unavailable')


@app.get('/api/ready')
async def ready():
    await client.admin.command('ping', maxTimeMS=1000)
    return {'status': 'ready', 'capacity_qualified': False}


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "jeemains.ai", "version": "1.0.0"}


for module in [
    auth,
    phone,
    content,
    answers,
    attempts,
    jobs,
    reviewers,
    profiles,
    corrections,
    engineering,
    imports,
    competitions,
    reviews,
    chapter_books,
    ai_solutions,
    cohorts,
    smart_imports,
    exam_navigation,
    mock_books,
    mock_solutions,
    manual_solutions,
    question_reports,
    learning_progress,
    my_tests,
    historical_rank,
    bitsat_branches,
    live_series,
    series_streak,
    jee_transfer,
    attempt_status,
    pyq,
    pyq_import,
    students,
    book_imports,
    structure,
    integrity,
    library,
    master,
    written,
    series_admin,
    chapter_split,
    draft_preview,
    qa_cleanup,
    timeline,
    analysis_api,
    names,
    media,
    rank_predictor,
    dreams,
    mission,
]:
    app.include_router(module.router)

from tejas.route_contracts import install_contracts
install_contracts(app)
