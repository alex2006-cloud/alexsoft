const REASONS: Record<string, string> = {
  idp: "Сервис входа (Authentik) недоступен. Убедитесь, что он запущен, и повторите попытку.",
  denied: "Вход отменён.",
  state: "Сессия входа не найдена или устарела. Начните вход заново.",
  expired: "Время входа истекло. Начните заново.",
  exchange: "Не удалось завершить вход. Повторите попытку.",
  claims: "Сервис входа вернул неполные данные профиля.",
};

export const metadata = { title: "Ошибка входа" };

export default async function LoginError({ searchParams }: { searchParams: Promise<{ reason?: string }> }) {
  const { reason } = await searchParams;
  return (
    <main className="wrap py-24">
      <div className="panel mx-auto max-w-lg p-8">
        <h1 className="display text-2xl">Не удалось войти</h1>
        <p className="mt-3 text-ink-dim">{REASONS[reason ?? ""] ?? "Что-то пошло не так."}</p>
        <div className="mt-6 flex gap-3">
          <a className="btn" href="/app/api/auth/login">
            Войти
          </a>
          <a className="btn btn-ghost" href="/">
            На главную
          </a>
        </div>
      </div>
    </main>
  );
}
