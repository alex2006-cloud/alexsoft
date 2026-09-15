import Link from "next/link";

/** Links to landing use plain <a> so they are not prefixed with basePath /games. */
export function GamesNav() {
  return (
    <header className="fixed inset-x-0 top-0 z-50 border-b border-white/10 bg-black/80 backdrop-blur-md">
      <nav className="wrap flex h-12 items-center justify-between text-[12px] tracking-tight text-ink/90">
        <a href="/" className="font-medium text-ink">
          alexsoft
        </a>
        <div className="flex items-center gap-5">
          <Link href="/" className="text-ink">
            Игры
          </Link>
          <a
            href="/#lab"
            className="rounded-full bg-blue px-3.5 py-1.5 text-[12px] font-medium text-white transition-colors hover:bg-blue-hover"
          >
            Лаборатория
          </a>
        </div>
      </nav>
    </header>
  );
}
