"""File selection rules for kb-sync: glob matching and the secret guard (nothing sensitive gets indexed)."""

from __future__ import annotations

import fnmatch
import math
import posixpath
import re
from functools import lru_cache

# ---- globs ---------------------------------------------------------------------------------


@lru_cache(maxsize=512)
def _glob_regex(pattern: str) -> re.Pattern[str]:
    out: list[str] = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif c == "*":
            out.append("[^/]*")
            i += 1
        elif c == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(c))
            i += 1
    return re.compile("".join(out) + r"\Z", re.I)


def match_glob(path: str, pattern: str) -> bool:
    """gitignore-like: a pattern without `/` matches the file name at any depth; `**` crosses folders."""
    path = path.replace("\\", "/")
    if "/" not in pattern:
        return bool(_glob_regex(pattern).match(posixpath.basename(path)))
    return bool(_glob_regex(pattern.lstrip("/")).match(path))


def match_any(path: str, patterns: list[str]) -> bool:
    return any(match_glob(path, p) for p in patterns)


# ---- secret guard --------------------------------------------------------------------------------
# Files that are never read, whatever is inside (name-based).
SECRET_NAME_PATTERNS = [
    ".env", ".env.*", "*.pem", "*.key", "*.p12", "*.pfx", "*.jks", "*.kdbx", "credentials.json",
    "secrets.*", "id_rsa*", "id_ed25519*", "*.sqlite", "*.sqlite3", "*.db", "*.dump", "*.bak",
]
SECRET_NAME_ALLOW = {".env.example", ".env.sample", ".env.template"}


def is_secret_name(path: str) -> bool:
    name = posixpath.basename(path).lower()
    if name in SECRET_NAME_ALLOW:
        return False
    return any(fnmatch.fnmatch(name, p) for p in SECRET_NAME_PATTERNS)


_TOKEN_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("API key (sk-...)", re.compile(r"\bsk-[A-Za-z0-9_-]{20,}")),
    ("private key", re.compile(r"-----BEGIN (?:[A-Z]+ )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
]
_ASSIGNMENT = re.compile(
    r"""(?ix)
    (?:api[_-]?key|secret|token|passwd|password|master[_-]?key|access[_-]?key)  # name
    ["']?\s*[:=]\s*
    ["']?([A-Za-z0-9_\-+/=.]{16,})["']?
    """
)
_PLACEHOLDER = re.compile(
    r"(?i)change|your|example|placeholder|dummy|sample|redacted|xxxx|\.\.\.|<|\$\{|\{\{|todo|secret|password|token|test"
)


def _entropy(s: str) -> float:
    counts = {ch: s.count(ch) for ch in set(s)}
    return -sum(c / len(s) * math.log2(c / len(s)) for c in counts.values())


def _looks_like_secret_value(value: str) -> bool:
    if _PLACEHOLDER.search(value):
        return False
    has_digit = any(ch.isdigit() for ch in value)
    has_alpha = any(ch.isalpha() for ch in value)
    if not (has_digit and has_alpha):
        return False  # identifiers like `settings.rag_api_key`, `os_environ_value`
    if re.fullmatch(r"[a-z0-9_.]+", value) and ("_" in value or "." in value):
        return False  # snake_case / dotted names, not random strings
    return _entropy(value) >= 3.3


def find_secret(text: str) -> str | None:
    """Return a short reason if the text contains something that looks like a real secret."""
    for label, pattern in _TOKEN_PATTERNS:
        if pattern.search(text):
            return label
    for m in _ASSIGNMENT.finditer(text):
        if _looks_like_secret_value(m.group(1)):
            return "hard-coded secret assignment"
    return None
