import Link from "next/link";
import { notFound } from "next/navigation";
import { ErrorPanel, PageTitle, StatusPill } from "@/components/ui";
import { BlError, blJson } from "@/lib/bl";
import { formatDate } from "@/lib/format";
import { requireSession } from "@/lib/session";
import type { Run } from "@/lib/types";

export default async function RunPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const session = await requireSession(`/app/runs/${id}`);
  let run: Run;
  try {
    run = await blJson<Run>(`/v1/runs/${encodeURIComponent(id)}`, undefined, session);
  } catch (e) {
    if (e instanceof BlError && (e.status === 404 || e.status === 422)) notFound();
    return <ErrorPanel detail={e instanceof BlError ? `${e.status}: ${e.message}` : String(e)} />;
  }

  return (
    <>
      <Link href="/runs" className="mb-4 inline-block text-sm text-link">
        ← История
      </Link>
      <PageTitle eyebrow={run.agent_id} title="Запуск">
        <StatusPill status={run.status} />
      </PageTitle>
      <div className="space-y-4">
        <section className="panel p-6">
          <h2 className="eyebrow mb-2">Запрос</h2>
          <p className="whitespace-pre-wrap text-sm">{run.input}</p>
        </section>
        <section className="panel p-6">
          <h2 className="eyebrow mb-2">{run.status === "failed" ? "Ошибка" : "Ответ"}</h2>
          <p className={`whitespace-pre-wrap text-sm ${run.status === "failed" ? "text-bad" : ""}`}>
            {run.status === "failed" ? run.error : run.output || "—"}
          </p>
        </section>
        <dl className="panel grid gap-x-8 gap-y-3 p-6 text-sm sm:grid-cols-2">
          <div>
            <dt className="text-ink-dim">Создан (МСК)</dt>
            <dd>{formatDate(run.created_at)}</dd>
          </div>
          <div>
            <dt className="text-ink-dim">Завершён (МСК)</dt>
            <dd>{formatDate(run.finished_at)}</dd>
          </div>
          <div>
            <dt className="text-ink-dim">Run ID</dt>
            <dd className="break-all">{run.id}</dd>
          </div>
          <div>
            <dt className="text-ink-dim">Trace ID</dt>
            <dd className="break-all">{run.trace_id ?? "—"}</dd>
          </div>
        </dl>
        <Link href={`/agents/${run.agent_id}`} className="btn inline-flex">
          Спросить ещё
        </Link>
      </div>
    </>
  );
}
