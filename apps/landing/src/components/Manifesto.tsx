import { site } from "@/content/site";
import { Reveal } from "@/components/Reveal";

export function Manifesto() {
  return (
    <section className="bg-paper text-paper-ink">
      <div className="wrap py-24 md:py-32">
        <Reveal>
          <p className="eyebrow text-paper-dim">Как я работаю</p>
          <h2 className="display mt-4 max-w-3xl text-[clamp(2.1rem,5vw,3.6rem)]">
            Сначала ясность. Потом контур. Затем эффект.
          </h2>
        </Reveal>
        <div className="mt-16 grid gap-10 md:grid-cols-3 md:gap-8">
          {site.manifesto.map((item, index) => (
            <Reveal key={item.title} delay={index * 90}>
              <p className="text-sm font-medium text-paper-dim">{item.title}</p>
              <p className="mt-3 text-[1.2rem] leading-snug tracking-[-0.02em]">{item.text}</p>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
