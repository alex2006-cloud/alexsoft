import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { ImageViewer } from "@/components/ImageViewer";
import { formatSize, getPortfolioItem, portfolioData } from "@/content/portfolio";

export const dynamicParams = false;

type Params = { id: string };

export function generateStaticParams(): Params[] {
  return portfolioData.items.filter((item) => item.pageHref).map((item) => ({ id: item.id }));
}

export async function generateMetadata({ params }: { params: Promise<Params> }): Promise<Metadata> {
  const { id } = await params;
  const item = getPortfolioItem(id);
  if (!item) return {};
  return {
    title: `${item.title} · Портфолио`,
    description: item.summary,
  };
}

export default async function PortfolioItemPage({ params }: { params: Promise<Params> }) {
  const { id } = await params;
  const item = getPortfolioItem(id);
  if (!item || !item.pageHref) notFound();

  const isText = item.view === "text";
  const images =
    item.view === "gallery"
      ? (item.images ?? [])
      : item.view === "image" && item.href
        ? [{ label: item.title, src: item.href }]
        : [];

  return (
    <main id="main" className="pb-24 pt-28 md:pt-32">
      <div className={isText ? "wrap-narrow" : "wrap"}>
        <Link href="/#portfolio" className="link text-sm">
          ← Портфолио
        </Link>

        <p className="eyebrow mt-8">
          {item.kind} · {item.format}
        </p>
        <h1 className="display mt-3 text-[clamp(1.9rem,5vw,3rem)]">
          <span className="mr-3" aria-hidden="true">
            {item.emoji}
          </span>
          {item.title}
        </h1>
        <p className="mt-4 max-w-2xl text-[1.1rem] leading-relaxed text-ink/75">{item.summary}</p>

        <div className="mt-6 flex flex-wrap items-center gap-x-1 gap-y-2">
          <span className="mr-1 text-sm text-ink-dim">Скачать:</span>
          {item.downloads.map((d) => (
            <a key={d.href} className="btn btn-ghost min-h-10 px-3 text-[0.95rem]" href={d.href} download>
              {d.label}
              <span className="ml-1.5 text-xs text-ink-dim">{formatSize(d.size)}</span>
            </a>
          ))}
        </div>

        <div className="mt-10">
          {isText && item.html ? (
            <article
              className="prose-doc rounded-[28px] bg-panel px-6 py-8 md:px-10 md:py-10"
              dangerouslySetInnerHTML={{ __html: item.html }}
            />
          ) : (
            <ImageViewer images={images} title={item.title} />
          )}
        </div>
      </div>
    </main>
  );
}
