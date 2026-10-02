import type { ReactNode } from "react";
import Link from "next/link";
import { Reveal } from "@/components/Reveal";
import { portfolio } from "@/content/site";
import { portfolioData, type PortfolioItem } from "@/content/portfolio";

function itemHref(item: PortfolioItem): { href: string; external?: boolean; download?: boolean } {
  if (item.pageHref) return { href: item.pageHref };
  if (item.view === "download") {
    return { href: item.downloads[0]?.href ?? item.href ?? "#", download: true };
  }
  return { href: item.href ?? "#", external: true };
}

function ItemSnap({ item }: { item: PortfolioItem }) {
  if (item.cover) {
    return <img src={item.cover} alt="" className="portfolio-item-tip-snap-img" />;
  }

  if (item.html) {
    return (
      <span className="portfolio-item-tip-snap-doc">
        <span
          className="portfolio-item-tip-snap-doc-scale"
          dangerouslySetInnerHTML={{ __html: item.html }}
        />
      </span>
    );
  }

  if (item.view === "html" && item.href) {
    return (
      <iframe
        className="portfolio-item-tip-snap-frame"
        src={item.href}
        title=""
        loading="lazy"
        tabIndex={-1}
      />
    );
  }

  return (
    <span className="portfolio-item-tip-snap-file">
      <span className="portfolio-item-tip-snap-emoji">{item.emoji}</span>
      <span className="portfolio-item-tip-snap-format">{item.format || item.kind}</span>
    </span>
  );
}

function ItemTip({ item }: { item: PortfolioItem }) {
  return (
    <span className="portfolio-item-tip" aria-hidden="true">
      <span className="portfolio-item-tip-summary">{item.summary}</span>
      <span className="portfolio-item-tip-snap">
        <ItemSnap item={item} />
      </span>
    </span>
  );
}

function ItemRow({ item, tipSide }: { item: PortfolioItem; tipSide: "left" | "right" }) {
  const target = itemHref(item);
  const wrapClass = `portfolio-item portfolio-item--tip-${tipSide} group relative`;
  const linkClass =
    "flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors group-hover:bg-white/[0.06] group-focus-within:bg-white/[0.06]";

  const label = (
    <>
      <span className="shrink-0 text-[1.15rem] leading-none" aria-hidden="true">
        {item.emoji}
      </span>
      <span className="min-w-0 flex-1 text-[1.02rem] font-medium tracking-[-0.015em] text-ink/90 group-hover:text-ink">
        {item.title}
      </span>
    </>
  );

  let link: ReactNode;
  if (target.download) {
    link = (
      <a className={linkClass} href={target.href} download>
        {label}
      </a>
    );
  } else if (target.external) {
    link = (
      <a className={linkClass} href={target.href} target="_blank" rel="noreferrer">
        {label}
      </a>
    );
  } else {
    link = (
      <Link className={linkClass} href={target.href}>
        {label}
      </Link>
    );
  }

  return (
    <div className={wrapClass}>
      {link}
      <ItemTip item={item} />
    </div>
  );
}

export function Portfolio() {
  const groups = portfolioData.groups;

  return (
    <section id="portfolio" className="border-t border-white/10">
      <div className="wrap py-24 md:py-32">
        <Reveal>
          <p className="eyebrow">{portfolio.title}</p>
          <h2 className="display mt-4 max-w-3xl text-[clamp(2.1rem,5vw,3.6rem)]">
            {portfolio.headline}
          </h2>
          <p className="mt-6 max-w-2xl text-[1.15rem] leading-relaxed text-ink/75">
            {portfolio.lead}
          </p>
        </Reveal>

        {groups.length === 0 ? (
          <Reveal delay={80}>
            <div className="mt-14 rounded-[28px] border border-dashed border-white/15 bg-panel/60 px-7 py-12 text-center md:px-10">
              <p className="text-[1.05rem] text-ink/80">Первые материалы скоро появятся здесь.</p>
              <p className="mt-3 text-sm text-ink-dim">
                Схемы, презентации и документы с просмотром и скачиванием.
              </p>
            </div>
          </Reveal>
        ) : (
          <div className="portfolio-groups mt-14 grid gap-4 md:grid-cols-3 md:gap-5">
            {groups.map((group, gi) => {
              const tipSide: "left" | "right" = gi === 0 ? "right" : "left";
              return (
                <Reveal key={group.id} delay={gi * 70} className="portfolio-group-reveal">
                  <div className="portfolio-group flex h-full flex-col rounded-[24px] bg-panel px-5 py-6 md:px-6 md:py-7">
                    <h3 className="display text-[1.15rem] leading-snug text-ink/90 md:text-[1.25rem]">
                      {group.title}
                    </h3>
                    <ul className="mt-4 flex flex-col gap-0.5">
                      {group.items.map((item) => (
                        <li key={item.id} className="portfolio-item-li">
                          <ItemRow item={item} tipSide={tipSide} />
                        </li>
                      ))}
                    </ul>
                  </div>
                </Reveal>
              );
            })}
          </div>
        )}
      </div>
    </section>
  );
}
