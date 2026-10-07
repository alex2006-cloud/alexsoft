import Link from "next/link";
import { ErrorPanel, PageTitle, StatusPill } from "@/components/ui";
import { BlError, blJson } from "@/lib/bl";
import { formatDate, truncate } from "@/lib/format";
import { requireSession } from "@/lib/session";
import type { Page, Run } from "@/lib/types";

export const metadata = { title: "Запуски (админ)" };
const PAGE = 30;

export default async function AdminRuns({
  searchParams,
}: {
  searchParams: Promise<{ page?: string; status?: string; agent_id?: string }>;
}) {
  const session = await requireSession("/app/admin/runs");
  const sp = await searchParams;
  const page = Math.max(1, Number(sp.page) || 1);
  const q = new URLSearchParams({ limit: String(PAGE), offset: String((page - 1) * PAGE) });
  if (sp.status) q.set("status", sp.status);
  if (sp.agent_id) q.set("agent_id", sp.agent_id);

  let data: Page<Run>;
  try {
    data = await blJson<Page<Run>>(`/v1/admin/runs?${q}`, undefined, session);
  } catch (e) {
    return <ErrorPanel detail={e instanceof BlError ? `${e.status}: ${e.message}` : String(e)} />;
  }
  const pages = Math.max(1, Math.ceil(data.total / PAGE));
  const keep = (p: number) => {
    const n = new URLSearchParams();
    if (sp.status) n.set("status", sp.status);
    if (sp.agent_id) n.set("agent_id", sp.agent_id);
    n.set("page", String(p));
    return `/admin/runs?${n}`;
  };

  return (
    <>
      <PageTitle eyebrow="Админ-панель" title="Запуски" />
      <div className="mb-4 flex flex-wrap gap-2 text-sm">
        {["", "succeeded", "failed", "running"].map((s) => (
          <Link
            key={s || "all"}
            href={s ? `/admin/runs?status=${s}` : "/admin/runs"}
            className={`btn btn-ghost ${sp.status === s || (!sp.status && !s) ? "border-white/40" : ""}`}
          >
            {s || "все"}
          </Link>
        ))}
      </div>
      <div className="panel overflow-x-auto">
        <table className="tbl">
          <thead>
            <tr>
              <th>Когда (МСК)</th>
              <th>Пользователь</th>
              <th>Агент</th>
              <th>Запрос</th>
              <th>Статус</th>
            </tr>
          </thead>
          <tbody>
            {data.items.length === 0 ? (
              <tr>
                <td colSpan={5} className="text-ink-dim">
                  Нет запусков.
                </td>
              </tr>
            ) : (
              data.items.map((r) => (
                <tr key={r.id}>
                  <td className="whitespace-nowrap text-ink-dim">{formatDate(r.created_at)}</td>
                  <td>{r.username || r.user_sub.slice(0, 8)}</td>
                  <td>{r.agent_id}</td>
                  <td title={r.error ?? undefined}>{truncate(r.input, 80)}</td>
                  <td>
                    <StatusPill status={r.status} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
      {pages > 1 ? (
        <div className="mt-6 flex items-center gap-4 text-sm">
          {page > 1 ? (
            <Link href={keep(page - 1)} className="text-link">
              ← Назад
            </Link>
          ) : null}
          <span className="text-ink-dim">
            {page} / {pages}
          </span>
          {page < pages ? (
            <Link href={keep(page + 1)} className="text-link">
              Дальше →
            </Link>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
