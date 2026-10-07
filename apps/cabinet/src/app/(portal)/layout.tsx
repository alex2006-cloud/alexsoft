import { Header } from "@/components/Header";
import { requireSession } from "@/lib/session";

export const dynamic = "force-dynamic";

export default async function PortalLayout({ children }: { children: React.ReactNode }) {
  const session = await requireSession();

  if (session.roles.length === 0) {
    return (
      <>
        <Header session={session} />
        <main className="wrap py-16">
          <div className="panel p-8">
            <h1 className="display text-2xl">Нет доступа</h1>
            <p className="mt-3 text-ink-dim">
              Ваша учётная запись ({session.username}) не входит в группу пользователей кабинета. Обратитесь к
              администратору или зарегистрируйтесь заново.
            </p>
          </div>
        </main>
      </>
    );
  }

  return (
    <>
      <Header session={session} />
      <main id="main" className="wrap py-10">
        {children}
      </main>
    </>
  );
}
