# Портфолио (исходники)

Схемы и документы для витрины на лендинге. **Не путать** с `artifacts/structurizr/` — там architecture-as-code платформы alexsoft.

## Куда что класть

| Место | Содержимое |
|-------|------------|
| `artifacts/portfolio/<кейс>/` | Исходники: `.drawio`, рабочие PDF, черновики |
| `artifacts/portfolio/<кейс>/exports/` | Экспорт для веба (PNG/SVG/PDF) |
| `apps/landing/public/portfolio/` | Файлы, которые реально отдаёт сайт |
| `apps/landing/src/content/site.ts` → `portfolio.items` | Карточки на лендинге |

## Именование

```
alfa-llm-context.pdf
vtb-accelerator-c4.svg
```

Латиница, kebab-case, без пробелов.

## Карточка в `site.ts`

```ts
{
  id: "alfa-llm-context",
  title: "AI-контур: System Context",
  summary: "Кратко, что на схеме и зачем.",
  kind: "Схема",       // Схема | Презентация | Документ
  format: "PDF",       // PDF | PNG | SVG
  previewHref: "/portfolio/alfa-llm-context.pdf",
  downloadHref: "/portfolio/alfa-llm-context.pdf",
}
```

После добавления файлов в `public/portfolio/` и записи в `portfolio.items` — пересобрать лендинг и выложить.
