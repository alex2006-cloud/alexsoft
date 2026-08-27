"use client";

import { useEffect, useState } from "react";
import { site } from "@/content/site";

export function SiteNav() {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  useEffect(() => {
    document.body.style.overflow = open ? "hidden" : "";
    return () => {
      document.body.style.overflow = "";
    };
  }, [open]);

  return (
    <header
      className={`fixed inset-x-0 top-0 z-50 border-b transition-[background,border-color] duration-300 ${
        scrolled || open
          ? "nav-blur border-white/10"
          : "border-transparent bg-transparent"
      }`}
    >
      <nav className="wrap flex h-12 items-center justify-between text-[12px] tracking-tight text-ink/90">
        <a href="/" className="font-medium text-ink">
          {site.name}
        </a>
        <ul className="hidden items-center gap-7 md:flex">
          {site.nav.map((item) => (
            <li key={item.href}>
              <a className="text-ink/80 transition-colors hover:text-ink" href={item.href}>
                {item.label}
              </a>
            </li>
          ))}
          <li>
            <a
              className="rounded-full bg-blue px-3.5 py-1.5 text-[12px] font-medium text-white transition-colors hover:bg-blue-hover"
              href="/#contact"
            >
              Написать
            </a>
          </li>
        </ul>
        <button
          type="button"
          className="inline-flex h-8 w-8 items-center justify-center rounded-full text-ink md:hidden"
          aria-expanded={open}
          aria-label={open ? "Закрыть меню" : "Открыть меню"}
          onClick={() => setOpen((value) => !value)}
        >
          <span className="sr-only">Меню</span>
          <span className="relative block h-3 w-4">
            <span
              className={`absolute left-0 h-px w-4 bg-ink transition-all ${open ? "top-1.5 rotate-45" : "top-0.5"}`}
            />
            <span
              className={`absolute left-0 h-px w-4 bg-ink transition-all ${open ? "top-1.5 -rotate-45" : "top-2.5"}`}
            />
          </span>
        </button>
      </nav>
      {open ? (
        <div className="absolute inset-x-0 top-12 min-h-[calc(100svh-3rem)] bg-black md:hidden">
          <ul className="wrap flex flex-col gap-1 py-8 text-[2rem] font-medium tracking-tight">
            {site.nav.map((item) => (
              <li key={item.href}>
                <a className="block py-2" href={item.href} onClick={() => setOpen(false)}>
                  {item.label}
                </a>
              </li>
            ))}
            <li>
              <a className="mt-4 inline-flex rounded-full bg-blue px-5 py-2 text-lg font-medium text-white" href="/#contact" onClick={() => setOpen(false)}>
                Написать
              </a>
            </li>
          </ul>
        </div>
      ) : null}
    </header>
  );
}
