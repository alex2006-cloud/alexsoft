import type { Metadata } from "next";
import Link from "next/link";
import { ContourGame } from "@/components/games/ContourGame";

export const metadata: Metadata = {
  title: "Контур",
  description:
    "C4 Puzzle: соберите системный контекст Personal Ecosystem Lab — посетитель, alexsoft, LLM API и GitHub.",
};

export default function ContourPage() {
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
          <p className="eyebrow">C4 Puzzle</p>
        </div>
        <ContourGame />
      </div>
    </main>
  );
}
