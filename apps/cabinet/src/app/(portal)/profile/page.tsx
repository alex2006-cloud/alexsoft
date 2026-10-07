import { ErrorPanel, PageTitle } from "@/components/ui";
import { BlError, blJson } from "@/lib/bl";
import { env } from "@/lib/env";
import { formatDate } from "@/lib/format";
import { requireSession } from "@/lib/session";
import type { Me } from "@/lib/types";

export const metadata = { title: "Профиль" };

export default async function ProfilePage() {
  const session = await requireSession("/app/profile");
  let me: Me;
  try {
    me = await blJson<Me>("/v1/me", undefined, session);
  } catch (e) {
    return <ErrorPanel detail={e instanceof BlError ? `${e.status}: ${e.message}` : String(e)} />;
  }

  return (
    <>
      <PageTitle eyebrow="Кабинет" title="Профиль" />
      <dl className="panel grid gap-x-8 gap-y-4 p-6 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-ink-dim">Имя</dt>
          <dd>{me.name || "—"}</dd>
        </div>
        <div>
          <dt className="text-ink-dim">Пользователь</dt>
          <dd>{me.username}</dd>
        </div>
        <div>
          <dt className="text-ink-dim">Email</dt>
          <dd>{me.email || "—"}</dd>
        </div>
        <div>
          <dt className="text-ink-dim">Роли</dt>
          <dd className="flex gap-2">
            {me.roles.map((r) => (
              <span key={r} className="pill">
                {r}
              </span>
            ))}
          </dd>
        </div>
        <div>
          <dt className="text-ink-dim">Квота запусков сегодня</dt>
          <dd>
            {me.quota.used_today} из {me.quota.daily_limit} (осталось {me.quota.remaining})
          </dd>
        </div>
        <div>
          <dt className="text-ink-dim">Сброс квоты (МСК)</dt>
          <dd>{formatDate(me.quota.resets_at)}</dd>
        </div>
      </dl>
      <p className="mt-6 text-sm text-ink-dim">
        Пароль и данные аккаунта меняются в{" "}
        <a className="text-link" href={`${env.authUrl}/if/user/#/settings`}>
          настройках учётной записи
        </a>
        .
      </p>
    </>
  );
}
