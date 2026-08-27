import { Reveal } from "@/components/Reveal";
import { expertise } from "@/content/site";

export function Expertise() {
  return (
    <section id="expertise" className="border-t border-white/10">
      <div className="wrap py-24 md:py-32">
        <Reveal>
          <p className="eyebrow">Экспертиза</p>
          <h2 className="display mt-4 max-w-3xl text-[clamp(2.1rem,5vw,3.6rem)]">
            Четыре контура, из которых собирается решение.
          </h2>
        </Reveal>
        <div className="mt-14 grid gap-4 md:grid-cols-2">
          {expertise.map((pillar, index) => (
            <Reveal key={pillar.title} delay={index * 70}>
              <article className="h-full rounded-[28px] bg-panel px-7 py-8 md:px-8 md:py-10">
                <h3 className="display text-[1.7rem] md:text-[1.9rem]">{pillar.title}</h3>
                <ul className="mt-6 space-y-2.5 text-[1.02rem] leading-snug text-ink/75">
                  {pillar.items.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
