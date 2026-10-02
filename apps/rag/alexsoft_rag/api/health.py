from __future__ import annotations

import asyncio

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from ..deps import get_services
from ..schemas import Health
from ..services import Services

router = APIRouter(tags=["Health"])


@router.get("/health/live", operation_id="getLiveness", response_model=Health)
async def live() -> Health:
    return Health(status="ok")


@router.get(
    "/health/ready",
    operation_id="getReadiness",
    response_model=Health,
    responses={503: {"model": Health}},
)
async def ready(svc: Services = Depends(get_services)) -> JSONResponse:
    names = ["postgres", "qdrant", "minio", "litellm"]
    results = await asyncio.gather(
        svc.db.is_alive(), svc.vectors.is_alive(), svc.objects.is_alive(), svc.llm.is_alive()
    )
    deps = {n: ("ok" if ok else "down") for n, ok in zip(names, results)}
    up = sum(results)
    status = "ok" if up == len(results) else ("down" if up == 0 else "degraded")
    body = Health(status=status, dependencies=deps)
    return JSONResponse(body.model_dump(), status_code=200 if status == "ok" else 503)
