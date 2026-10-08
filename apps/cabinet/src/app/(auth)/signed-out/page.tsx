export const metadata = { title: "Вы вышли" };

export default function SignedOut() {
  return (
    <main className="wrap py-24">
      <div className="panel mx-auto max-w-lg p-8">
        <h1 className="display text-2xl">Вы вышли из кабинета</h1>
        <div className="mt-6 flex gap-3">
          <a className="btn" href="/app/api/auth/login?returnTo=%2Fapp">
            Войти снова
          </a>
          <a className="btn btn-ghost" href="/">
            На главную
          </a>
        </div>
      </div>
    </main>
  );
}
