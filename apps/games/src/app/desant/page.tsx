import type { Metadata } from "next";
import Link from "next/link";
import { DesantGame } from "@/components/games/DesantGame";

export const metadata: Metadata = {
  title: "Десант",
  description:
    "Run & Gun в духе Contra / Dendy: беги, прыгай, стреляй. Оригинальный чиптюн в браузере.",
};

export default function DesantPage() {
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
          <p className="eyebrow">Run &amp; Gun</p>
        </div>
        <DesantGame />
      </div>
    </main>
  );
}
