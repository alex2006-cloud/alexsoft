import Link from "next/link";
import { ErrorPanel, PageTitle, StatusPill } from "@/components/ui";
import { BlError, blJson } from "@/lib/bl";
import { formatDate, truncate } from "@/lib/format";
import { requireSession } from "@/lib/session";
import type { Page, Run } from "@/lib/types";

export const metadata = { title: "История" };
const PAGE = 20;

export default async function RunsPage({ searchParams }: { searchParams: Promise<{ page?: string }> }) {
  const session = await requireSession("/app/runs");
  const page = Math.max(1, Number((await searchParams).page) || 1);
  let data: Page<Run>;
  try {
    data = await blJson<Page<Run>>(`/v1/runs?limit=${PAGE}&offset=${(page - 1) * PAGE}`, undefined, session);
  } catch (e) {
    return <ErrorPanel detail={e instanceof BlError ? `${e.status}: ${e.message}` : String(e)} />;
  }
  const pages = Math.max(1, Math.ceil(data.total / PAGE));

  return (
    <>
      <PageTitle eyebrow="Кабинет" title="История запусков" />
      {data.items.length === 0 ? (
        <div className="panel p-6 text-ink-dim">Запусков пока нет.</div>
      ) : (
        <div className="panel overflow-x-auto">
          <table className="tbl">
            <thead>
              <tr>
                <th>Когда (МСК)</th>
                <th>Агент</th>
                <th>Запрос</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.id}>
                  <td className="whitespace-nowrap text-ink-dim">{formatDate(r.created_at)}</td>
                  <td>{r.agent_id}</td>
                  <td>
                    <Link href={`/runs/${r.id}`} className="hover:text-link">
                      {truncate(r.input, 100)}
                    </Link>
                  </td>
                  <td>
                    <StatusPill status={r.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      {pages > 1 ? (
        <div className="mt-6 flex items-center gap-4 text-sm">
          {page > 1 ? (
            <Link href={`/runs?page=${page - 1}`} className="text-link">
              ← Назад
            </Link>
          ) : null}
          <span className="text-ink-dim">
            {page} / {pages}
          </span>
          {page < pages ? (
            <Link href={`/runs?page=${page + 1}`} className="text-link">
              Дальше →
            </Link>
          ) : null}
        </div>
      ) : null}
    </>
  );
}
