export default function NotFound() {
  return (
    <main className="flex min-h-[80svh] items-center justify-center px-6">
      <div className="text-center">
        <p className="eyebrow">Ошибка</p>
        <h1 className="display mt-4 text-[clamp(3rem,8vw,5rem)]">404</h1>
        <p className="mt-4 text-ink-dim">Такой страницы нет. Вернитесь на витрину.</p>
        <a className="btn btn-primary mt-8" href="/">
          На главную
        </a>
      </div>
    </main>
  );
}
