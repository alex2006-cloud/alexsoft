import { site } from "@/content/site";

export function Hero() {
  return (
    <section
      id="top"
      className="relative isolate flex min-h-[100svh] items-center overflow-hidden pt-12"
    >
      <div className="hero-orb hero-orb-a" />
      <div className="hero-orb hero-orb-b" />
      <div className="grain" />
      <div className="wrap relative z-10 py-24 md:py-32">
        <div className="hero-copy mx-auto max-w-4xl text-center">
          <p className="eyebrow">{site.role} · {site.location}</p>
          <h1 className="display mt-6 text-[clamp(3.4rem,11vw,6.75rem)]">
            {site.name}
          </h1>
          <p className="mx-auto mt-7 max-w-3xl text-[clamp(1.35rem,3.2vw,2.35rem)] font-medium leading-[1.15] tracking-[-0.03em] text-ink">
            {site.tagline}
          </p>
          <p className="mx-auto mt-7 max-w-2xl lede">{site.summary}</p>
          <div className="mt-10 flex flex-wrap items-center justify-center gap-2">
            <a className="btn btn-primary" href="/#work">
              Смотреть работы
            </a>
            <a className="btn btn-ghost" href="/#contact">
              Связаться →
            </a>
          </div>
        </div>
      </div>
    </section>
  );
}
