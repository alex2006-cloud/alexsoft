import Link from "next/link";
import type { Session } from "@/lib/session";

export function Header({ session }: { session: Session }) {
  const admin = session.roles.includes("admin");
  return (
    <header className="sticky top-0 z-40 border-b border-white/10 bg-black/80 backdrop-blur">
      <nav className="wrap flex h-12 items-center justify-between text-[13px] text-ink/90">
        <div className="flex items-center gap-6">
          {/* the landing is a different app (static): plain link, not next/link */}
          <a href="/" className="font-medium text-ink">
            alexsoft
          </a>
          <Link href="/" className="text-ink-dim hover:text-ink">
            Агенты
          </Link>
          <Link href="/runs" className="text-ink-dim hover:text-ink">
            История
          </Link>
          {admin ? (
            <Link href="/admin" className="text-ink-dim hover:text-ink">
              Админ-панель
            </Link>
          ) : null}
        </div>
        <div className="flex items-center gap-4">
          <Link href="/profile" className="text-ink-dim hover:text-ink">
            {session.name || session.username}
          </Link>
          <form action="/app/api/auth/logout" method="post">
            <button type="submit" className="text-ink-dim hover:text-ink">
              Выйти
            </button>
          </form>
        </div>
      </nav>
    </header>
  );
}
