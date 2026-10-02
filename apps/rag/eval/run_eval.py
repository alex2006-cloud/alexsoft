"""Retrieval / answer quality check against a running RAG service.

    python eval/run_eval.py                 # retrieval only: hit@k and MRR (needs embeddings, no chat LLM)
    python eval/run_eval.py --answer        # also /v1/query: citations and insufficient_context checks
Exit code 1 if hit@k is below --min-hit.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import httpx
import yaml

from alexsoft_rag.config import get_settings


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default="project-docs")
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
    hits = rr_sum = answerable = 0
    negatives_ok = negatives = 0

    for item in data["questions"]:
        q = item["q"]
        if item.get("answerable") is False:
            negatives += 1
            if args.answer:
                body = http.post("/v1/query", json={"collection": args.collection, "question": q, "top_k": args.top_k}).json()
                ok = body.get("insufficient_context") is True
                negatives_ok += ok
                print(f"[{'OK ' if ok else 'BAD'}] (negative) {q}\n      answer={body.get('answer')!r}")
            continue

        answerable += 1
        r = http.post("/v1/search", json={"collection": args.collection, "query": q, "top_k": args.top_k})
        r.raise_for_status()
        chunks = r.json()["chunks"]
        rank = next(
            (i for i, c in enumerate(chunks, 1) if any(e in (c.get("external_id") or "") for e in item["expect_any"])),
            None,
        )
        hits += rank is not None
        rr_sum += 1 / rank if rank else 0
        top = chunks[0]["external_id"] if chunks else None
        print(f"[{'HIT' if rank else 'MISS'}] rank={rank} top={top}  {q}")

        if args.answer:
            body = http.post("/v1/query", json={"collection": args.collection, "question": q, "top_k": args.top_k}).json()
            cites = [c.get("external_id") for c in body.get("citations", [])]
            print(f"      insufficient={body.get('insufficient_context')} citations={cites}\n      {body.get('answer')}")

    hit_rate = hits / answerable if answerable else 0.0
    print(f"\nhit@{args.top_k} = {hits}/{answerable} = {hit_rate:.2f}   MRR = {rr_sum / max(answerable, 1):.2f}")
    if args.answer and negatives:
        print(f"negatives handled: {negatives_ok}/{negatives}")
    return 0 if hit_rate >= args.min_hit else 1


if __name__ == "__main__":
    sys.exit(main())
