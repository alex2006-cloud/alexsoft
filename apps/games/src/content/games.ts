export type GameEntry = {
  slug: string;
  name: string;
  subtitle: string;
  blurb: string;
  status: "Live" | "Скоро";
  /** Path inside the games app (basePath /games is added by Next Link / Image). */
  href: string;
  /** Cover under public/covers/ */
  cover: string;
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
    cover: "/covers/vibe-check.png",
  },
  {
    slug: "contour",
    name: "Контур",
    subtitle: "C4 Puzzle",
    blurb:
      "Соберите системный контекст Personal Ecosystem Lab: кто к кому ходит и зачем — как на диаграмме C4.",
    status: "Live",
    href: "/contour",
    cover: "/covers/contour.png",
  },
  {
    slug: "desant",
    name: "Десант",
    subtitle: "Run & Gun · Dendy",
    blurb:
      "Беги, прыгай, стреляй — боковой экшен в духе Contra. Со своим чиптюном в браузере.",
    status: "Live",
    href: "/desant",
    cover: "/covers/desant.png",
  },
];
