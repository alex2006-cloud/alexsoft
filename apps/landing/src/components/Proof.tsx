import { site } from "@/content/site";
import { Reveal } from "@/components/Reveal";

export function Proof() {
  return (
    <section className="border-t border-white/10 pb-6 pt-2">
      <div className="wrap">
        <Reveal>
          <dl className="grid grid-cols-2 gap-px overflow-hidden rounded-[28px] bg-line md:grid-cols-4">
            {site.stats.map((stat) => (
              <div key={stat.label} className="bg-canvas px-6 py-10 md:px-8 md:py-12">
                <dt className="sr-only">{stat.label}</dt>
                <dd className="display text-[clamp(1.8rem,4vw,2.6rem)] text-ink">{stat.value}</dd>
                <p className="mt-3 max-w-[12rem] text-sm leading-snug text-ink-dim">{stat.label}</p>
              </div>
            ))}
          </dl>
        </Reveal>
        <Reveal className="py-16 md:py-20" delay={80}>
          <p className="eyebrow text-center">Масштаб заказчиков</p>
          <p className="mx-auto mt-6 max-w-4xl text-center text-[clamp(1.2rem,2.6vw,1.85rem)] font-medium leading-snug tracking-[-0.03em] text-ink/90">
            {site.clients.join("  ·  ")}
          </p>
        </Reveal>
      </div>
    </section>
  );
}
