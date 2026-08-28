import { Reveal } from "@/components/Reveal";
import { career, credentials } from "@/content/site";

export function Career() {
  return (
    <section className="border-t border-white/10">
      <div className="wrap py-24 md:py-32">
        <div className="grid items-start gap-16 md:grid-cols-[1.15fr_0.85fr] md:gap-20">
          <Reveal>
            <p className="eyebrow">Путь</p>
            <h2 className="display mt-4 text-[clamp(2rem,4vw,3rem)]">
              11 лет: от инженерии к архитектуре ИИ
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
            <div id="education" className="scroll-mt-16">
              <p className="eyebrow">Основа</p>
              <h2 className="display mt-4 text-[clamp(2rem,4vw,3rem)]">
                Образование и подтверждения
              </h2>
              <p className="mt-5 text-[1.05rem] leading-relaxed text-ink/80">
                {credentials.education}
              </p>
              <p className="mt-2 text-[1.05rem] text-ink/80">{credentials.languages}</p>
              <div className="mt-5 rounded-2xl bg-[linear-gradient(180deg,rgba(41,151,255,0.14),rgba(41,151,255,0.05))] px-4 py-3 ring-1 ring-[#2997ff]/35">
                <p className="text-[11px] font-medium uppercase tracking-[0.12em] text-link">
                  Международные сертификаты
                </p>
                <ul className="mt-2 divide-y divide-white/10">
                  {credentials.certificates.map((item) => (
                    <li key={item.title} className="py-2 first:pt-0 last:pb-0">
                      <p className="text-sm font-medium tracking-tight text-ink">{item.title}</p>
                      <p className="text-[13px] text-ink-dim">
                        {item.issuer} · {item.year}
                      </p>
                    </li>
                  ))}
                </ul>
              </div>
              <ul className="mt-4 space-y-2 text-sm leading-snug text-ink-dim">
                {credentials.awards.map((item) => (
                  <li key={item} className="border-t border-white/10 pt-2.5">
                    {item}
                  </li>
                ))}
              </ul>
              <p className="mt-5 text-[11px] font-medium uppercase tracking-[0.12em] text-ink-dim">
                Повышение квалификации
              </p>
              <ul className="mt-2 space-y-0">
                {credentials.courses.map((item) => (
                  <li key={`${item.title}-${item.year}`} className="border-t border-white/10 py-2.5">
                    <p className="text-sm text-ink/85">{item.title}</p>
                    <p className="text-[13px] text-ink-dim">
                      {item.issuer} · {item.year}
                    </p>
                  </li>
                ))}
              </ul>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
}
