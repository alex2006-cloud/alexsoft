import type { RunStatus } from "@/lib/types";

const STATUS: Record<RunStatus, { label: string; cls: string }> = {
  queued: { label: "в очереди", cls: "text-ink-dim" },
  running: { label: "выполняется", cls: "text-warn" },
  succeeded: { label: "готово", cls: "text-ok" },
  failed: { label: "ошибка", cls: "text-bad" },
};

export function StatusPill({ status }: { status: RunStatus }) {
  const s = STATUS[status];
  return <span className={`pill ${s.cls}`}>{s.label}</span>;
}

export function ErrorPanel({ title = "Не удалось загрузить данные", detail }: { title?: string; detail?: string }) {
  return (
    <div className="panel p-6">
      <p className="font-medium text-bad">{title}</p>
      {detail ? <p className="mt-1 text-sm text-ink-dim">{detail}</p> : null}
    </div>
  );
}

export function PageTitle({ eyebrow, title, children }: { eyebrow?: string; title: string; children?: React.ReactNode }) {
  return (
    <div className="mb-8 flex flex-wrap items-end justify-between gap-4">
      <div>
        {eyebrow ? <p className="eyebrow mb-2">{eyebrow}</p> : null}
        <h1 className="display text-3xl md:text-4xl">{title}</h1>
      </div>
      {children}
    </div>
  );
}
