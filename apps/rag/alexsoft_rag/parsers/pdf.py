"""PDF parser: text layer via pypdf; pages without text are rendered and read by a vision model."""

from __future__ import annotations

import asyncio
import io
import logging

import pypdfium2 as pdfium
from pypdf import PdfReader

from ..errors import ApiError
from ..ingest.parser import clean_text
from .base import ParseContext, RawDocument, Segment

log = logging.getLogger("alexsoft_rag.pdf")

MIN_TEXT_CHARS = 25  # fewer letters/digits than this = no usable text layer
RENDER_SCALE = 2.0


def _has_text(text: str) -> bool:
    return sum(ch.isalnum() for ch in text) >= MIN_TEXT_CHARS


def _extract_pages(raw: RawDocument) -> list[str]:
    try:
        reader = PdfReader(io.BytesIO(raw.data))
        if reader.is_encrypted and not reader.decrypt(""):
            raise ApiError(422, "validation_error", f"{raw.filename}: PDF is password-protected")
        pages: list[str] = []
        for page in reader.pages:
            try:
                pages.append(clean_text(page.extract_text() or ""))
            except Exception:  # noqa: BLE001 - one broken page must not fail the whole file
                pages.append("")
        return pages
    except ApiError:
        raise
    except Exception as e:  # noqa: BLE001
        raise ApiError(422, "validation_error", f"{raw.filename}: cannot read PDF ({type(e).__name__})") from e


def _render_png(data: bytes, index: int) -> bytes:
    pdf = pdfium.PdfDocument(data)
    try:
        bitmap = pdf[index].render(scale=RENDER_SCALE)
        out = io.BytesIO()
        bitmap.to_pil().convert("RGB").save(out, format="PNG", optimize=True)
        return out.getvalue()
    finally:
        pdf.close()


async def parse_pdf(raw: RawDocument, ctx: ParseContext) -> list[Segment]:
    texts = await asyncio.to_thread(_extract_pages, raw)
    scanned = [i for i, t in enumerate(texts) if not _has_text(t)]
    skipped: list[int] = []

    if scanned:
        if ctx.ocr is None:
            skipped = scanned
        else:
            todo, skipped = scanned[: ctx.max_ocr_pages], scanned[ctx.max_ocr_pages :]
            sem = asyncio.Semaphore(ctx.ocr_concurrency)

            async def ocr_page(i: int) -> tuple[int, str]:
                async with sem:
                    png = await asyncio.to_thread(_render_png, raw.data, i)
                    return i, clean_text(await ctx.ocr.read_page(png))  # type: ignore[union-attr]

            for i, text in await asyncio.gather(*(ocr_page(i) for i in todo)):
                texts[i] = text

    if skipped:
        log.warning("%s: %d page(s) without text were not OCR'd: %s", raw.filename, len(skipped), skipped[:10])

    segments = [
        Segment(
            text,
            kind="page",
            locator={"page": i + 1},
            header=f"{raw.filename}, стр. {i + 1}",
        )
        for i, text in enumerate(texts)
        if text.strip()
    ]
    if not segments:
        reason = "no text layer and OCR is not available" if ctx.ocr is None else "no recognizable text"
        raise ApiError(422, "validation_error", f"{raw.filename}: {reason}")
    return segments


EXTENSIONS = {".pdf": parse_pdf}
