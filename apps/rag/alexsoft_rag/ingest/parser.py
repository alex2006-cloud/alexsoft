"""Parser & Clean: normalize raw text before chunking."""

from __future__ import annotations

import re

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_TRAILING_WS = re.compile(r"[ \t]+$", re.MULTILINE)
_BLANKS = re.compile(r"\n{3,}")


def clean_text(text: str) -> str:
    text = text.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")
    text = _CTRL.sub("", text)
    text = _TRAILING_WS.sub("", text)
    text = _BLANKS.sub("\n\n", text)
    return text.strip()
