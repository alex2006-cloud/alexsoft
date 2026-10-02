"""FastAPI application. Run: `python -m alexsoft_rag` (or uvicorn alexsoft_rag.main:app)."""

from __future__ import annotations

import logging
import os
import re
import uuid
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request

from . import __version__
from .api import collections, documents, health, retrieval
from .config import get_settings
from .deps import require_api_key
from .errors import install_error_handlers
from .services import Services, build_services

log = logging.getLogger("alexsoft_rag")
_REQUEST_ID_OK = re.compile(r"^[\w.\-:]{1,128}$")


def create_app(services: Services | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        svc = services or build_services(get_settings())
        app.state.services = svc
        if not svc.settings.rag_api_key:
            log.error("RAG_API_KEY is empty: all protected endpoints will answer 401")
        await svc.db.connect()
        stale = await svc.db.fail_stale_jobs()
        if stale:
            log.warning("marked %d stale ingest job(s) as failed after restart", stale)
        try:
            await svc.objects.ensure_bucket()
        except Exception as e:  # MinIO may be down; /health/ready reports it
            log.warning("could not ensure MinIO bucket: %s", e)
        warm = getattr(svc.sparse, "warmup", None)
        if warm:
            import asyncio

            await asyncio.to_thread(warm)
        log.info("alexsoft-rag %s ready", __version__)
        try:
            yield
        finally:
            await svc.pipeline.drain()
            await svc.llm.aclose()
            await svc.vectors.aclose()
            await svc.db.close()

    app = FastAPI(
        title="alexsoft RAG API",
        version=__version__,
        description="Implements artifacts/api/rag.openapi.yaml",
        lifespan=lifespan,
    )
    install_error_handlers(app)

    @app.middleware("http")
    async def request_id(request: Request, call_next):
        incoming = request.headers.get("X-Request-Id", "")
        rid = incoming if _REQUEST_ID_OK.match(incoming) else uuid.uuid4().hex
        request.state.request_id = rid
        response = await call_next(request)
        response.headers["X-Request-Id"] = rid
        return response

    app.include_router(health.router)
    secured = [Depends(require_api_key)]
    app.include_router(collections.router, dependencies=secured)
    app.include_router(documents.router, dependencies=secured)
    app.include_router(retrieval.router, dependencies=secured)
    return app


def _configure_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("RAG_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def run() -> None:
    import uvicorn

    _configure_logging()
    s = get_settings()
    uvicorn.run(create_app(), host=s.rag_host, port=s.rag_port, log_level="info")
