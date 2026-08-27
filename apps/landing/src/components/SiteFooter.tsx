import { site } from "@/content/site";

export function SiteFooter() {
  const year = new Date().getFullYear();

  return (
    <footer className="border-t border-white/10 bg-[#0b0b0c] text-[12px] text-ink-dim">
      <div className="wrap grid gap-10 py-12 md:grid-cols-4">
        <div className="md:col-span-2">
          <p className="text-sm font-medium text-ink">{site.name}</p>
          <p className="mt-2 max-w-sm leading-relaxed">
            {site.role}. Личный лендинг и витрина лаборатории alexsoft.
          </p>
        </div>
        <div>
          <p className="mb-3 font-medium text-ink/80">Разделы</p>
          <ul className="space-y-2">
            {site.nav.map((item) => (
              <li key={item.href}>
                <a className="hover:text-ink" href={item.href}>
                  {item.label}
                </a>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="mb-3 font-medium text-ink/80">Связь</p>
          <ul className="space-y-2">
            <li>
              <a className="hover:text-ink" href={`mailto:${site.contacts.email}`}>
                Почта
              </a>
            </li>
            <li>
              <a
                className="hover:text-ink"
                href={site.contacts.telegramHref}
                target="_blank"
                rel="noreferrer"
              >
                Telegram
              </a>
            </li>
            <li>
              <a
                className="hover:text-ink"
                href={site.contacts.githubHref}
                target="_blank"
                rel="noreferrer"
              >
                GitHub
              </a>
            </li>
          </ul>
        </div>
      </div>
      <div className="wrap flex flex-col gap-2 border-t border-white/10 py-6 sm:flex-row sm:items-center sm:justify-between">
        <p>
          © {year} {site.name}. alexsoft — Personal Ecosystem Lab.
        </p>
        <p>Москва</p>
      </div>
    </footer>
  );
}
