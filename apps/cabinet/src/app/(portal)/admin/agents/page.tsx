import { AgentToggle, QuotaForm } from "@/components/AdminControls";
import { ErrorPanel, PageTitle } from "@/components/ui";
import { BlError, blJson } from "@/lib/bl";
import { requireSession } from "@/lib/session";
import type { Agent } from "@/lib/types";

export const metadata = { title: "Агенты и квота (админ)" };

export default async function AdminAgents() {
  const session = await requireSession("/app/admin/agents");
  let agents: Agent[];
  let quota: number;
  try {
    const [a, s] = await Promise.all([
      blJson<{ items: Agent[] }>("/v1/admin/agents", undefined, session),
      blJson<{ daily_run_quota: number }>("/v1/admin/settings", undefined, session),
    ]);
    agents = a.items;
    quota = s.daily_run_quota;
  } catch (e) {
    return <ErrorPanel detail={e instanceof BlError ? `${e.status}: ${e.message}` : String(e)} />;
  }

  return (
    <>
      <PageTitle eyebrow="Админ-панель" title="Агенты и квота" />
      <section className="panel mb-8 p-6">
        <h2 className="eyebrow mb-3">Суточная квота запусков на пользователя</h2>
        <QuotaForm initial={quota} />
        <p className="mt-3 text-xs text-ink-dim">Защищает расход токенов при открытой регистрации. Сброс в 00:00 UTC.</p>
      </section>

      <h2 className="eyebrow mb-3">Реестр агентов</h2>
      <div className="panel overflow-x-auto">
        <table className="tbl">
          <thead>
            <tr>
              <th>Агент</th>
              <th>Тип</th>
              <th>Включён</th>
            </tr>
          </thead>
          <tbody>
            {agents.map((a) => (
              <tr key={a.id}>
                <td>
                  <span className="font-medium">{a.title}</span>
                  <span className="block text-xs text-ink-dim">{a.id}</span>
                </td>
                <td>
                  <span className="pill">{a.kind}</span>
                </td>
                <td>
                  <AgentToggle id={a.id} enabled={a.enabled} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-4 text-sm text-ink-dim">
        Агент БП1 (<code>bp1-project-qa</code>) выключен, пока граф <code>bp1_qa</code> не добавлен в Agent Server.
      </p>
    </>
  );
}
