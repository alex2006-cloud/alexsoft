import { Reveal } from "@/components/Reveal";
import { career, credentials } from "@/content/site";

export function Career() {
  return (
    <section className="border-t border-white/10">
      <div className="wrap grid gap-16 py-24 md:grid-cols-[1.15fr_0.85fr] md:gap-20 md:py-32">
        <Reveal>
          <p className="eyebrow">Путь</p>
          <h2 className="display mt-4 text-[clamp(2rem,4vw,3rem)]">
            11 лет: от инженерии к архитектуре ИИ.
          </h2>
          <ol className="mt-10">
            {career.map((item) => (
              <li
                key={`${item.company}-${item.period}`}
                className="grid grid-cols-[7.5rem_1fr] gap-4 border-t border-white/10 py-5 md:grid-cols-[8.5rem_1fr]"
              >
                <p className="text-sm text-ink-dim">{item.period}</p>
                <div>
                  <p className="font-medium tracking-tight">{item.company}</p>
                  <p className="mt-1 text-sm leading-snug text-ink-dim">{item.role}</p>
                </div>
              </li>
            ))}
          </ol>
        </Reveal>
        <Reveal delay={90}>
          <p className="eyebrow">Основа</p>
          <h2 className="display mt-4 text-[clamp(2rem,4vw,3rem)]">Образование и подтверждения.</h2>
          <p className="mt-8 text-[1.05rem] leading-relaxed text-ink/80">{credentials.education}</p>
          <p className="mt-4 text-[1.05rem] text-ink/80">{credentials.languages}</p>
          <ul className="mt-8 space-y-3 text-sm leading-relaxed text-ink-dim">
            {credentials.highlights.map((item) => (
              <li key={item} className="border-t border-white/10 pt-3">
                {item}
              </li>
            ))}
          </ul>
        </Reveal>
      </div>
    </section>
  );
}
