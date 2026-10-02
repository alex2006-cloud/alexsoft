"use client";

import { useState } from "react";

type Img = { label: string; src: string };

/** Просмотр диаграммы: вкладки для нескольких картинок, увеличение и открытие в новой вкладке. */
export function ImageViewer({ images, title }: { images: Img[]; title: string }) {
  const [active, setActive] = useState(0);
  const [zoomed, setZoomed] = useState(false);
  const current = images[active] ?? images[0];
  if (!current) return null;

  return (
    <div>
      {images.length > 1 ? (
        <div
          role="tablist"
          aria-label={`${title}: диаграммы`}
          className="-mx-1 mb-4 flex gap-2 overflow-x-auto px-1 pb-2"
        >
          {images.map((img, i) => (
            <button
              key={img.src}
              type="button"
              role="tab"
              aria-selected={i === active}
              onClick={() => setActive(i)}
              className={`shrink-0 rounded-full px-4 py-2 text-sm font-medium transition-colors ${
                i === active ? "bg-white text-paper-ink" : "bg-panel text-ink/80 hover:text-ink"
              }`}
            >
              {img.label}
            </button>
          ))}
        </div>
      ) : null}

      <div className="mb-3 flex flex-wrap items-center gap-x-4 gap-y-1 text-sm">
        <button type="button" onClick={() => setZoomed((z) => !z)} className="link">
          {zoomed ? "Уместить в ширину" : "Увеличить"}
        </button>
        <a className="link" href={current.src} target="_blank" rel="noreferrer">
          Открыть в новой вкладке
        </a>
      </div>

      <div
        className={`overflow-auto rounded-[20px] bg-white ${zoomed ? "max-h-[80vh]" : ""}`}
        style={{ WebkitOverflowScrolling: "touch" }}
      >
        {/* eslint-disable-next-line @next/next/no-img-element */}
        <img
          src={current.src}
          alt={`${title}: ${current.label}`}
          className={zoomed ? "block h-auto max-w-none" : "block h-auto w-full"}
          style={zoomed ? { width: "220%" } : undefined}
        />
      </div>
    </div>
  );
}
