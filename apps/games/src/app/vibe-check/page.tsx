import type { Metadata } from "next";
import Link from "next/link";
import { VibeCheckGame } from "@/components/games/VibeCheckGame";

export const metadata: Metadata = {
  title: "Вайб-чек",
  description:
    "Зумерская игра на реакцию: поймай зелёную зону вайба за 30 секунд. W или L — решаешь ты.",
};

export default function VibeCheckPage() {
  return (
    <main id="main" className="pb-24 pt-24 md:pb-32 md:pt-28">
      <div className="wrap">
        <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
          <Link
            href="/"
            className="text-sm font-medium text-ink/70 transition-colors hover:text-ink"
          >
            ← Все игры
          </Link>
          <p className="eyebrow">Gen Z</p>
        </div>
        <VibeCheckGame />
      </div>
    </main>
  );
}
