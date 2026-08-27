import { Reveal } from "@/components/Reveal";
import { work } from "@/content/site";

export function Work() {
  return (
    <section id="work" className="bg-paper pb-8 text-paper-ink">
      <div className="wrap pb-8 pt-4">
        <Reveal>
          <p className="eyebrow text-paper-dim">Избранные работы</p>
          <h2 className="display mt-4 max-w-3xl text-[clamp(2.1rem,5vw,3.6rem)]">
            Не список мест. Решения, которые выдержали масштаб.
          </h2>
        </Reveal>
      </div>
      <div className="wrap flex flex-col gap-4 pb-16 md:gap-5 md:pb-24">
        {work.map((item, index) => (
          <Reveal key={item.id} delay={index * 40}>
            <article
              className={`overflow-hidden rounded-[28px] px-6 py-10 md:px-12 md:py-14 ${
                item.tone === "dark"
                  ? "bg-canvas text-ink"
                  : "bg-white text-paper-ink shadow-[0_2px_24px_rgba(0,0,0,0.04)]"
              }`}
            >
              <p
                className={`eyebrow ${item.tone === "dark" ? "text-ink-dim" : "text-paper-dim"}`}
              >
                {item.kicker}
              </p>
              <div className="mt-5 grid gap-10 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,0.8fr)] lg:items-end">
                <div>
                  <h3 className="display text-[clamp(1.9rem,4vw,3.1rem)]">{item.title}</h3>
                  <p
                    className={`mt-3 text-sm font-medium ${item.tone === "dark" ? "text-ink-dim" : "text-paper-dim"}`}
                  >
                    {item.role}
                  </p>
                  <p
                    className={`mt-5 max-w-2xl text-[1.125rem] leading-relaxed ${
                      item.tone === "dark" ? "text-ink/80" : "text-paper-ink/80"
                    }`}
                  >
                    {item.lead}
                  </p>
                </div>
                <dl className="grid grid-cols-2 gap-x-6 gap-y-6">
                  {item.metrics.map((metric) => (
                    <div key={metric.label}>
                      <dt
                        className={`text-xs leading-snug ${item.tone === "dark" ? "text-ink-dim" : "text-paper-dim"}`}
                      >
                        {metric.label}
                      </dt>
                      <dd className="display mt-1 text-[1.35rem] tracking-[-0.03em] md:text-[1.55rem]">
                        {metric.value}
                      </dd>
                    </div>
                  ))}
                </dl>
              </div>
              <ul
                className={`mt-10 grid gap-3 text-[0.98rem] leading-snug md:grid-cols-3 ${
                  item.tone === "dark" ? "text-ink/75" : "text-paper-ink/75"
                }`}
              >
                {item.points.map((point) => (
                  <li key={point} className="border-t border-current/15 pt-3">
                    {point}
                  </li>
                ))}
              </ul>
              <p
                className={`mt-8 text-xs tracking-[0.01em] ${item.tone === "dark" ? "text-ink-dim" : "text-paper-dim"}`}
              >
                {item.stack}
              </p>
            </article>
          </Reveal>
        ))}
      </div>
    </section>
  );
}
