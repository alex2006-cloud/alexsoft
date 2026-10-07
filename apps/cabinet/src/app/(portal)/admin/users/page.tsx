import { UserActiveToggle } from "@/components/AdminControls";
import { ErrorPanel, PageTitle } from "@/components/ui";
import { BlError, blJson } from "@/lib/bl";
import { env } from "@/lib/env";
import { formatDate } from "@/lib/format";
import { requireSession } from "@/lib/session";
import type { AdminUser, Page } from "@/lib/types";

export const metadata = { title: "Пользователи (админ)" };

export default async function AdminUsers({ searchParams }: { searchParams: Promise<{ search?: string }> }) {
  const session = await requireSession("/app/admin/users");
  const { search } = await searchParams;
  let data: Page<AdminUser>;
  try {
    const q = new URLSearchParams({ limit: "100" });
    if (search) q.set("search", search);
    data = await blJson<Page<AdminUser>>(`/v1/admin/users?${q}`, undefined, session);
  } catch (e) {
    return <ErrorPanel title="Пользователи недоступны" detail={e instanceof BlError ? `${e.status}: ${e.message}` : String(e)} />;
  }

  return (
    <>
      <PageTitle eyebrow="Админ-панель" title="Пользователи">
        <form className="flex gap-2" action="/app/admin/users">
          <input className="input" name="search" defaultValue={search} placeholder="Поиск" aria-label="Поиск" />
          <button className="btn btn-ghost" type="submit">
            Найти
          </button>
        </form>
      </PageTitle>
      <div className="panel overflow-x-auto">
        <table className="tbl">
          <thead>
            <tr>
              <th>Пользователь</th>
              <th>Email</th>
              <th>Группы</th>
              <th>Последний вход (МСК)</th>
              <th>Активен</th>
            </tr>
          </thead>
          <tbody>
            {data.items.map((u) => (
              <tr key={u.id}>
                <td>
                  {u.username}
                  {u.name ? <span className="block text-xs text-ink-dim">{u.name}</span> : null}
                </td>
                <td className="text-ink-dim">{u.email || "—"}</td>
                <td className="space-x-1">
                  {u.groups.map((g) => (
                    <span key={g} className="pill">
                      {g}
                    </span>
                  ))}
                </td>
                <td className="whitespace-nowrap text-ink-dim">{formatDate(u.last_login)}</td>
                <td>
                  <UserActiveToggle id={u.id} active={u.is_active} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-4 text-sm text-ink-dim">
        Группы и права меняются в{" "}
        <a className="text-link" href={env.adminLinks.authentik} target="_blank" rel="noreferrer">
          Authentik Admin
        </a>
        . Всего: {data.total}.
      </p>
    </>
  );
}
