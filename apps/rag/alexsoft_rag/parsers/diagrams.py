"""Diagram sources (.drawio, .bpmn, .xml) -> readable text: nodes (grouped by container) and links.

The point is retrieval: "what does the RAG container talk to?" is answered from the node/edge list,
not from XML noise.
"""

from __future__ import annotations

import base64
import html
import re
import urllib.parse
import xml.etree.ElementTree as ET
import zlib

from ..errors import ApiError
from .base import ParseContext, RawDocument, Segment
from .text import parse_plain

_TAG = re.compile(r"<[^>]+>")
_BPMN_FLOW_NODES = re.compile(r"(task|event|gateway|subProcess|callActivity)$", re.I)


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _clean_label(value: str | None) -> str:
    if not value:
        return ""
    text = html.unescape(_TAG.sub(" ", value.replace("<br>", " ").replace("<br/>", " ")))
    return re.sub(r"\s+", " ", text).strip()


def _parse_xml(raw: RawDocument) -> ET.Element:
    head = raw.data[:4096].lower()
    if b"<!doctype" in head or b"<!entity" in raw.data[:65536].lower():
        raise ApiError(422, "validation_error", f"{raw.filename}: DTD/entities are not allowed in XML")
    try:
        return ET.fromstring(raw.data)
    except ET.ParseError as e:
        raise ApiError(422, "validation_error", f"{raw.filename}: invalid XML ({e})") from e


# ---- draw.io ---------------------------------------------------------------------------
def _decode_diagram(text: str) -> ET.Element | None:
    """Compressed draw.io page: base64 -> raw deflate -> url-encoded XML."""
    try:
        data = zlib.decompress(base64.b64decode(text.strip()), -15)
        return ET.fromstring(urllib.parse.unquote(data.decode("utf-8")))
    except Exception:  # noqa: BLE001
        return None


def _drawio_page(name: str, model: ET.Element) -> str:
    labels: dict[str, str] = {}
    parents: dict[str, str] = {}
    vertices: list[str] = []
    edges: list[tuple[str, str, str]] = []
    for el in model.iter():
        tag = _local(el.tag)
        if tag in ("object", "UserObject"):
            cell = next((c for c in el if _local(c.tag) == "mxCell"), None)
            attrs = cell.attrib if cell is not None else {}
            cid, label = el.get("id", ""), _clean_label(el.get("label"))
        elif tag == "mxCell":
            if el.get("id") in labels:  # already handled via its wrapper
                continue
            attrs, cid, label = el.attrib, el.get("id", ""), _clean_label(el.get("value"))
        else:
            continue
        if not cid or cid in ("0", "1"):
            continue
        labels[cid] = label
        parents[cid] = attrs.get("parent", "")
        if attrs.get("edge") == "1":
            edges.append((attrs.get("source", ""), attrs.get("target", ""), label))
        elif attrs.get("vertex") == "1" and label:
            vertices.append(cid)

    groups: dict[str, list[str]] = {}
    for vid in vertices:
        parent = parents.get(vid, "")
        key = labels.get(parent, "") if parent not in ("0", "1", "") else ""
        groups.setdefault(key, []).append(labels[vid])

    lines = [f"Диаграмма: {name}"]
    for container, nodes in groups.items():
        title = f"Внутри «{container}»" if container else "Узлы"
        lines.append(f"{title}: " + "; ".join(dict.fromkeys(nodes)))
    links = []
    for src, dst, label in edges:
        a, b = labels.get(src, ""), labels.get(dst, "")
        if a and b:
            links.append(f"- {a} -> {b}" + (f" [{label}]" if label else ""))
    if links:
        lines.append("Связи:")
        lines.extend(dict.fromkeys(links))
    return "\n".join(lines)


def _parse_drawio(root: ET.Element) -> list[Segment]:
    out: list[Segment] = []
    if _local(root.tag) == "mxGraphModel":
        text = _drawio_page("page", root)
        return [Segment(text, kind="diagram", locator={"section": "page"})] if "\n" in text else []
    for diagram in root.iter():
        if _local(diagram.tag) != "diagram":
            continue
        name = diagram.get("name") or "page"
        model = next((c for c in diagram if _local(c.tag) == "mxGraphModel"), None)
        if model is None and (diagram.text or "").strip():
            model = _decode_diagram(diagram.text)
        if model is None:
            continue
        text = _drawio_page(name, model)
        if text.count("\n") >= 1:
            out.append(Segment(text, kind="diagram", locator={"section": name}))
    return out


# ---- BPMN --------------------------------------------------------------------------------
def _parse_bpmn(root: ET.Element) -> list[Segment]:
    out: list[Segment] = []
    nodes: dict[str, tuple[str, str]] = {}  # id -> (type, name)
    for el in root.iter():
        tag = _local(el.tag)
        if _BPMN_FLOW_NODES.search(tag) and el.get("id"):
            nodes[el.get("id", "")] = (tag, el.get("name") or el.get("id", ""))

    for process in (e for e in root.iter() if _local(e.tag) == "process"):
        pname = process.get("name") or process.get("id") or "process"
        lines = [f"BPMN-процесс: {pname}"]
        docs = [_clean_label(d.text) for d in process.iter() if _local(d.tag) == "documentation" and d.text]
        if docs:
            lines.append("Описание: " + " ".join(docs))
        lanes = [e for e in process.iter() if _local(e.tag) == "lane"]
        for lane in lanes:
            refs = [nodes.get((r.text or "").strip(), ("", ""))[1] for r in lane if _local(r.tag) == "flowNodeRef"]
            refs = [r for r in refs if r]
            lines.append(f"Дорожка «{lane.get('name') or lane.get('id')}»: " + "; ".join(refs))
        lines.append("Элементы:")
        for el in process.iter():
            tag = _local(el.tag)
            if _BPMN_FLOW_NODES.search(tag) and el.get("id"):
                lines.append(f"- [{tag}] {el.get('name') or el.get('id')}")
        flows = []
        for el in process.iter():
            if _local(el.tag) == "sequenceFlow":
                a = nodes.get(el.get("sourceRef", ""), ("", el.get("sourceRef", "")))[1]
                b = nodes.get(el.get("targetRef", ""), ("", el.get("targetRef", "")))[1]
                flows.append(f"- {a} -> {b}" + (f" [{el.get('name')}]" if el.get("name") else ""))
        if flows:
            lines.append("Переходы:")
            lines.extend(flows)
        out.append(Segment("\n".join(lines), kind="diagram", locator={"section": pname}))
    return out


async def parse_diagram(raw: RawDocument, ctx: ParseContext) -> list[Segment]:
    root = _parse_xml(raw)
    kind = _local(root.tag)
    if kind in ("mxfile", "mxGraphModel"):
        segments = _parse_drawio(root)
    elif kind == "definitions":
        segments = _parse_bpmn(root)
    else:  # generic XML: treat as text
        return await parse_plain(raw, ctx)
    if not segments:
        raise ApiError(422, "validation_error", f"{raw.filename}: diagram has no readable nodes")
    return segments


EXTENSIONS = {".drawio": parse_diagram, ".bpmn": parse_diagram, ".xml": parse_diagram}
