import type { Metadata } from "next";
import Link from "next/link";
import { VisitingCard } from "@/components/VisitingCard";
import { site } from "@/content/site";

export const metadata: Metadata = {
  title: "Визитка",
  description: `${site.name} — ${site.role}. ${site.tagline}`,
  openGraph: {
    title: `${site.name} — визитка`,
    description: site.tagline,
  },
};

export default function CardPage() {
  return (
    <main id="main" className="visiting-card-page">
      <div className="hero-orb hero-orb-a" />
      <div className="hero-orb hero-orb-b" />
      <div className="grain" />

      <div className="wrap relative z-10 py-20 md:py-28">
        <div className="mb-10 flex flex-wrap items-center justify-between gap-4">
          <Link
            href="/"
            className="text-sm font-medium text-ink/70 transition-colors hover:text-ink"
          >
            ← Полный лендинг
          </Link>
          <p className="eyebrow">Цифровая визитка</p>
        </div>

        <VisitingCard />
      </div>
    </main>
  );
}
