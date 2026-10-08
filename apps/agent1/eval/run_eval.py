"""Eval for the BP1 agent against a running LangGraph Agent Server (:2024).

python apps/agent1/eval/run_eval.py [--url http://127.0.0.1:2024] [--min 0.8] [-v]
Exit code 1 if the pass rate is below --min.
"""
from __future__ import annotations

import argparse
import os
import re
import sys

import httpx
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REFUSAL = re.compile(r"не нашл|не найден|нет информации|нет данных|не относится|вне тем|не могу|только .*проект|"
                     r"не располагаю|отсутствует", re.I)


def _text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(p if isinstance(p, str) else str(p.get("text", "")) for p in content)
    return ""


def ask(client: httpx.Client, question: str) -> tuple[str, int]:
    thread = client.post("/threads", json={}).json()["thread_id"]
    resp = client.post(f"/threads/{thread}/runs/wait", json={
        "assistant_id": "bp1_qa",
        "input": {"messages": [{"role": "user", "content": question}]},
    })
    resp.raise_for_status()
    msgs = resp.json().get("messages") or []
    answer = next((_text(m.get("content")).strip() for m in reversed(msgs)
                   if m.get("type") == "ai" and _text(m.get("content")).strip()), "")
    tool_calls = sum(1 for m in msgs if m.get("type") == "tool")
    return answer, tool_calls


def judge(item: dict, answer: str, tool_calls: int) -> tuple[bool, str]:
    if not answer:
        return False, "пустой ответ"
    if item.get("refuse"):
        cites = "Источники" in answer and re.search(r"(?m)^\s*-\s*\S+\.\w+", answer)
        if cites:
            return False, "цитирует источники на вопрос вне темы"
        return (True, "отказ") if REFUSAL.search(answer) else (False, "нет отказа")
    if tool_calls == 0:
        return False, "не вызвал search_project"
    if not any(s.lower() in answer.lower() for s in item.get("sources", [])):
        return False, f"нет ожидаемых источников {item.get('sources')}"
    kws = item.get("keywords")
    if kws and not any(k.lower() in answer.lower() for k in kws):
        return False, f"нет ключевых слов {kws}"
    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--url", default=os.environ.get("AGENT1_STUDIO_URL", "http://127.0.0.1:2024"))
    ap.add_argument("--min", type=float, default=0.8)
    ap.add_argument("-v", action="store_true", help="print answers")
    args = ap.parse_args()

    with open(os.path.join(HERE, "bp1_questions.yaml"), encoding="utf-8") as f:
        items = yaml.safe_load(f)["questions"]

    passed = 0
    with httpx.Client(base_url=args.url, timeout=180, trust_env=False) as client:
        for item in items:
            try:
                answer, calls = ask(client, item["q"])
                ok, why = judge(item, answer, calls)
            except httpx.HTTPError as exc:
                answer, ok, why = "", False, f"ошибка запроса: {type(exc).__name__}"
            passed += ok
            print(f"[{'PASS' if ok else 'FAIL'}] {item['q']}  -> {why}")
            if args.v or not ok:
                print("    " + answer.replace("\n", "\n    ")[:900])
    rate = passed / len(items)
    print(f"\nBP1 eval: {passed}/{len(items)} = {rate:.2f} (min {args.min})")
    return 0 if rate >= args.min else 1


if __name__ == "__main__":
    sys.exit(main())
