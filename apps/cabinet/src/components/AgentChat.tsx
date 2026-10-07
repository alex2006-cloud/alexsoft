"use client";

import { useEffect, useRef, useState } from "react";

interface Step {
  name: string;
  detail?: string;
}
interface Msg {
  id: number;
  role: "user" | "agent" | "error";
  text: string;
  steps?: Step[];
  pending?: boolean;
  runId?: string;
  traceId?: string | null;
}

const API = "/app/api/bl/v1";

export function AgentChat({
  agentId,
  hint,
  initialRemaining,
  dailyLimit,
}: {
  agentId: string;
  hint?: string | null;
  initialRemaining: number;
  dailyLimit: number;
}) {
  const [messages, setMessages] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [remaining, setRemaining] = useState(initialRemaining);
  const threadId = useRef<string | null>(null);
  const seq = useRef(0);
  const source = useRef<EventSource | null>(null);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => () => source.current?.close(), []);
  useEffect(() => bottom.current?.scrollIntoView({ behavior: "smooth", block: "end" }), [messages]);

  const patch = (id: number, fn: (m: Msg) => Msg) => setMessages((all) => all.map((m) => (m.id === id ? fn(m) : m)));

  async function send() {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    setBusy(true);
    const userMsg: Msg = { id: ++seq.current, role: "user", text };
    const agentMsg: Msg = { id: ++seq.current, role: "agent", text: "", steps: [], pending: true };
    setMessages((m) => [...m, userMsg, agentMsg]);
    const fail = (message: string) => {
      patch(agentMsg.id, (m) => ({ ...m, role: "error", text: message, pending: false }));
      setBusy(false);
    };

    let run: { id: string; thread_id?: string | null };
    try {
      const res = await fetch(`${API}/agents/${encodeURIComponent(agentId)}/runs`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ input: text, ...(threadId.current ? { thread_id: threadId.current } : {}) }),
      });
      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        if (res.status === 401) return fail("Сессия истекла. Обновите страницу и войдите заново.");
        return fail(body.detail || body.title || `Ошибка ${res.status}`);
      }
      const q = res.headers.get("x-quota-remaining");
      if (q !== null) setRemaining(Number(q));
      run = await res.json();
    } catch {
      return fail("Нет связи с сервером.");
    }

    patch(agentMsg.id, (m) => ({ ...m, runId: run.id }));
    const es = new EventSource(`${API}/runs/${run.id}/events`);
    source.current = es;
    const finish = () => {
      es.close();
      setBusy(false);
    };
    es.addEventListener("step", (e) => {
      const d = JSON.parse((e as MessageEvent).data) as Step;
      patch(agentMsg.id, (m) => ({ ...m, steps: [...(m.steps ?? []), d] }));
    });
    es.addEventListener("message", (e) => {
      const d = JSON.parse((e as MessageEvent).data) as { content: string };
      patch(agentMsg.id, (m) => ({ ...m, text: d.content }));
    });
    es.addEventListener("done", (e) => {
      const d = JSON.parse((e as MessageEvent).data) as { run: { thread_id?: string | null; trace_id?: string | null; output?: string | null } };
      if (d.run.thread_id) threadId.current = d.run.thread_id;
      patch(agentMsg.id, (m) => ({ ...m, text: d.run.output ?? m.text, pending: false, traceId: d.run.trace_id }));
      finish();
    });
    es.addEventListener("error", (e) => {
      if (e instanceof MessageEvent && e.data) {
        const d = JSON.parse(e.data) as { message: string };
        patch(agentMsg.id, (m) => ({ ...m, role: "error", text: d.message, pending: false }));
        finish();
      } else if (es.readyState === EventSource.CLOSED) {
        patch(agentMsg.id, (m) => (m.pending ? { ...m, role: "error", text: "Соединение потеряно.", pending: false } : m));
        finish();
      } // otherwise EventSource reconnects and the server replays from Last-Event-ID
    });
  }

  function reset() {
    source.current?.close();
    threadId.current = null;
    setMessages([]);
    setBusy(false);
  }

  return (
    <div className="panel flex min-h-[28rem] flex-col">
      <div className="flex-1 space-y-4 overflow-y-auto p-5" aria-live="polite">
        {messages.length === 0 ? (
          <p className="py-10 text-center text-sm text-ink-dim">{hint ? `Например: ${hint}` : "Напишите запрос агенту."}</p>
        ) : null}
        {messages.map((m) => (
          <div key={m.id} className={m.role === "user" ? "flex justify-end" : "flex justify-start"}>
            <div
              className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-4 py-3 text-sm leading-relaxed ${
                m.role === "user"
                  ? "bg-blue text-white"
                  : m.role === "error"
                    ? "border border-bad/40 bg-bad/10 text-bad"
                    : "border border-line bg-black"
              }`}
            >
              {m.steps && m.steps.length > 0 ? (
                <ul className="mb-2 space-y-0.5 border-b border-line pb-2 text-xs text-ink-dim">
                  {m.steps.map((s, i) => (
                    <li key={i}>
                      <span className="text-ink/70">{s.name}</span>
                      {s.detail ? <span> — {s.detail}</span> : null}
                    </li>
                  ))}
                </ul>
              ) : null}
              {m.text || (m.pending ? <span className="text-ink-dim">Думаю…</span> : null)}
              {m.traceId ? <p className="mt-2 text-[11px] text-ink-dim">trace: {m.traceId}</p> : null}
            </div>
          </div>
        ))}
        <div ref={bottom} />
      </div>

      <form
        className="border-t border-line p-4"
        onSubmit={(e) => {
          e.preventDefault();
          void send();
        }}
      >
        <div className="flex gap-3">
          <textarea
            className="input min-h-12 resize-none"
            rows={2}
            maxLength={8000}
            placeholder={hint ?? "Ваш запрос"}
            value={input}
            disabled={busy}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                void send();
              }
            }}
            aria-label="Запрос агенту"
          />
          <button className="btn self-end" type="submit" disabled={busy || !input.trim() || remaining <= 0}>
            {busy ? "…" : "Отправить"}
          </button>
        </div>
        <div className="mt-3 flex items-center justify-between text-xs text-ink-dim">
          <span>
            Осталось запусков сегодня: {remaining} из {dailyLimit}
          </span>
          <button type="button" className="hover:text-ink" onClick={reset} disabled={busy}>
            Новая беседа
          </button>
        </div>
      </form>
    </div>
  );
}
