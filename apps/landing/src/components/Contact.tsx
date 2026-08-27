import { site } from "@/content/site";
import { Reveal } from "@/components/Reveal";

export function Contact() {
  const { email, phone, phoneHref, telegram, telegramHref, siteLabel, siteHref } =
    site.contacts;

  return (
    <section id="contact" className="bg-paper text-paper-ink">
      <div className="wrap py-24 md:py-32">
        <Reveal>
          <p className="eyebrow text-paper-dim">Контакты</p>
          <h2 className="display mt-4 max-w-3xl text-[clamp(2.2rem,6vw,4.2rem)]">
            Давайте соберём контур, который выдержит нагрузку.
          </h2>
          <p className="mt-5 max-w-xl text-[1.15rem] leading-relaxed text-paper-ink/70">
            Москва. Гибрид, удалённо или на площадке. Командировки — да. Пишите в
            Telegram или на почту: это самый быстрый путь.
          </p>
        </Reveal>
        <Reveal className="mt-14 space-y-5" delay={80}>
          <a
            className="display block text-[clamp(1.5rem,4vw,2.6rem)] text-blue transition-opacity hover:opacity-80"
            href={`mailto:${email}`}
          >
            {email}
          </a>
          <div className="flex flex-col gap-3 text-lg text-paper-ink/80 sm:flex-row sm:flex-wrap sm:gap-x-8">
            <a className="link" href={telegramHref} target="_blank" rel="noreferrer">
              Telegram {telegram}
            </a>
            <a className="link" href={phoneHref}>
              {phone}
            </a>
            <a className="link" href={siteHref} target="_blank" rel="noreferrer">
              {siteLabel}
            </a>
          </div>
        </Reveal>
      </div>
    </section>
  );
}
