import data from "./portfolio.generated.json";

/**
 * Данные витрины портфолио. Файл portfolio.generated.json создаёт
 * scripts/collect-portfolio.mjs из artifacts/portfolio/portfolio.yaml
 * (запускается автоматически перед dev и build). Руками не править.
 */

export type PortfolioView = "pdf" | "html" | "text" | "image" | "gallery" | "download";

export type PortfolioDownload = {
  label: string;
  href: string;
  size: number;
};

export type PortfolioItem = {
  id: string;
  group: string;
  title: string;
  emoji: string;
  kind: string;
  summary: string;
  view: PortfolioView;
  format: string;
  /** Главный файл (pdf, html, md, картинка, xlsx). Для gallery не задан. */
  href?: string;
  size?: number;
  /** Страница просмотра на сайте (text, image, gallery). */
  pageHref?: string;
  /** Миниатюра для карточки. */
  cover?: string;
  /** HTML превью: из .md (view=text) или извлечённый текст PDF (view=pdf). */
  html?: string;
  images?: { label: string; src: string }[];
  downloads: PortfolioDownload[];
};

export type PortfolioGroup = {
  id: string;
  title: string;
  items: PortfolioItem[];
};

export const portfolioData = data as { groups: PortfolioGroup[]; items: PortfolioItem[] };

export function getPortfolioItem(id: string): PortfolioItem | undefined {
  return portfolioData.items.find((item) => item.id === id);
}

export function formatSize(bytes: number): string {
  if (bytes >= 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} МБ`;
  return `${Math.max(1, Math.round(bytes / 1024))} КБ`;
}
