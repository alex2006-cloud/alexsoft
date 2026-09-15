import type { Metadata, Viewport } from "next";
import { Inter, Inter_Tight } from "next/font/google";
import { GamesNav } from "@/components/GamesNav";
import "./globals.css";

const inter = Inter({
  subsets: ["latin", "cyrillic", "cyrillic-ext"],
  variable: "--font-inter",
  display: "swap",
});

const interTight = Inter_Tight({
  subsets: ["latin", "cyrillic", "cyrillic-ext"],
  variable: "--font-inter-tight",
  display: "swap",
});

const siteUrl = process.env.LANDING_URL ?? "http://localhost:3000";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "Игры — alexsoft",
    template: "%s — alexsoft",
  },
  description: "Мини-игры Personal Ecosystem Lab.",
};

export const viewport: Viewport = {
  themeColor: "#000000",
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ru" className={`${inter.variable} ${interTight.variable}`}>
      <body className="min-h-screen bg-canvas font-sans text-ink antialiased">
        <GamesNav />
        {children}
      </body>
    </html>
  );
}
