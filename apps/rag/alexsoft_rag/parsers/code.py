"""Source code and config parsers (ADR-0018).

* py: stdlib `ast` -> one unit per top-level definition (large classes are split into methods).
* ts / tsx / js: declaration boundaries by regex (large classes are split into methods).
* ps1 / sql / yaml / toml / dsl / puml / ...: block-wise splitting by language-specific boundaries.

Small neighbouring units are merged up to `chunk_size` tokens. Every segment carries
`File / Language / Symbol / Lines` in `header` and `line_start` / `line_end` / `symbol` in the locator
(line numbers refer to the original file).

Why no tree-sitter: its native Python binding corrupted the heap on Windows (random access
violations in unrelated code), which is unacceptable for a long-running service.
"""

from __future__ import annotations

import ast
import posixpath
import re
from dataclasses import dataclass
from typing import Any

from .base import ParseContext, RawDocument, Segment, count_tokens, normalize_newlines
from .text import decode_text

# ---- languages -------------------------------------------------------------------
LANGUAGES: dict[str, str] = {
    ".py": "python", ".pyi": "python",
    ".ts": "typescript", ".mts": "typescript", ".cts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript", ".jsx": "javascript", ".mjs": "javascript", ".cjs": "javascript",
    ".ps1": "powershell", ".psm1": "powershell",
    ".sql": "sql",
    ".yaml": "yaml", ".yml": "yaml",
    ".toml": "toml", ".ini": "ini", ".cfg": "ini", ".conf": "nginx",
    ".json": "json",
    ".dsl": "structurizr", ".puml": "plantuml", ".plantuml": "plantuml",
    ".sh": "shell", ".bat": "batch", ".cmd": "batch",
    ".css": "css", ".html": "html",
}
JS_FAMILY = {"typescript", "tsx", "javascript"}


@dataclass
class Unit:
    start: int  # 0-based first line
    end: int  # 0-based last line
    names: list[str]
    tokens: int = 0


def _unit_tokens(lines: list[str], u: Unit) -> int:
    return count_tokens("\n".join(lines[u.start : u.end + 1]))


# ---- python (ast) ----------------------------------------------------------------------
_PY_DEFS = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)


def _py_start(node: ast.stmt) -> int:
    decorators = getattr(node, "decorator_list", [])
    return min([node.lineno, *[d.lineno for d in decorators]]) - 1


def _py_collect(body: list[ast.stmt], prefix: str, lines: list[str], limit: int) -> list[Unit]:
    units: list[Unit] = []
    for node in body:
        sym = node.name if isinstance(node, _PY_DEFS) else None
        full = (f"{prefix}.{sym}" if prefix else sym) if sym else ""
        u = Unit(_py_start(node), (node.end_lineno or node.lineno) - 1, [full] if full else [])
        if isinstance(node, ast.ClassDef) and _unit_tokens(lines, u) > limit:
            first = next((i for i, n in enumerate(node.body) if isinstance(n, _PY_DEFS)), None)
            if first is not None:
                head_end = max(_py_start(node.body[first]) - 1, u.start)
                units.append(Unit(u.start, head_end, [full]))
                units.extend(_py_collect(node.body[first:], full, lines, limit))
                continue
        units.append(u)
    return units


def _units_python(text: str, limit: int) -> list[Unit] | None:
    try:
        tree = ast.parse(text)
    except (SyntaxError, ValueError):
        return None
    return _py_collect(tree.body, "", text.split("\n"), limit)


# ---- ts / tsx / js (regex) -------------------------------------------------------------------
_JS_DECL = re.compile(
    r"^(?:export\s+)?(?:default\s+)?(?:declare\s+)?(?:abstract\s+)?(?:async\s+)?"
    r"(?:function\*?|class|interface|type|enum|namespace|const|let|var)\s+([A-Za-z_$][\w$]*)"
)
_JS_DEFAULT_ANON = re.compile(r"^export\s+default\s+(?:async\s+)?(?:function|class)\b")
_JS_CLASS = re.compile(r"^(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+")
_JS_METHOD = re.compile(
    r"^(?: {2}| {4}|\t)(?:(?:public|private|protected|static|async|readonly|override|abstract|get|set)\s+)*"
    r"([A-Za-z_$#][\w$]*)\s*(?:<[^>\n]*>)?\s*\("
)
_NOT_METHODS = {"if", "for", "while", "switch", "return", "catch", "function", "await", "super", "with"}
_COMMENT_LINE = re.compile(r"^\s*(?://|/\*|\*|@)")


def _js_boundaries(lines: list[str]) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        m = _JS_DECL.match(line)
        name = m.group(1) if m else ("default" if _JS_DEFAULT_ANON.match(line) else None)
        if name is None:
            continue
        start = i
        while start > 0 and _COMMENT_LINE.match(lines[start - 1]):  # leading doc comments / decorators
            start -= 1
        found.append((start, name))
    return found


def _js_split_class(lines: list[str], u: Unit, class_name: str) -> list[Unit]:
    cuts: list[tuple[int, str]] = []
    for i in range(u.start + 1, u.end + 1):
        m = _JS_METHOD.match(lines[i])
        if not m or m.group(1) in _NOT_METHODS or not lines[i].rstrip().endswith(("{", ";", ",", ")")):
            continue
        start = i
        while start > u.start + 1 and _COMMENT_LINE.match(lines[start - 1]):
            start -= 1
        cuts.append((start, f"{class_name}.{m.group(1)}"))
    if not cuts:
        return [u]
    units = [Unit(u.start, cuts[0][0] - 1, [class_name])]
    for k, (start, name) in enumerate(cuts):
        end = cuts[k + 1][0] - 1 if k + 1 < len(cuts) else u.end
        units.append(Unit(start, end, [name]))
    return units


def _units_js(lines: list[str], limit: int) -> list[Unit]:
    bounds = _js_boundaries(lines)
    if not bounds:
        return [Unit(0, len(lines) - 1, [])]
    units: list[Unit] = []
    if bounds[0][0] > 0:
        units.append(Unit(0, bounds[0][0] - 1, []))
    for k, (start, name) in enumerate(bounds):
        end = bounds[k + 1][0] - 1 if k + 1 < len(bounds) else len(lines) - 1
        u = Unit(start, end, [name])
        decl_line = next((ln for ln in lines[start : end + 1] if _JS_DECL.match(ln)), "")
        if _JS_CLASS.match(decl_line) and _unit_tokens(lines, u) > limit:
            units.extend(_js_split_class(lines, u, name))
        else:
            units.append(u)
    return units


# ---- block-wise (no grammar) ----------------------------------------------------------
_BOUNDARIES: dict[str, re.Pattern[str]] = {
    "powershell": re.compile(r"^(?:function|filter)\s+([\w:-]+)|^#region\s+(.+)", re.I),
    "sql": re.compile(
        r"^\s*(?:create|alter)\s+(?:or\s+replace\s+)?(?:unique\s+)?(?:table|view|function|procedure|index|schema|type|trigger|extension)\s+(?:if\s+not\s+exists\s+)?([\w.\"]+)",
        re.I,
    ),
    "python": re.compile(r"^(?:async\s+)?(?:def|class)\s+(\w+)"),  # fallback for files that do not parse
    "yaml": re.compile(r"^([A-Za-z_][\w.\-/ ]*):(?:\s|$)"),
    "toml": re.compile(r"^\[\[?([^\]]+)\]\]?"),
    "ini": re.compile(r"^\[([^\]]+)\]"),
    "nginx": re.compile(r"^(?:server|upstream|location|http|events|map)\b[^{]*"),
    "structurizr": re.compile(r"^ {0,4}(?:\w+\s*=\s*)?(\w+(?:\s+\"[^\"]*\")?)[^{\n]*\{\s*$"),
    "plantuml": re.compile(r"^(?:@start\w+|package\b.*\{|node\b.*\{|rectangle\b.*\{|== .+ ==|title\b.*)"),
    "shell": re.compile(r"^(?:function\s+)?([\w-]+)\s*\(\)\s*\{|^function\s+([\w-]+)"),
    "batch": re.compile(r"^:([\w-]+)\s*$"),
    "css": re.compile(r"^([.#@\w][^{]*)\{\s*$"),
}


def _boundary_symbol(lang: str, line: str) -> str | None:
    pattern = _BOUNDARIES.get(lang)
    if pattern is None:
        return None
    m = pattern.match(line)
    if not m:
        return None
    groups = [g for g in m.groups() if g]
    return (groups[0] if groups else m.group(0)).strip().strip('"')


def _units_blocks(lines: list[str], lang: str) -> list[Unit]:
    units: list[Unit] = []
    start = 0
    names: list[str] = []
    for i, line in enumerate(lines):
        sym = _boundary_symbol(lang, line)
        if sym is not None and i > start:
            units.append(Unit(start, i - 1, names))
            start, names = i, [sym]
        elif sym is not None:
            names = [sym]
    units.append(Unit(start, len(lines) - 1, names))
    return units


# ---- merge + emit ------------------------------------------------------------------------
def _contiguous(units: list[Unit], n_lines: int) -> list[Unit]:
    """Make units cover the whole file: gaps (blank lines, comments) join the *following* unit."""
    units = sorted(units, key=lambda u: u.start)
    cursor = 0
    for u in units:
        u.start = min(cursor, u.start)
        cursor = u.end + 1
    if units:
        units[-1].end = max(units[-1].end, n_lines - 1)
    return units


def _merge(units: list[Unit], lines: list[str], limit: int) -> list[Unit]:
    for u in units:
        u.tokens = _unit_tokens(lines, u)
    merged: list[Unit] = []
    for u in units:
        if merged and merged[-1].tokens + u.tokens <= limit:
            prev = merged[-1]
            prev.end = u.end
            prev.names.extend(n for n in u.names if n not in prev.names)
            prev.tokens += u.tokens
        else:
            merged.append(u)
    return merged


def _symbol_label(names: list[str]) -> str:
    if len(names) <= 3:
        return ", ".join(names)
    return ", ".join(names[:3]) + ", …"


def build_header(path: str, language: str, symbol: str, line_start: int, line_end: int) -> str:
    parts = [f"File: {path}", f"Language: {language}"]
    if symbol:
        parts.append(f"Symbol: {symbol}")
    parts.append(f"Lines: {line_start}-{line_end}")
    return "\n".join(parts)


def _segments(path: str, lang: str, lines: list[str], units: list[Unit], limit: int) -> list[Segment]:
    out: list[Segment] = []
    for u in _merge(_contiguous(units, len(lines)), lines, limit):
        block = lines[u.start : u.end + 1]
        if not any(line.strip() for line in block):
            continue
        # drop blank edges, keeping line numbers exact
        lead = next(i for i, line in enumerate(block) if line.strip())
        trail = next(i for i, line in enumerate(reversed(block)) if line.strip())
        body = "\n".join(block[lead : len(block) - trail])
        first = u.start + 1 + lead
        last = u.end + 1 - trail
        symbol = _symbol_label(u.names)
        locator: dict[str, Any] = {"line_start": first, "line_end": last}
        if symbol:
            locator["symbol"] = symbol
        out.append(
            Segment(
                body,
                kind="code",
                locator=locator,
                meta={"language": lang},
                header=build_header(path, lang, symbol, first, last),
            )
        )
    return out


async def parse_code(raw: RawDocument, ctx: ParseContext) -> list[Segment]:
    ext = posixpath.splitext(raw.filename.lower())[1]
    lang = LANGUAGES.get(ext, "text")
    text = normalize_newlines(decode_text(raw)).rstrip()
    if not text.strip():
        return []
    limit = max(ctx.chunk_size, 64)
    lines = text.split("\n")
    units: list[Unit] | None = None
    if lang == "python":
        units = _units_python(text, limit)
    elif lang in JS_FAMILY:
        units = _units_js(lines, limit)
    if units is None:  # unparsable python, or a block-wise language
        units = _units_blocks(lines, lang)
    return _segments(raw.filename, lang, lines, units, limit)


EXTENSIONS = {ext: parse_code for ext in LANGUAGES}
