from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent / ".env")
import os, uuid, time, asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
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
)
from tejas.db import indexes, client
from tejas.contracts import EnvelopeResponse, error_response, request_id
from tejas_storage import StorageError


@asynccontextmanager
async def lifespan(app):
    await indexes()
    await auth.seed_owner()
    from tejas.mock_solutions import worker, solutions
    await solutions.create_index('id', unique=True)
    await solutions.create_index([('state', 1), ('order', 1)])
    await solutions.create_index('set_id')
    solver = asyncio.create_task(worker())
    yield
    solver.cancel()
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
origins = [os.environ["FRONTEND_URL"].rstrip("/")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type"],
)


@app.middleware("http")
async def protections(request: Request, call_next):
    rid = str(uuid.uuid4())
    ctx = request_id.set(rid)
    started = time.perf_counter()
    try:
        origin = request.headers.get("origin")
        if (
            request.method in ["POST", "PUT", "PATCH", "DELETE"]
            and origin
            and origin not in origins
        ):
            return error_response("Cross-origin write rejected.", 403, "origin_denied")
        response = await call_next(request)
        response.headers.update(
            {
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "same-origin",
                "X-Request-ID": rid,
                "Cache-Control": "private, no-store",
                "X-Frame-Options": "DENY",
                "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
                "Server-Timing": f"app;dur={(time.perf_counter()-started)*1000:.1f}",
            }
        )
        return response
    finally:
        request_id.reset(ctx)


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
]:
    app.include_router(module.router)

from tejas.route_contracts import install_contracts
install_contracts(app)
