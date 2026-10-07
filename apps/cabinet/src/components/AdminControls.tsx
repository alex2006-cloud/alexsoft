"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

const API = "/app/api/bl/v1/admin";

async function call(path: string, method: string, body: unknown): Promise<string | null> {
  try {
    const res = await fetch(`${API}${path}`, {
      method,
      headers: { "content-type": "application/json" },
      body: JSON.stringify(body),
    });
    if (res.ok) return null;
    const j = await res.json().catch(() => ({}));
    return j.detail || j.title || `Ошибка ${res.status}`;
  } catch {
    return "Нет связи с сервером";
  }
}

function Toggle({ on, busy, onClick, label }: { on: boolean; busy: boolean; onClick: () => void; label: string }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label={label}
      disabled={busy}
      onClick={onClick}
      className={`relative h-6 w-11 rounded-full transition-colors disabled:opacity-50 ${on ? "bg-ok" : "bg-line"}`}
    >
      <span className={`absolute top-0.5 h-5 w-5 rounded-full bg-white transition-all ${on ? "left-[1.375rem]" : "left-0.5"}`} />
    </button>
  );
}

export function AgentToggle({ id, enabled }: { id: string; enabled: boolean }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  return (
    <span className="flex items-center gap-3">
      <Toggle
        on={enabled}
        busy={busy}
        label={`Агент ${id}`}
        onClick={async () => {
          setBusy(true);
          setErr(await call(`/agents/${encodeURIComponent(id)}`, "PATCH", { enabled: !enabled }));
          setBusy(false);
          router.refresh();
        }}
      />
      {err ? <span className="text-xs text-bad">{err}</span> : null}
    </span>
  );
}

export function UserActiveToggle({ id, active }: { id: number; active: boolean }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  return (
    <span className="flex items-center gap-3">
      <Toggle
        on={active}
        busy={busy}
        label={`Пользователь ${id}`}
        onClick={async () => {
          if (active && !confirm("Деактивировать пользователя? Он не сможет войти.")) return;
          setBusy(true);
          setErr(await call(`/users/${id}`, "PATCH", { is_active: !active }));
          setBusy(false);
          router.refresh();
        }}
      />
      {err ? <span className="text-xs text-bad">{err}</span> : null}
    </span>
  );
}

export function QuotaForm({ initial }: { initial: number }) {
  const router = useRouter();
  const [value, setValue] = useState(String(initial));
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);
  return (
    <form
      className="flex items-center gap-3"
      onSubmit={async (e) => {
        e.preventDefault();
        setBusy(true);
        const err = await call("/settings", "PUT", { daily_run_quota: Number(value) });
        setMsg(err ? { ok: false, text: err } : { ok: true, text: "Сохранено" });
        setBusy(false);
        router.refresh();
      }}
    >
      <input
        className="input w-32"
        type="number"
        min={0}
        max={10000}
        value={value}
        onChange={(e) => setValue(e.target.value)}
        aria-label="Запусков в сутки"
      />
      <button className="btn" type="submit" disabled={busy}>
        Сохранить
      </button>
      {msg ? <span className={`text-sm ${msg.ok ? "text-ok" : "text-bad"}`}>{msg.text}</span> : null}
    </form>
  );
}
