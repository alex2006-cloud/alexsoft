"""CLI: python -m alexsoft_rag.kbsync [--dry-run] [--no-summaries] [--only GLOB ...] [--force] [--strict]"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from ..config import REPO_ROOT, get_settings
from .config import load_config
from .runner import KbSync, build_plan, git_files


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="kb-sync", description="Sync the repo into the project knowledge base.")
    ap.add_argument("--config", type=Path, default=None, help="path to sources.yaml")
    ap.add_argument("--api", default=None, help="RAG base URL (default http://127.0.0.1:RAG_PORT)")
    ap.add_argument("--dry-run", action="store_true", help="show what would be synced, touch nothing")
    ap.add_argument("--no-summaries", action="store_true", help="do not generate/refresh code summaries")
    ap.add_argument("--only", action="append", default=None, metavar="GLOB", help="sync only matching files (repeatable)")
    ap.add_argument("--collection", action="append", default=None, help="limit to a collection (repeatable)")
    ap.add_argument("--force", action="store_true", help="re-ingest even if the content hash is unchanged")
    ap.add_argument("--no-delete", action="store_true", help="do not remove documents of vanished files")
    ap.add_argument("--strict", action="store_true", help="exit 1 when files were skipped as suspected secrets")
    ap.add_argument("-v", "--verbose", action="store_true", help="list skipped files")
    args = ap.parse_args(argv)

    settings = get_settings()
    cfg = load_config(args.config)
    if args.no_summaries:
        cfg.summaries.enabled = False
    if args.collection:
        cfg.collections = [c for c in cfg.collections if c.name in set(args.collection)]
        if not cfg.collections:
            print("no such collection in sources.yaml")
            return 2

    files = git_files(REPO_ROOT)
    plan = build_plan(cfg, REPO_ROOT, files, only=args.only)
    by_col = Counter(i.collection for i in plan.items)
    print(f"Repo: {len(files)} files -> {len(plan.items)} selected "
          + ", ".join(f"{k}={v}" for k, v in sorted(by_col.items())))
    skipped = Counter(reason.split(" (")[0] for _, reason in plan.skipped)
    print("Skipped: " + (", ".join(f"{k}={v}" for k, v in sorted(skipped.items())) or "none"))
    if args.verbose:
        for rel, reason in plan.skipped:
            print(f"   skip {rel}: {reason}")
    if plan.flagged:
        print(f"WARNING: {len(plan.flagged)} file(s) NOT indexed (suspected secrets):")
        for rel, reason in plan.flagged:
            print(f"   {rel}: {reason}")

    base = args.api or f"http://127.0.0.1:{settings.rag_port}"
    sync = KbSync(cfg, settings, REPO_ROOT, base)
    try:
        remote: dict[str, dict] = {}
        if not args.dry_run:
            sync.ensure_collections({c.name for c in cfg.collections})
            remote = {c.name: sync.remote_documents(c.name) for c in cfg.collections}
        stats = sync.add_summaries(plan, remote, dry_run=args.dry_run)
        if stats:
            print("Summaries: " + ", ".join(f"{k}={v}" for k, v in sorted(stats.items())))
        if args.dry_run:
            for rule in cfg.collections:
                print(f"[{rule.name}]")
                for it in plan.items:
                    if it.collection == rule.name:
                        print(f"   {it.metadata['kind']:<14} {it.external_id}")
            return 1 if (args.strict and plan.flagged) else 0
        failed = sync.sync(plan, remote, delete=not args.no_delete and not args.only, force=args.force)
        for rule in cfg.collections:
            info = sync.http.get(f"/v1/collections/{rule.name}").json()
            print(f"[{rule.name}] {info['documents_count']} docs, {info['chunks_count']} chunks")
    finally:
        sync.close()

    if failed:
        print(f"FAILED: {failed} document(s)")
        return 1
    if args.strict and plan.flagged:
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
