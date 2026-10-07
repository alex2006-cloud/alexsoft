"""FastAPI app. Run: `python -m alexsoft_api` (or uvicorn alexsoft_api.main:app)."""

from __future__ import annotations

import logging
import os
import re
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request

from . import __version__
from .agents import seed_agents
from .config import get_settings
from .errors import install_error_handlers
from .routes import router
from .services import Services, build_services

log = logging.getLogger("alexsoft_api")
_REQUEST_ID_OK = re.compile(r"^[\w.\-:]{1,128}$")


def create_app(services: Services | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        svc = services or build_services(get_settings())
        app.state.services = svc
        if not svc.settings.authentik_bl_token:
            log.warning("AUTHENTIK_BL_TOKEN is empty: /v1/admin/users will answer 502")
        await svc.store.connect()
        stale = await svc.store.fail_stale_runs()
        if stale:
            log.warning("marked %d stale run(s) as failed after restart", stale)
        await svc.store.seed_agents(seed_agents(svc.settings))
        log.info("alexsoft-api %s ready (issuer %s)", __version__, svc.settings.issuer)
        try:
            yield
        finally:
            await svc.runs.shutdown()
            await svc.authentik.aclose()
            if svc.keys:
                await svc.keys.aclose()
            await svc.store.close()

    app = FastAPI(
        title="alexsoft BL API",
        version=__version__,
        description="Implements artifacts/api/bl.openapi.yaml",
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

    app.include_router(router)
    return app


def _configure_logging() -> None:
    logging.basicConfig(
        level=os.environ.get("BL_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


def run() -> None:
    import uvicorn

    _configure_logging()
    s = get_settings()
    uvicorn.run(create_app(), host=s.bl_host, port=s.bl_port, log_level="info")
