from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import get_services
from ..schemas import QueryRequest, QueryResponse, SearchRequest, SearchResponse
from ..services import Services

router = APIRouter(tags=["Retrieval"])


@router.post("/v1/search", operation_id="searchChunks", response_model=SearchResponse)
async def search_chunks(body: SearchRequest, svc: Services = Depends(get_services)) -> SearchResponse:
    chunks, timings = await svc.search.search(body, body.query)
    return SearchResponse(chunks=chunks, timings_ms=timings)


@router.post("/v1/query", operation_id="queryWithAnswer", response_model=QueryResponse)
async def query_with_answer(body: QueryRequest, svc: Services = Depends(get_services)) -> QueryResponse:
    return await svc.query.query(body)
