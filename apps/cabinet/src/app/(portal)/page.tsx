import Link from "next/link";
import { ErrorPanel, PageTitle, StatusPill } from "@/components/ui";
import { BlError, blJson } from "@/lib/bl";
import { formatDate, truncate } from "@/lib/format";
import { requireSession } from "@/lib/session";
import type { Agent, Me, Page, Run } from "@/lib/types";

export const metadata = { title: "Агенты" };

export default async function Dashboard() {
  const session = await requireSession();
  let data: { me: Me; agents: Agent[]; runs: Run[] };
  try {
    const [me, agents, runs] = await Promise.all([
      blJson<Me>("/v1/me", undefined, session),
      blJson<{ items: Agent[] }>("/v1/agents", undefined, session),
      blJson<Page<Run>>("/v1/runs?limit=5", undefined, session),
    ]);
    data = { me, agents: agents.items, runs: runs.items };
  } catch (e) {
    return <ErrorPanel detail={e instanceof BlError ? `${e.status}: ${e.message}` : String(e)} />;
  }
  const { me, agents, runs } = data;

  return (
    <>
      <PageTitle eyebrow="Личный кабинет" title={`Здравствуйте, ${me.name || me.username}`}>
        <div className="panel px-5 py-3 text-sm">
          <span className="text-ink-dim">Запусков сегодня: </span>
          <span className="font-medium">
            {me.quota.used_today} / {me.quota.daily_limit}
          </span>
        </div>
      </PageTitle>

      <h2 className="eyebrow mb-4">Агенты</h2>
      {agents.length === 0 ? (
        <div className="panel p-6 text-ink-dim">Пока нет доступных агентов.</div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {agents.map((a) => (
            <Link key={a.id} href={`/agents/${a.id}`} className="panel block p-6 transition-colors hover:border-white/25">
              <div className="mb-2 flex items-center justify-between gap-3">
                <h3 className="display text-xl">{a.title}</h3>
                <span className="pill">{a.kind === "echo" ? "демо" : "LLM"}</span>
              </div>
              <p className="text-sm leading-relaxed text-ink-dim">{a.description}</p>
              <p className="mt-4 text-sm text-link">Открыть →</p>
            </Link>
          ))}
        </div>
      )}

      <div className="mb-4 mt-12 flex items-center justify-between">
        <h2 className="eyebrow">Последние запуски</h2>
        <Link href="/runs" className="text-sm text-link">
          Вся история
        </Link>
      </div>
      {runs.length === 0 ? (
        <div className="panel p-6 text-ink-dim">Запусков ещё не было — выберите агента выше.</div>
      ) : (
        <div className="panel overflow-x-auto">
          <table className="tbl">
            <thead>
              <tr>
                <th>Когда</th>
                <th>Агент</th>
                <th>Запрос</th>
                <th>Статус</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((r) => (
                <tr key={r.id}>
                  <td className="whitespace-nowrap text-ink-dim">{formatDate(r.created_at)}</td>
                  <td>{r.agent_id}</td>
                  <td>
                    <Link href={`/runs/${r.id}`} className="hover:text-link">
                      {truncate(r.input, 80)}
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
    </>
  );
}
