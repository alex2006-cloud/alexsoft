export type GameEntry = {
  slug: string;
  name: string;
  subtitle: string;
  blurb: string;
  status: "Live" | "Скоро";
  /** Path inside the games app (basePath /games is added by Next Link). */
  href: string;
  gradient?: string;
};

export const gamesCatalog = {
  title: "Игры",
  lead: "Мини-продукты лаборатории alexsoft. Открывайте, играйте, смотрите, как идея становится интерактивным контуром.",
} as const;

export const games: GameEntry[] = [
  {
    slug: "vibe-check",
    name: "Вайб-чек",
    subtitle: "Gen Z · реакция",
    blurb:
      "30 секунд, полоска вайба и зелёная зона. Поймал — W и slay. Промах — L и skill issue.",
    status: "Live",
    href: "/vibe-check",
    gradient: "from-[#ff6ec7] via-[#7c3aed] to-[#0f172a]",
  },
  {
    slug: "contour",
    name: "Контур",
    subtitle: "C4 Puzzle",
    blurb:
      "Соберите системный контекст Personal Ecosystem Lab: кто к кому ходит и зачем — как на диаграмме C4.",
    status: "Live",
    href: "/contour",
  },
  {
    slug: "desant",
    name: "Десант",
    subtitle: "Run & Gun · Dendy",
    blurb:
      "Беги, прыгай, стреляй — боковой экшен в духе Contra. Со своим чиптюном в браузере.",
    status: "Live",
    href: "/desant",
  },
];
