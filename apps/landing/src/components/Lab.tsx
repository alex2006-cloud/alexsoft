import { Reveal } from "@/components/Reveal";
import { lab } from "@/content/site";

const visuals = [
  "from-[#1e3a8a] via-[#0f172a] to-black",
  "from-[#4c1d95] via-[#1e1b4b] to-black",
  "from-[#0f766e] via-[#042f2e] to-black",
];

export function Lab() {
  return (
    <section id="lab" className="bg-paper text-paper-ink">
      <div className="wrap py-24 md:py-32">
        <Reveal>
          <p className="eyebrow text-paper-dim">{lab.title}</p>
          <h2 className="display mt-4 text-[clamp(2.1rem,5vw,3.6rem)]">
            {lab.name}
            <span className="block text-[0.55em] font-medium tracking-[-0.03em] text-paper-dim">
              {lab.subtitle}
            </span>
          </h2>
          <p className="mt-6 max-w-2xl text-[1.2rem] leading-relaxed text-paper-ink/75">
            {lab.lead}
          </p>
        </Reveal>
        <div className="mt-14 grid gap-5 md:grid-cols-3">
          {lab.products.map((product, index) => (
            <Reveal key={product.name} delay={index * 80}>
              <article className="overflow-hidden rounded-[28px] bg-white shadow-[0_2px_24px_rgba(0,0,0,0.04)]">
                <div
                  className={`tile-visual aspect-[16/10] bg-gradient-to-br ${visuals[index]}`}
                />
                <div className="px-6 py-6">
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="display text-[1.55rem]">{product.name}</h3>
                    <span className="rounded-full bg-paper px-3 py-1 text-xs font-medium text-paper-dim">
                      {product.status}
                    </span>
                  </div>
                  <p className="mt-3 text-[0.98rem] leading-relaxed text-paper-ink/70">
                    {product.blurb}
                  </p>
                </div>
              </article>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
}
