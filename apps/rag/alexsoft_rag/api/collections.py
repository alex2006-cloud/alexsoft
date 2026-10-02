from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from ..deps import get_services
from ..errors import ApiError, not_found
from ..schemas import Collection, CollectionCreate, CollectionName, CollectionPage
from ..services import Services
from ..store.postgres import decode_cursor, encode_cursor

router = APIRouter(tags=["Collections"])


@router.get("/v1/collections", operation_id="listCollections", response_model=CollectionPage)
async def list_collections(
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = None,
    svc: Services = Depends(get_services),
) -> CollectionPage:
    offset = decode_cursor(cursor)
    items, has_more = await svc.db.list_collections(limit, offset)
    return CollectionPage(items=items, next_cursor=encode_cursor(offset + limit) if has_more else None)


@router.post(
    "/v1/collections",
    operation_id="createCollection",
    response_model=Collection,
    status_code=201,
)
async def create_collection(
    body: CollectionCreate, response: Response, svc: Services = Depends(get_services)
) -> Collection:
    s = svc.settings
    created = await svc.db.create_collection(
        body.name,
        body.description,
        s.rag_embedding_model,
        s.rag_embedding_dimensions,
        body.chunking,
    )
    if created is None:
        raise ApiError(409, "already_exists", f"Collection {body.name!r} already exists")
    try:
        if await svc.vectors.exists(body.name):  # orphan from a lost registry row: start clean
            await svc.vectors.delete_collection(body.name)
        await svc.vectors.create_collection(body.name, s.rag_embedding_dimensions)
    except Exception:
        await svc.db.delete_collection(body.name)  # keep registry and Qdrant consistent
        raise
    response.headers["Location"] = f"/v1/collections/{body.name}"
    return created


@router.get("/v1/collections/{collection}", operation_id="getCollection", response_model=Collection)
async def get_collection(collection: CollectionName, svc: Services = Depends(get_services)) -> Collection:
    found = await svc.db.get_collection(collection)
    if found is None:
        raise not_found(f"Collection {collection!r}")
    return found


@router.delete("/v1/collections/{collection}", operation_id="deleteCollection", status_code=204)
async def delete_collection(collection: CollectionName, svc: Services = Depends(get_services)) -> Response:
    if await svc.db.get_collection(collection) is None:
        raise not_found(f"Collection {collection!r}")
    if await svc.vectors.exists(collection):
        await svc.vectors.delete_collection(collection)
    await svc.db.delete_collection(collection)  # documents/jobs cascade; MinIO files stay
    return Response(status_code=204)
