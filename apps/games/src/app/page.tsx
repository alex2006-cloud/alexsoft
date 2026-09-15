import type { Metadata } from "next";
import Link from "next/link";
import { games, gamesCatalog } from "@/content/games";

export const metadata: Metadata = {
  title: "Игры",
  description: gamesCatalog.lead,
};

export default function GamesCatalogPage() {
  return (
    <main id="main" className="pb-24 pt-24 md:pb-32 md:pt-28">
      <div className="wrap">
        <div className="mb-10 flex flex-wrap items-center justify-between gap-4">
          <a
            href="/#lab"
            className="text-sm font-medium text-ink/70 transition-colors hover:text-ink"
          >
            ← Лаборатория
          </a>
          <p className="eyebrow">alexsoft · Lab</p>
        </div>

        <h1 className="display text-[clamp(2.2rem,5vw,3.4rem)]">{gamesCatalog.title}</h1>
        <p className="mt-5 max-w-2xl text-[1.15rem] leading-relaxed text-ink-dim">
          {gamesCatalog.lead}
        </p>

        <ul className="mt-14 grid gap-5 md:grid-cols-2">
          {games.map((game) => (
            <li key={game.slug}>
              <Link
                href={game.href}
                className="group block overflow-hidden rounded-[28px] border border-line bg-panel transition-[border-color,transform] duration-200 hover:border-white/25 hover:scale-[1.01]"
              >
                <div
                  className={`aspect-[16/9] bg-gradient-to-br ${
                    game.gradient ?? "from-[#1e3a8a] via-[#0f172a] to-black"
                  }`}
                />
                <div className="px-6 py-6">
                  <div className="flex items-center justify-between gap-3">
                    <div>
                      <h2 className="display text-[1.55rem] transition-colors group-hover:text-white">
                        {game.name}
                      </h2>
                      <p className="mt-1 text-sm text-ink-dim">{game.subtitle}</p>
                    </div>
                    <span className="rounded-full border border-line bg-black/30 px-3 py-1 text-xs font-medium text-ink-dim">
                      {game.status}
                    </span>
                  </div>
                  <p className="mt-3 text-[0.98rem] leading-relaxed text-ink/70">
                    {game.blurb}
                  </p>
                  <p className="mt-4 text-sm font-medium text-link">Играть →</p>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}
