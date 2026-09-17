"""Export LangFlow workflows from local SQLite into the alexsoft repo.

Reads the on-disk LangFlow DB (no API key). Skips Starter templates.
Redacts obvious secrets from node data before writing JSON.
"""
from __future__ import annotations

import json
import re
import sqlite3
import sys
from pathlib import Path

SECRET_KEY_RE = re.compile(
    r"(api[_-]?key|password|secret|token|authorization|access[_-]?key|private[_-]?key)$",
    re.I,
)
STARTER_FOLDER_RE = re.compile(r"^starter\s*projects$", re.I)  # example pack only (plural)

UNSAFE_NAME = re.compile(r"[^\w\-]+", re.UNICODE)



def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def find_db() -> Path | None:
    local = Path.home() / "AppData" / "Local"
    candidates = [
        local / "LangFlow" / "langflow.db",
        local / "langflow" / "langflow.db",
        local / "LangFlow" / "venv" / "Lib" / "site-packages" / "langflow" / "langflow.db",
        local / "langflow" / "venv" / "Lib" / "site-packages" / "langflow" / "langflow.db",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return None


def safe_filename(name: str, flow_id: str) -> str:
    base = UNSAFE_NAME.sub("-", (name or "flow").strip()).strip("-").lower() or "flow"
    short = (flow_id or "id")[:8]
    return f"{base}--{short}.json"


def redact(obj):
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if isinstance(k, str) and SECRET_KEY_RE.search(k) and isinstance(v, str) and v:
                # Keep empty / placeholder / env-looking values
                if v.startswith(("os.environ", "${", "{{")) or v in {"*", "****"}:
                    out[k] = v
                else:
                    out[k] = "***REDACTED***"
            else:
                out[k] = redact(v)
        return out
    if isinstance(obj, list):
        return [redact(x) for x in obj]
    return obj


def export_flows(out_dir: Path) -> int:
    db = find_db()
    if db is None:
        print("LangFlow DB not found — skip export (OK if LangFlow unused).")
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(
        """
        SELECT f.id, f.name, f.description, f.data, f.updated_at, f.is_component,
               f.flow_type, fol.name AS folder_name
        FROM flow f
        LEFT JOIN folder fol ON f.folder_id = fol.id
        WHERE COALESCE(f.is_component, 0) = 0
        """
    )
    rows = cur.fetchall()
    conn.close()

    written = 0
    keep_names: set[str] = set()
    for row in rows:
        folder = row["folder_name"] or ""
        if STARTER_FOLDER_RE.match(folder.strip()):
            continue
        raw = row["data"]
        if isinstance(raw, str):
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = raw
        else:
            data = raw

        payload = {
            "id": row["id"],
            "name": row["name"],
            "description": row["description"],
            "folder": folder,
            "flow_type": row["flow_type"],
            "updated_at": row["updated_at"],
            "data": redact(data),
        }
        fname = safe_filename(row["name"], row["id"])
        keep_names.add(fname)
        path = out_dir / fname
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written += 1
        print(f"wrote {path.relative_to(repo_root())}")

    # Remove stale exports that are no longer in DB (non-starter)
    for existing in out_dir.glob("*.json"):
        if existing.name not in keep_names:
            existing.unlink()
            print(f"removed stale {existing.relative_to(repo_root())}")

    print(f"export_done count={written} db={db}")
    return written


def main() -> int:
    out = repo_root() / "apps" / "agent1" / "langflow" / "flows"
    export_flows(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
