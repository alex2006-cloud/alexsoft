import { site } from "@/content/site";

const highlights = [
  "C4 · ADR · AI / Data",
  "LLM · RAG · MLOps",
  "PostgreSQL · Kafka · K8s",
];

export function VisitingCard() {
  const { email, phone, phoneHref, telegram, telegramHref, siteLabel, siteHref, githubHref } =
    site.contacts;

  return (
    <div className="visiting-card-scene">
      <article className="visiting-card" aria-label="Цифровая визитка">
        <div className="visiting-card-glow" aria-hidden />

        <div className="visiting-card-inner">
          <header className="visiting-card-head">
            <img
              src="/portrait.jpg"
              alt=""
              width={88}
              height={88}
              className="visiting-card-photo"
            />
            <div>
              <p className="visiting-card-brand">alexsoft · Personal Ecosystem Lab</p>
              <h1 className="visiting-card-name">{site.name}</h1>
              <p className="visiting-card-role">{site.role}</p>
              <p className="visiting-card-location">{site.location}</p>
            </div>
          </header>

          <p className="visiting-card-tagline">{site.tagline}</p>

          <ul className="visiting-card-tags" aria-label="Фокус">
            {highlights.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>

          <div className="visiting-card-stats">
            {site.stats.slice(0, 3).map((stat) => (
              <div key={stat.label}>
                <span className="visiting-card-stat-value">{stat.value}</span>
                <span className="visiting-card-stat-label">{stat.label}</span>
              </div>
            ))}
          </div>

          <div className="visiting-card-divider" aria-hidden />

          <nav className="visiting-card-contacts" aria-label="Контакты">
            <a className="visiting-card-contact visiting-card-contact-primary" href={telegramHref}>
              <span className="visiting-card-contact-label">Telegram</span>
              <span className="visiting-card-contact-value">{telegram}</span>
            </a>
            <a className="visiting-card-contact" href={`mailto:${email}`}>
              <span className="visiting-card-contact-label">Email</span>
              <span className="visiting-card-contact-value">{email}</span>
            </a>
            <a className="visiting-card-contact" href={phoneHref}>
              <span className="visiting-card-contact-label">Телефон</span>
              <span className="visiting-card-contact-value">{phone}</span>
            </a>
            <a className="visiting-card-contact" href={siteHref}>
              <span className="visiting-card-contact-label">Сайт</span>
              <span className="visiting-card-contact-value">{siteLabel}</span>
            </a>
            <a className="visiting-card-contact" href={githubHref} target="_blank" rel="noreferrer">
              <span className="visiting-card-contact-label">GitHub</span>
              <span className="visiting-card-contact-value">alexsoft</span>
            </a>
          </nav>
        </div>
      </article>

      <p className="visiting-card-hint">
        Сохраните страницу в закладки или отправьте ссылку{" "}
        <a className="link" href={siteHref}>
          {siteLabel}/card
        </a>
      </p>
    </div>
  );
}
