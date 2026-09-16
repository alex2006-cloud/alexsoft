import { Reveal } from "@/components/Reveal";
import { portfolio } from "@/content/site";

export function Portfolio() {
  const items = portfolio.items;

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

        {items.length === 0 ? (
          <Reveal delay={80}>
            <div className="mt-14 rounded-[28px] border border-dashed border-white/15 bg-panel/60 px-7 py-12 text-center md:px-10">
              <p className="text-[1.05rem] text-ink/80">
                Первые материалы скоро появятся здесь.
              </p>
              <p className="mt-3 text-sm text-ink-dim">
                Схемы, презентации и документы — с просмотром и скачиванием.
              </p>
            </div>
          </Reveal>
        ) : (
          <ul className="mt-14 grid gap-4 md:grid-cols-2">
            {items.map((item, index) => (
              <Reveal key={item.id} delay={index * 60}>
                <li className="flex h-full flex-col rounded-[28px] bg-panel px-7 py-8 md:px-8 md:py-9">
                  <div className="flex flex-wrap items-center gap-2 text-[11px] font-medium uppercase tracking-[0.12em] text-ink-dim">
                    <span>{item.kind}</span>
                    <span aria-hidden="true">·</span>
                    <span>{item.format}</span>
                  </div>
                  <h3 className="display mt-4 text-[1.55rem] md:text-[1.75rem]">
                    <span className="mr-2" aria-hidden="true">
                      {item.emoji}
                    </span>
                    {item.title}
                  </h3>
                  <p className="mt-3 flex-1 text-[1.02rem] leading-relaxed text-ink/75">
                    {item.summary}
                  </p>
                  <div className="mt-8 flex flex-wrap gap-3">
                    {item.previewHref ? (
                      <a
                        className="btn btn-primary min-h-10 px-5 text-[0.95rem]"
                        href={item.previewHref}
                        target="_blank"
                        rel="noreferrer"
                      >
                        Смотреть
                      </a>
                    ) : null}
                    <a
                      className={`btn min-h-10 px-5 text-[0.95rem] ${
                        item.previewHref ? "btn-ghost px-4" : "btn-primary"
                      }`}
                      href={item.downloadHref}
                      download
                    >
                      Скачать →
                    </a>
                  </div>
                </li>
              </Reveal>
            ))}
          </ul>
        )}
      </div>
    </section>
  );
}
