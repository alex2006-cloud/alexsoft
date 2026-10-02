// Собирает витрину портфолио из artifacts/portfolio/portfolio.yaml.
//
// Источник правды: artifacts/portfolio/ (файлы + portfolio.yaml).
// Результат (в .gitignore, пересобирается при каждом dev/build):
//   public/portfolio/files/<id>/...        файлы для просмотра и скачивания
//   src/content/portfolio.generated.json   данные карточек для лендинга
//
// Запуск: node scripts/collect-portfolio.mjs (автоматически как predev / prebuild).

import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from "node:fs";
import { basename, extname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { Marked } from "marked";
import { parse } from "yaml";

const landingRoot = resolve(fileURLToPath(new URL(".", import.meta.url)), "..");
const repoRoot = resolve(landingRoot, "..", "..");
const sourceDir = join(repoRoot, "artifacts", "portfolio");
const indexFile = join(sourceDir, "portfolio.yaml");
const filesOut = join(landingRoot, "public", "portfolio", "files");
const jsonOut = join(landingRoot, "src", "content", "portfolio.generated.json");

const VIEWS = ["pdf", "html", "text", "image", "gallery", "download"];
const ID_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;

const errors = [];
const fail = (message) => errors.push(message);

function readIndex() {
  if (!existsSync(indexFile)) {
    console.error(`[portfolio] Нет индекса: ${indexFile}`);
    process.exit(1);
  }
  return parse(readFileSync(indexFile, "utf8")) ?? {};
}

function resolveSource(rel, where) {
  if (typeof rel !== "string" || rel.length === 0) {
    fail(`${where}: не указан путь к файлу`);
    return null;
  }
  const abs = resolve(sourceDir, rel);
  if (!abs.startsWith(sourceDir)) {
    fail(`${where}: путь выходит за пределы artifacts/portfolio: ${rel}`);
    return null;
  }
  if (!existsSync(abs) || !statSync(abs).isFile()) {
    fail(`${where}: файл не найден: artifacts/portfolio/${rel}`);
    return null;
  }
  return abs;
}

const marked = new Marked({
  gfm: true,
  renderer: {
    // Относительные ссылки на файлы репозитория на сайте не работают: оставляем только текст.
    link({ href, title, tokens }) {
      const text = this.parser.parseInline(tokens);
      if (!/^(https?:|mailto:|#)/i.test(href)) return text;
      const t = title ? ` title="${title}"` : "";
      return `<a href="${href}"${t} target="_blank" rel="noreferrer">${text}</a>`;
    },
  },
});

const copied = new Map(); // abs -> url, чтобы не копировать дважды в рамках одной карточки
function publish(itemId, abs) {
  const key = `${itemId}|${abs}`;
  if (copied.has(key)) return copied.get(key);
  const dir = join(filesOut, itemId);
  mkdirSync(dir, { recursive: true });
  const name = basename(abs);
  copyFileSync(abs, join(dir, name));
  const url = `/portfolio/files/${itemId}/${encodeURIComponent(name)}`;
  copied.set(key, url);
  return url;
}

const formatOf = (abs) => extname(abs).replace(".", "").toUpperCase();

const PREVIEW_CHARS = 3500;

function escapeHtml(s) {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/** Плоский текст → простой HTML для мини-превью в тултипе. */
function textToPreviewHtml(text) {
  const clipped = text.replace(/[ \t]+\n/g, "\n").replace(/\n{3,}/g, "\n\n").trim().slice(0, PREVIEW_CHARS);
  if (!clipped) return "";
  return clipped
    .split(/\n{2,}/)
    .map((block) => `<p>${escapeHtml(block).replace(/\n/g, "<br>")}</p>`)
    .join("\n");
}

async function extractPdfPreviewHtml(abs, where) {
  try {
    const { extractText, getDocumentProxy } = await import("unpdf");
    const pdf = await getDocumentProxy(new Uint8Array(readFileSync(abs)));
    const maxPages = Math.min(3, pdf.numPages || 3);
    const { text } = await extractText(pdf, { mergePages: true });
    const limited =
      typeof text === "string"
        ? text
        : Array.isArray(text)
          ? text.slice(0, maxPages).join("\n\n")
          : "";
    const html = textToPreviewHtml(limited);
    if (!html) {
      console.warn(`[portfolio] ${where}: в PDF нет извлекаемого текста — превью-заглушка`);
    }
    return html;
  } catch (err) {
    console.warn(`[portfolio] ${where}: не удалось прочитать PDF (${err?.message ?? err})`);
    return "";
  }
}

async function build() {
  const index = readIndex();
  const groups = Array.isArray(index.groups) ? index.groups : [];
  const rawItems = Array.isArray(index.items) ? index.items : [];

  const groupIds = new Set();
  for (const g of groups) {
    if (!g?.id || !g?.title) fail(`groups: у группы нужны id и title (${JSON.stringify(g)})`);
    else if (groupIds.has(g.id)) fail(`groups: дублирующийся id группы "${g.id}"`);
    else groupIds.add(g.id);
  }

  rmSync(filesOut, { recursive: true, force: true });

  const ids = new Set();
  const items = [];

  for (const raw of rawItems) {
    const where = `items[${raw?.id ?? "?"}]`;
    if (!raw?.id || !ID_RE.test(raw.id) || raw.id === "files") {
      fail(`${where}: id обязателен, в kebab-case и не равен "files"`);
      continue;
    }
    if (ids.has(raw.id)) {
      fail(`${where}: дублирующийся id`);
      continue;
    }
    ids.add(raw.id);

    for (const field of ["group", "title", "emoji", "kind", "summary", "view"]) {
      if (!raw[field]) fail(`${where}: не заполнено поле "${field}"`);
    }
    if (raw.group && !groupIds.has(raw.group)) fail(`${where}: неизвестная группа "${raw.group}"`);
    if (raw.view && !VIEWS.includes(raw.view)) {
      fail(`${where}: view должен быть одним из ${VIEWS.join(", ")}`);
      continue;
    }

    const item = {
      id: raw.id,
      group: raw.group,
      title: raw.title,
      emoji: raw.emoji,
      kind: raw.kind,
      summary: raw.summary,
      view: raw.view,
      downloads: [],
    };

    if (raw.view === "gallery") {
      const images = Array.isArray(raw.images) ? raw.images : [];
      if (images.length === 0) fail(`${where}: для gallery нужен список images`);
      item.images = [];
      for (const img of images) {
        const abs = resolveSource(img?.file, `${where}.images`);
        if (!abs) continue;
        item.images.push({ label: img.label ?? basename(abs), src: publish(raw.id, abs) });
      }
      item.format = item.images.length ? formatOf(resolve(sourceDir, images[0].file)) : "";
      item.cover = item.images[0]?.src;
      item.pageHref = `/portfolio/${raw.id}`;
    } else {
      const abs = resolveSource(raw.file, where);
      if (!abs) continue;
      const url = publish(raw.id, abs);
      item.format = formatOf(abs);
      item.size = statSync(abs).size;
      item.href = url;

      if (raw.view === "text") {
        if (extname(abs).toLowerCase() !== ".md") fail(`${where}: для text нужен файл .md`);
        item.html = marked.parse(readFileSync(abs, "utf8"));
        item.pageHref = `/portfolio/${raw.id}`;
      } else if (raw.view === "image") {
        item.cover = url;
        item.pageHref = `/portfolio/${raw.id}`;
      } else if (raw.view === "pdf") {
        if (extname(abs).toLowerCase() !== ".pdf") fail(`${where}: для pdf нужен файл .pdf`);
        const preview = await extractPdfPreviewHtml(abs, where);
        if (preview) item.html = preview;
      }
    }

    const dl =
      Array.isArray(raw.downloads) && raw.downloads.length > 0
        ? raw.downloads
        : [{ label: item.format || "Скачать", file: raw.file ?? raw.images?.[0]?.file }];
    for (const d of dl) {
      const abs = resolveSource(d?.file, `${where}.downloads`);
      if (!abs) continue;
      item.downloads.push({ label: d.label ?? formatOf(abs), href: publish(raw.id, abs), size: statSync(abs).size });
    }

    items.push(item);
  }

  if (errors.length > 0) {
    console.error("[portfolio] Ошибки в artifacts/portfolio/portfolio.yaml:");
    for (const e of errors) console.error(`  - ${e}`);
    process.exit(1);
  }

  const out = {
    groups: groups
      .map((g) => ({ id: g.id, title: g.title, items: items.filter((i) => i.group === g.id) }))
      .filter((g) => g.items.length > 0),
    items,
  };
  mkdirSync(resolve(jsonOut, ".."), { recursive: true });
  writeFileSync(jsonOut, JSON.stringify(out, null, 2) + "\n", "utf8");
  console.log(`[portfolio] ${items.length} карточек, ${out.groups.length} групп -> ${jsonOut.replace(repoRoot, ".")}`);
}

await build();
