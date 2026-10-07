from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, Query, Response

from ..deps import get_services
from ..errors import ApiError, not_found
from ..schemas import CollectionName, Document, DocumentIngest, DocumentPage, Job
from ..services import Services
from ..store.postgres import decode_cursor, encode_cursor

router = APIRouter(tags=["Documents"])


async def _require_collection(svc: Services, name: str) -> None:
    if await svc.db.get_collection(name) is None:
        raise not_found(f"Collection {name!r}")


@router.get(
    "/v1/collections/{collection}/documents", operation_id="listDocuments", response_model=DocumentPage
)
async def list_documents(
    collection: CollectionName,
    limit: int = Query(50, ge=1, le=200),
    cursor: str | None = None,
    status: Literal["queued", "processing", "indexed", "failed"] | None = None,
    svc: Services = Depends(get_services),
) -> DocumentPage:
    await _require_collection(svc, collection)
    offset = decode_cursor(cursor)
    items, has_more = await svc.db.list_documents(collection, limit, offset, status)
    return DocumentPage(items=items, next_cursor=encode_cursor(offset + limit) if has_more else None)


@router.post(
    "/v1/collections/{collection}/documents",
    operation_id="ingestDocument",
    response_model=Job,
    status_code=202,
)
async def ingest_document(
    collection: CollectionName,
    body: DocumentIngest,
    response: Response,
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key", max_length=128),
    svc: Services = Depends(get_services),
) -> Job:
    await _require_collection(svc, collection)
    max_chars = svc.settings.rag_max_document_chars
    if body.source.type == "inline" and len(body.source.text) > max_chars:
        raise ApiError(413, "payload_too_large", f"Inline text exceeds {max_chars} characters")

    job, created = await svc.db.create_ingest(
        collection,
        body.external_id,
        body.source.model_dump(exclude_none=True),
        body.metadata,
        body.chunking,
        idempotency_key,
        body.content_hash,
    )
    if created and job.document_id is not None:
        svc.pipeline.submit(job.id, job.document_id)
    response.headers["Location"] = f"/v1/jobs/{job.id}"
    return job


@router.get(
    "/v1/collections/{collection}/documents/{documentId}",
    operation_id="getDocument",
    response_model=Document,
)
async def get_document(
    collection: CollectionName, documentId: UUID, svc: Services = Depends(get_services)
) -> Document:
    doc = await svc.db.get_document(collection, documentId)
    if doc is None:
        raise not_found(f"Document {documentId}")
    return doc


@router.delete(
    "/v1/collections/{collection}/documents/{documentId}",
    operation_id="deleteDocument",
    status_code=204,
)
async def delete_document(
    collection: CollectionName, documentId: UUID, svc: Services = Depends(get_services)
) -> Response:
    if await svc.db.get_document(collection, documentId) is None:
        raise not_found(f"Document {documentId}")
    if await svc.vectors.exists(collection):
        await svc.vectors.delete_document_points(collection, documentId)
    await svc.db.delete_document(collection, documentId)
    return Response(status_code=204)


@router.get("/v1/jobs/{jobId}", operation_id="getJob", response_model=Job)
async def get_job(jobId: UUID, svc: Services = Depends(get_services)) -> Job:
    job = await svc.db.get_job(jobId)
    if job is None:
        raise not_found(f"Job {jobId}")
    return job
