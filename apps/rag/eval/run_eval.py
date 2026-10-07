"""Retrieval / answer quality check against a running RAG service.

    python eval/run_eval.py                          # all questions, each asks its own collection
    python eval/run_eval.py --collection project-code
    python eval/run_eval.py --answer                 # also /v1/query: citations and insufficient_context checks
Exit code 1 if hit@k is below --min-hit.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import httpx
import yaml

from alexsoft_rag.config import get_settings

DEFAULT_COLLECTION = "project-docs"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default=None, help="ask only the questions of this collection")
    ap.add_argument("--top-k", type=int, default=5)
    ap.add_argument("--min-hit", type=float, default=0.8)
    ap.add_argument("--answer", action="store_true", help="also call /v1/query (uses the chat LLM)")
    ap.add_argument("--api", default=None)
    args = ap.parse_args()

    s = get_settings()
    http = httpx.Client(
        base_url=args.api or f"http://127.0.0.1:{s.rag_port}",
        headers={"X-API-Key": s.rag_api_key},
        timeout=180,
        trust_env=False,
    )
    data = yaml.safe_load((Path(__file__).parent / "questions.yaml").read_text(encoding="utf-8"))
    per = defaultdict(lambda: {"hits": 0, "n": 0, "rr": 0.0})
    negatives_ok = negatives = 0

    for item in data["questions"]:
        q = item["q"]
        coll = item.get("collection", DEFAULT_COLLECTION)
        if args.collection and coll != args.collection:
            continue
        if item.get("answerable") is False:
            negatives += 1
            if args.answer:
                body = http.post("/v1/query", json={"collection": coll, "question": q, "top_k": args.top_k}).json()
                ok = body.get("insufficient_context") is True
                negatives_ok += ok
                print(f"[{'OK ' if ok else 'BAD'}] (negative) {q}\n      answer={body.get('answer')!r}")
            continue

        r = http.post("/v1/search", json={"collection": coll, "query": q, "top_k": args.top_k})
        r.raise_for_status()
        chunks = r.json()["chunks"]
        rank = next(
            (i for i, c in enumerate(chunks, 1) if any(e in (c.get("external_id") or "") for e in item["expect_any"])),
            None,
        )
        stat = per[coll]
        stat["n"] += 1
        stat["hits"] += rank is not None
        stat["rr"] += 1 / rank if rank else 0
        top = chunks[0]["external_id"] if chunks else None
        loc = chunks[0].get("locator") if chunks else None
        where = ""
        if loc:
            where = " @" + ",".join(f"{k}={loc[k]}" for k in ("page", "sheet", "range", "line_start", "symbol") if k in loc)
        print(f"[{'HIT' if rank else 'MISS'}] {coll} rank={rank} top={top}{where}  {q}")

        if args.answer:
            body = http.post("/v1/query", json={"collection": coll, "question": q, "top_k": args.top_k}).json()
            cites = [c.get("external_id") for c in body.get("citations", [])]
            print(f"      insufficient={body.get('insufficient_context')} citations={cites}\n      {body.get('answer')}")

    answerable = sum(v["n"] for v in per.values())
    hits = sum(v["hits"] for v in per.values())
    print()
    for coll, v in sorted(per.items()):
        print(f"{coll}: hit@{args.top_k} = {v['hits']}/{v['n']} = {v['hits'] / v['n']:.2f}   MRR = {v['rr'] / v['n']:.2f}")
    hit_rate = hits / answerable if answerable else 0.0
    print(f"TOTAL hit@{args.top_k} = {hits}/{answerable} = {hit_rate:.2f}")
    if args.answer and negatives:
        print(f"negatives handled: {negatives_ok}/{negatives}")
    return 0 if hit_rate >= args.min_hit else 1


if __name__ == "__main__":
    sys.exit(main())
