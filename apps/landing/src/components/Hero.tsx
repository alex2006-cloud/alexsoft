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
      <div className="wrap relative z-10 py-16 md:py-24">
        <div className="grid items-center gap-10 lg:grid-cols-[minmax(0,1.05fr)_minmax(0,0.9fr)] lg:gap-16">
          <div className="hero-copy text-center lg:text-left">
            <img
              src="/portrait.jpg"
              alt={site.name}
              width={160}
              height={160}
              className="mx-auto mb-7 size-36 rounded-full object-cover object-[54%_12%] ring-1 ring-white/15 lg:hidden"
            />
            <p className="eyebrow">
              {site.role} · {site.location}
            </p>
            <h1 className="display mt-5 text-[clamp(2.7rem,8vw,5.4rem)]">
              {site.name}
            </h1>
            <p className="mx-auto mt-6 max-w-xl text-[clamp(1.2rem,2.4vw,1.85rem)] font-medium leading-[1.18] tracking-[-0.03em] text-ink lg:mx-0">
              {site.tagline}
            </p>
            <p className="mx-auto mt-6 max-w-xl lede lg:mx-0">{site.summary}</p>
            <div className="mt-9 flex flex-wrap items-center justify-center gap-2 lg:justify-start">
              <a className="btn btn-primary" href="/#work">
                Смотреть работы
              </a>
              <a className="btn btn-ghost" href="/#contact">
                Связаться →
              </a>
            </div>
          </div>
          <div className="hidden lg:block">
            <div className="relative mx-auto aspect-[4/5] max-h-[min(72vh,640px)] w-full max-w-[520px] overflow-hidden rounded-[32px] bg-panel ring-1 ring-white/10">
              <img
                src="/portrait.jpg"
                alt={`${site.name} — выступление`}
                className="absolute inset-0 h-full w-full object-cover object-[58%_14%] scale-[1.08]"
              />
              <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-black/35 via-transparent to-black/10" />
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
