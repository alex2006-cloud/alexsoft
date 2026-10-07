import { ErrorPanel, PageTitle } from "@/components/ui";
import { BlError, blJson } from "@/lib/bl";
import { env } from "@/lib/env";
import { requireSession } from "@/lib/session";
import type { Stats } from "@/lib/types";

export const metadata = { title: "Админ-панель" };

export default async function AdminHome() {
  const session = await requireSession("/app/admin");
  let stats: Stats;
  try {
    stats = await blJson<Stats>("/v1/admin/stats", undefined, session);
  } catch (e) {
    return <ErrorPanel detail={e instanceof BlError ? `${e.status}: ${e.message}` : String(e)} />;
  }
  const cards: [string, number][] = [
    ["Запусков сегодня", stats.runs_today],
    ["Ошибок сегодня", stats.failed_today],
    ["Активных пользователей сегодня", stats.active_users_today],
    ["Запусков всего", stats.runs_total],
  ];
  const links: [string, string, string][] = [
    ["Authentik", env.adminLinks.authentik, "пользователи, группы, потоки входа"],
    ["Grafana", env.adminLinks.grafana, "метрики и логи"],
    ["Metabase", env.adminLinks.metabase, "BI и отчёты"],
    ["LiteLLM", env.adminLinks.litellm, "модели и расход токенов"],
  ];

  return (
    <>
      <PageTitle eyebrow="Админ-панель" title="Сводка" />
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {cards.map(([label, value]) => (
          <div key={label} className="panel p-5">
            <p className="text-xs text-ink-dim">{label}</p>
            <p className="display mt-2 text-3xl">{value}</p>
          </div>
        ))}
      </div>

      <h2 className="eyebrow mb-3 mt-10">По агентам</h2>
      <div className="panel overflow-x-auto">
        <table className="tbl">
          <thead>
            <tr>
              <th>Агент</th>
              <th>Запусков</th>
            </tr>
          </thead>
          <tbody>
            {stats.by_agent.length === 0 ? (
              <tr>
                <td colSpan={2} className="text-ink-dim">
                  Запусков ещё не было.
                </td>
              </tr>
            ) : (
              stats.by_agent.map((a) => (
                <tr key={a.agent_id}>
                  <td>{a.agent_id}</td>
                  <td>{a.runs}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      <h2 className="eyebrow mb-3 mt-10">Инструменты</h2>
      <div className="grid gap-4 sm:grid-cols-2">
        {links.map(([name, href, note]) => (
          <a key={name} href={href} target="_blank" rel="noreferrer" className="panel block p-5 hover:border-white/25">
            <p className="font-medium">{name} ↗</p>
            <p className="mt-1 text-sm text-ink-dim">{note}</p>
          </a>
        ))}
      </div>
    </>
  );
}
