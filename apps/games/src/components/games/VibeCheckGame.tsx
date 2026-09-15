"use client";

import { useCallback, useEffect, useRef, useState } from "react";

type Phase = "idle" | "play" | "over";

const PRAISE = [
  "W",
  "SLAY",
  "BASED",
  "NO CAP",
  "MAIN CHARACTER",
  "IT'S GIVING",
  "ATE",
  "VALID",
  "LOWKEY FIRE",
  "BET",
  "UNDERSTOOD THE ASSIGNMENT",
];

const ROAST = [
  "L",
  "MID",
  "COOKED",
  "DELULU",
  "SKILL ISSUE",
  "NOT IT",
  "BRUH",
  "TOUCH GRASS",
  "IT'S OVER",
  "NPC ENERGY",
];

function pick<T>(arr: T[]) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function sfx(kind: "hit" | "miss" | "start") {
  try {
    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();
    osc.connect(gain);
    gain.connect(ctx.destination);
    const t = ctx.currentTime;
    if (kind === "hit") {
      osc.type = "square";
      osc.frequency.setValueAtTime(520, t);
      osc.frequency.exponentialRampToValueAtTime(880, t + 0.08);
      gain.gain.setValueAtTime(0.06, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.12);
      osc.start(t);
      osc.stop(t + 0.12);
    } else if (kind === "miss") {
      osc.type = "sawtooth";
      osc.frequency.setValueAtTime(180, t);
      osc.frequency.exponentialRampToValueAtTime(90, t + 0.2);
      gain.gain.setValueAtTime(0.05, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.2);
      osc.start(t);
      osc.stop(t + 0.2);
    } else {
      osc.type = "triangle";
      osc.frequency.setValueAtTime(330, t);
      osc.frequency.setValueAtTime(440, t + 0.06);
      gain.gain.setValueAtTime(0.04, t);
      gain.gain.exponentialRampToValueAtTime(0.001, t + 0.15);
      osc.start(t);
      osc.stop(t + 0.15);
    }
    osc.onended = () => void ctx.close();
  } catch {
    /* no audio */
  }
}

export function VibeCheckGame() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [score, setScore] = useState(0);
  const [streak, setStreak] = useState(0);
  const [best, setBest] = useState(0);
  const [timeLeft, setTimeLeft] = useState(30);
  const [meter, setMeter] = useState(0.5);
  const [flash, setFlash] = useState<string | null>(null);
  const [flashKind, setFlashKind] = useState<"win" | "lose">("win");
  const [zoneWidth, setZoneWidth] = useState(0.28);

  const meterRef = useRef(0.5);
  const dirRef = useRef(1);
  const speedRef = useRef(1.1);
  const zoneRef = useRef(0.28);
  const rafRef = useRef(0);
  const lastRef = useRef(0);
  const phaseRef = useRef<Phase>("idle");
  const streakRef = useRef(0);

  phaseRef.current = phase;
  streakRef.current = streak;

  const start = useCallback(() => {
    meterRef.current = 0.5;
    dirRef.current = 1;
    speedRef.current = 1.1;
    zoneRef.current = 0.28;
    streakRef.current = 0;
    setZoneWidth(0.28);
    setMeter(0.5);
    setScore(0);
    setStreak(0);
    setTimeLeft(30);
    setFlash(null);
    setPhase("play");
    sfx("start");
  }, []);

  const endGame = useCallback((finalScore: number) => {
    setPhase("over");
    setBest((b) => Math.max(b, finalScore));
  }, []);

  const check = useCallback(() => {
    if (phaseRef.current !== "play") return;
    const pos = meterRef.current;
    const half = zoneRef.current / 2;
    const inZone = pos >= 0.5 - half && pos <= 0.5 + half;
    const perfect = pos >= 0.5 - half * 0.35 && pos <= 0.5 + half * 0.35;

    if (inZone) {
      const add = perfect ? 150 + streakRef.current * 20 : 80 + streakRef.current * 10;
      streakRef.current += 1;
      setStreak(streakRef.current);
      setScore((s) => s + add);
      setFlash(pick(PRAISE));
      setFlashKind("win");
      sfx("hit");
      speedRef.current = Math.min(3.2, speedRef.current + 0.08);
      zoneRef.current = Math.max(0.12, zoneRef.current - 0.012);
      setZoneWidth(zoneRef.current);
    } else {
      streakRef.current = 0;
      setStreak(0);
      setFlash(pick(ROAST));
      setFlashKind("lose");
      sfx("miss");
      speedRef.current = Math.max(0.9, speedRef.current - 0.15);
      zoneRef.current = Math.min(0.32, zoneRef.current + 0.02);
      setZoneWidth(zoneRef.current);
    }

    window.setTimeout(() => setFlash(null), 700);
  }, []);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.code === "Space" || e.code === "Enter") {
        e.preventDefault();
        if (phaseRef.current === "idle" || phaseRef.current === "over") start();
        else check();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [check, start]);

  useEffect(() => {
    if (phase !== "play") return;
    const tick = window.setInterval(() => {
      setTimeLeft((t) => {
        if (t <= 1) {
          window.clearInterval(tick);
          setScore((s) => {
            endGame(s);
            return s;
          });
          return 0;
        }
        return t - 1;
      });
    }, 1000);
    return () => window.clearInterval(tick);
  }, [phase, endGame]);

  useEffect(() => {
    const loop = (ts: number) => {
      const last = lastRef.current || ts;
      const dt = Math.min(0.033, (ts - last) / 1000);
      lastRef.current = ts;

      if (phaseRef.current === "play") {
        let m = meterRef.current + dirRef.current * speedRef.current * dt;
        if (m >= 1) {
          m = 1;
          dirRef.current = -1;
        } else if (m <= 0) {
          m = 0;
          dirRef.current = 1;
        }
        meterRef.current = m;
        setMeter(m);
      }

      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafRef.current);
  }, []);

  const zoneHalf = zoneWidth / 2;
  const zoneLeft = (0.5 - zoneHalf) * 100;
  const zoneWidthPct = zoneWidth * 100;
  const needleLeft = meter * 100;

  return (
    <div className="vibe-check">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow text-[#ff6ec7]">Gen Z edition · 30 sec</p>
          <h1 className="display mt-2 text-[clamp(1.8rem,4vw,2.8rem)]">
            <span className="bg-gradient-to-r from-[#ff6ec7] via-[#c084fc] to-[#5eead4] bg-clip-text text-transparent">
              Вайб-чек
            </span>
          </h1>
          <p className="mt-3 max-w-xl text-[1.05rem] leading-relaxed text-ink-dim">
            Поймай зелёную зону, когда полоска вайба в центре. Чем длиннее streak — тем уже окно и
            быстрее полоска. Miss = L.
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-sm">
          <Stat label="Очки" value={String(score)} />
          <Stat label="Streak" value={String(streak)} accent />
          <Stat label="Таймер" value={`${timeLeft}s`} />
          <Stat label="Рекорд" value={String(best)} />
        </div>
      </div>

      <button
        type="button"
        className="vibe-check-stage relative w-full overflow-hidden rounded-[28px] border border-white/10 bg-gradient-to-br from-[#1a0a2e] via-[#0f172a] to-[#042f2e] p-8 text-left outline-none focus-visible:ring-2 focus-visible:ring-[#ff6ec7]"
        onClick={() => {
          if (phase === "idle" || phase === "over") start();
          else check();
        }}
        aria-label="Поймать вайб"
      >
        <div className="pointer-events-none absolute -right-20 -top-20 h-56 w-56 rounded-full bg-[#ff6ec7]/20 blur-3xl" />
        <div className="pointer-events-none absolute -bottom-16 -left-16 h-48 w-48 rounded-full bg-[#5eead4]/15 blur-3xl" />

        <p className="relative text-center text-xs font-semibold uppercase tracking-[0.2em] text-[#c084fc]">
          {phase === "play" ? "Жми когда в зоне" : "Tap / Space"}
        </p>

        <div className="relative mx-auto mt-10 max-w-lg">
          <div className="relative h-14 overflow-hidden rounded-full border border-white/15 bg-black/50 shadow-inner">
            <div
              className="absolute inset-y-1 rounded-full bg-gradient-to-r from-[#22c55e]/30 via-[#4ade80]/50 to-[#22c55e]/30 transition-[left,width] duration-150"
              style={{ left: `${zoneLeft}%`, width: `${zoneWidthPct}%` }}
            />
            <div
              className="absolute inset-y-0 w-1.5 -translate-x-1/2 rounded-full bg-white shadow-[0_0_16px_#fff,0_0_32px_#ff6ec7]"
              style={{ left: `${needleLeft}%` }}
            />
          </div>
          <div className="mt-3 flex justify-between text-[11px] font-medium uppercase tracking-wider text-ink-dim">
            <span>cringe</span>
            <span className="text-[#4ade80]">vibe zone</span>
            <span>mid</span>
          </div>
        </div>

        {flash ? (
          <p
            className={`relative mt-10 text-center font-display text-[clamp(1.6rem,5vw,2.8rem)] font-bold tracking-tight ${
              flashKind === "win"
                ? "animate-pulse text-[#4ade80]"
                : "text-[#fb7185]"
            }`}
          >
            {flash}
          </p>
        ) : (
          <p className="relative mt-10 text-center text-sm text-ink-dim">
            {phase === "play"
              ? "Space / клик — поймать вайб"
              : phase === "over"
                ? `Итог: ${score} · ${score >= 1200 ? "certified zoomer" : score >= 600 ? "valid" : "go again"}`
                : "30 секунд. Поймай максимум W."}
          </p>
        )}

        {(phase === "idle" || phase === "over") && (
          <div className="relative mt-8 flex justify-center">
            <span className="rounded-full bg-gradient-to-r from-[#ff6ec7] to-[#c084fc] px-6 py-2.5 text-sm font-semibold text-white shadow-lg shadow-[#ff6ec7]/25">
              {phase === "over" ? "Ещё раунд" : "Начать вайб-чек"}
            </span>
          </div>
        )}
      </button>

      <p className="mt-4 text-sm text-ink-dim">
        Управление: <span className="text-ink">Space</span> или клик по полю. Streak увеличивает
        очки, но сужает зону.
      </p>
    </div>
  );
}

function Stat({
  label,
  value,
  accent,
}: {
  label: string;
  value: string;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-2xl border px-3.5 py-2 ${
        accent ? "border-[#ff6ec7]/40 bg-[#ff6ec7]/10" : "border-line bg-black/40"
      }`}
    >
      <p className="text-[0.65rem] uppercase tracking-[0.08em] text-ink-dim">{label}</p>
      <p className="mt-0.5 font-medium tabular-nums text-ink">{value}</p>
    </div>
  );
}
