"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Chiptune } from "@/components/games/desant/chiptune";

const W = 960;
const H = 540;
const WORLD_W = 3200;
const GRAVITY = 2200;
const MOVE = 320;
const JUMP = 780;
const BULLET_SPEED = 620;

type Rect = { x: number; y: number; w: number; h: number };

type Bullet = Rect & { vx: number; friendly: boolean; life: number };
type Enemy = Rect & {
  vx: number;
  hp: number;
  kind: "walker" | "turret";
  cooldown: number;
  facing: 1 | -1;
};
type Particle = { x: number; y: number; vx: number; vy: number; life: number; color: string };

type Phase = "title" | "play" | "dead" | "win";

type State = {
  phase: Phase;
  player: Rect & {
    vx: number;
    vy: number;
    onGround: boolean;
    facing: 1 | -1;
    shootCd: number;
    invuln: number;
  };
  lives: number;
  score: number;
  cameraX: number;
  bullets: Bullet[];
  enemies: Enemy[];
  particles: Particle[];
  platforms: Rect[];
  flag: Rect;
  keys: Record<string, boolean>;
};

function aabb(a: Rect, b: Rect) {
  return a.x < b.x + b.w && a.x + a.w > b.x && a.y < b.y + b.h && a.y + a.h > b.y;
}

function buildLevel(): { platforms: Rect[]; enemies: Enemy[]; flag: Rect } {
  const platforms: Rect[] = [
    { x: 0, y: 480, w: WORLD_W, h: 60 },
    { x: 280, y: 390, w: 160, h: 18 },
    { x: 520, y: 320, w: 140, h: 18 },
    { x: 780, y: 390, w: 180, h: 18 },
    { x: 1100, y: 340, w: 120, h: 18 },
    { x: 1320, y: 280, w: 200, h: 18 },
    { x: 1680, y: 390, w: 160, h: 18 },
    { x: 1960, y: 320, w: 220, h: 18 },
    { x: 2360, y: 370, w: 180, h: 18 },
    { x: 2680, y: 300, w: 200, h: 18 },
  ];

  const enemies: Enemy[] = [
    { x: 420, y: 448, w: 28, h: 32, vx: -50, hp: 2, kind: "walker", cooldown: 0, facing: -1 },
    { x: 860, y: 358, w: 28, h: 32, vx: 55, hp: 2, kind: "walker", cooldown: 0, facing: 1 },
    { x: 1180, y: 308, w: 30, h: 28, vx: 0, hp: 3, kind: "turret", cooldown: 1.2, facing: -1 },
    { x: 1480, y: 248, w: 28, h: 32, vx: -60, hp: 2, kind: "walker", cooldown: 0, facing: -1 },
    { x: 1800, y: 358, w: 28, h: 32, vx: 50, hp: 2, kind: "walker", cooldown: 0, facing: 1 },
    { x: 2100, y: 288, w: 30, h: 28, vx: 0, hp: 3, kind: "turret", cooldown: 0.8, facing: -1 },
    { x: 2480, y: 338, w: 28, h: 32, vx: -55, hp: 2, kind: "walker", cooldown: 0, facing: -1 },
    { x: 2860, y: 268, w: 30, h: 28, vx: 0, hp: 4, kind: "turret", cooldown: 0.6, facing: -1 },
  ];

  return { platforms, enemies, flag: { x: 3050, y: 420, w: 24, h: 60 } };
}

function createState(keys: Record<string, boolean> = {}): State {
  const { platforms, enemies, flag } = buildLevel();
  return {
    phase: "title",
    player: {
      x: 80,
      y: 400,
      w: 26,
      h: 36,
      vx: 0,
      vy: 0,
      onGround: false,
      facing: 1,
      shootCd: 0,
      invuln: 0,
    },
    lives: 3,
    score: 0,
    cameraX: 0,
    bullets: [],
    enemies,
    particles: [],
    platforms,
    flag,
    keys,
  };
}

function burst(particles: Particle[], x: number, y: number, color: string, n = 10) {
  for (let i = 0; i < n; i++) {
    particles.push({
      x,
      y,
      vx: (Math.random() - 0.5) * 280,
      vy: (Math.random() - 0.8) * 280,
      life: 0.35 + Math.random() * 0.25,
      color,
    });
  }
}

export function DesantGame() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const stateRef = useRef<State>(createState());
  const musicRef = useRef<Chiptune | null>(null);
  const rafRef = useRef(0);
  const lastRef = useRef(0);
  const [ui, setUi] = useState({ lives: 3, score: 0, muted: false, phase: "title" as Phase });

  const syncUi = useCallback(() => {
    const s = stateRef.current;
    setUi({
      lives: s.lives,
      score: s.score,
      muted: musicRef.current?.muted ?? false,
      phase: s.phase,
    });
  }, []);

  const startGame = useCallback(async () => {
    const music = musicRef.current ?? new Chiptune();
    musicRef.current = music;
    await music.resume();
    music.stop();
    music.start();
    stateRef.current = { ...createState(stateRef.current.keys), phase: "play" };
    syncUi();
    canvasRef.current?.focus();
  }, [syncUi]);

  const toggleMute = useCallback(() => {
    const music = musicRef.current ?? new Chiptune();
    musicRef.current = music;
    music.setMuted(!music.muted);
    syncUi();
  }, [syncUi]);

  useEffect(() => {
    musicRef.current = new Chiptune();
    const canvas = canvasRef.current;
    const ctx = canvas?.getContext("2d");
    if (!canvas || !ctx) return;

    const hurt = (s: State, fell: boolean) => {
      if (s.phase !== "play") return;
      s.lives -= 1;
      musicRef.current?.sfx("die");
      burst(s.particles, s.player.x + 13, s.player.y + 18, "#93c5fd", 14);
      if (s.lives <= 0) {
        s.phase = "dead";
        musicRef.current?.stop();
        syncUi();
        return;
      }
      if (fell) s.player.x = Math.max(40, s.player.x - 120);
      s.player.y = 360;
      s.player.vy = 0;
      s.player.invuln = 1.5;
      syncUi();
    };

    const onKey = (e: KeyboardEvent, down: boolean) => {
      const k = e.key.toLowerCase();
      const map: Record<string, string> = {
        arrowleft: "left",
        arrowright: "right",
        arrowup: "jump",
        " ": "jump",
        a: "left",
        d: "right",
        w: "jump",
        z: "shoot",
        j: "shoot",
        control: "shoot",
      };
      const action = map[k];
      if (action) {
        e.preventDefault();
        stateRef.current.keys[action] = down;
      }
      if (down && (k === "enter" || k === " ")) {
        const phase = stateRef.current.phase;
        if (phase === "title" || phase === "dead" || phase === "win") {
          e.preventDefault();
          void startGame();
        }
      }
      if (down && k === "m") {
        e.preventDefault();
        toggleMute();
      }
    };
    const down = (e: KeyboardEvent) => onKey(e, true);
    const up = (e: KeyboardEvent) => onKey(e, false);
    window.addEventListener("keydown", down);
    window.addEventListener("keyup", up);

    const update = (dt: number) => {
      const s = stateRef.current;
      if (s.phase !== "play") return;
      const p = s.player;
      const keys = s.keys;

      p.vx = 0;
      if (keys.left) {
        p.vx = -MOVE;
        p.facing = -1;
      }
      if (keys.right) {
        p.vx = MOVE;
        p.facing = 1;
      }
      if (keys.jump && p.onGround) {
        p.vy = -JUMP;
        p.onGround = false;
        musicRef.current?.sfx("jump");
      }

      p.vy += GRAVITY * dt;
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      p.onGround = false;

      for (const plat of s.platforms) {
        if (!aabb(p, plat)) continue;
        const prevBottom = p.y + p.h - p.vy * dt;
        if (p.vy >= 0 && prevBottom <= plat.y + 6) {
          p.y = plat.y - p.h;
          p.vy = 0;
          p.onGround = true;
        }
      }

      p.x = Math.max(8, Math.min(WORLD_W - p.w - 8, p.x));
      if (p.y > H + 80) hurt(s, true);

      p.shootCd = Math.max(0, p.shootCd - dt);
      p.invuln = Math.max(0, p.invuln - dt);
      if (keys.shoot && p.shootCd <= 0) {
        p.shootCd = 0.18;
        s.bullets.push({
          x: p.x + (p.facing > 0 ? p.w : -8),
          y: p.y + 14,
          w: 10,
          h: 4,
          vx: BULLET_SPEED * p.facing,
          friendly: true,
          life: 1.2,
        });
        musicRef.current?.sfx("shoot");
      }

      for (const e of s.enemies) {
        if (e.kind === "walker") {
          e.x += e.vx * dt;
          e.facing = e.vx >= 0 ? 1 : -1;
          const under = s.platforms.find(
            (pl) =>
              e.x + e.w / 2 > pl.x &&
              e.x + e.w / 2 < pl.x + pl.w &&
              Math.abs(e.y + e.h - pl.y) < 8,
          );
          if (!under || e.x < under.x + 4 || e.x + e.w > under.x + under.w - 4) {
            e.vx *= -1;
          }
        } else {
          e.cooldown -= dt;
          if (e.cooldown <= 0) {
            e.cooldown = 1.4;
            const dir = p.x < e.x ? -1 : 1;
            e.facing = dir as 1 | -1;
            s.bullets.push({
              x: e.x + e.w / 2,
              y: e.y + 10,
              w: 8,
              h: 4,
              vx: 280 * dir,
              friendly: false,
              life: 2,
            });
          }
        }
      }

      for (const b of s.bullets) {
        b.x += b.vx * dt;
        b.life -= dt;
      }

      for (const b of s.bullets) {
        if (!b.friendly || b.life <= 0) continue;
        for (const e of s.enemies) {
          if (e.hp <= 0) continue;
          if (!aabb(b, e)) continue;
          b.life = 0;
          e.hp -= 1;
          burst(s.particles, e.x + e.w / 2, e.y + e.h / 2, "#fbbf24", 8);
          musicRef.current?.sfx("hit");
          if (e.hp <= 0) {
            s.score += e.kind === "turret" ? 300 : 100;
            burst(s.particles, e.x + e.w / 2, e.y + e.h / 2, "#fb7185", 16);
            syncUi();
          }
        }
      }

      for (const b of s.bullets) {
        if (b.friendly || b.life <= 0 || p.invuln > 0) continue;
        if (aabb(b, p)) {
          b.life = 0;
          hurt(s, false);
        }
      }

      for (const e of s.enemies) {
        if (e.hp <= 0 || p.invuln > 0) continue;
        if (aabb(p, e)) hurt(s, false);
      }

      s.enemies = s.enemies.filter((e) => e.hp > 0);
      s.bullets = s.bullets.filter((b) => b.life > 0 && b.x > -40 && b.x < WORLD_W + 40);
      for (const pt of s.particles) {
        pt.x += pt.vx * dt;
        pt.y += pt.vy * dt;
        pt.vy += 600 * dt;
        pt.life -= dt;
      }
      s.particles = s.particles.filter((pt) => pt.life > 0);

      if (aabb(p, s.flag)) {
        s.phase = "win";
        musicRef.current?.sfx("win");
        musicRef.current?.stop();
        syncUi();
      }

      s.cameraX = Math.max(0, Math.min(WORLD_W - W, p.x + p.w / 2 - W / 2));
    };

    const draw = () => {
      const s = stateRef.current;
      const cam = s.cameraX;
      ctx.fillStyle = "#0b1220";
      ctx.fillRect(0, 0, W, H);

      for (let i = 0; i < 6; i++) {
        const y = 60 + i * 55;
        ctx.fillStyle = i % 2 === 0 ? "#10233d" : "#0e1c30";
        ctx.fillRect(0, y, W, 40);
        ctx.fillStyle = "#16324f";
        for (let x = -((cam * (0.2 + i * 0.05)) % 120); x < W; x += 120) {
          ctx.beginPath();
          ctx.moveTo(x, y + 40);
          ctx.lineTo(x + 40, y + 8);
          ctx.lineTo(x + 80, y + 40);
          ctx.fill();
        }
      }

      for (const plat of s.platforms) {
        const x = plat.x - cam;
        ctx.fillStyle = "#3f2e1f";
        ctx.fillRect(x, plat.y, plat.w, plat.h);
        ctx.fillStyle = "#4ade80";
        ctx.fillRect(x, plat.y, plat.w, 5);
      }

      const fx = s.flag.x - cam;
      ctx.fillStyle = "#e2e8f0";
      ctx.fillRect(fx + 10, s.flag.y, 4, s.flag.h);
      ctx.fillStyle = "#ef4444";
      ctx.beginPath();
      ctx.moveTo(fx + 14, s.flag.y);
      ctx.lineTo(fx + 42, s.flag.y + 12);
      ctx.lineTo(fx + 14, s.flag.y + 24);
      ctx.fill();

      for (const e of s.enemies) {
        const x = e.x - cam;
        if (e.kind === "walker") {
          ctx.fillStyle = "#b91c1c";
          ctx.fillRect(x, e.y, e.w, e.h);
          ctx.fillStyle = "#fef3c7";
          ctx.fillRect(x + 6, e.y + 6, 14, 10);
        } else {
          ctx.fillStyle = "#7c2d12";
          ctx.fillRect(x, e.y + 8, e.w, e.h - 8);
          ctx.fillStyle = "#f97316";
          ctx.fillRect(x + 4, e.y, e.w - 8, 12);
        }
      }

      const p = s.player;
      if (p.invuln <= 0 || Math.floor(p.invuln * 12) % 2 === 0) {
        const x = p.x - cam;
        ctx.fillStyle = "#38bdf8";
        ctx.fillRect(x, p.y, p.w, p.h);
        ctx.fillStyle = "#0f172a";
        ctx.fillRect(x + (p.facing > 0 ? 14 : 2), p.y + 8, 10, 8);
        ctx.fillStyle = "#fbbf24";
        ctx.fillRect(x + (p.facing > 0 ? p.w : -10), p.y + 16, 12, 5);
      }

      for (const b of s.bullets) {
        ctx.fillStyle = b.friendly ? "#fde68a" : "#fb7185";
        ctx.fillRect(b.x - cam, b.y, b.w, b.h);
      }

      for (const pt of s.particles) {
        ctx.globalAlpha = Math.max(0, pt.life * 2);
        ctx.fillStyle = pt.color;
        ctx.fillRect(pt.x - cam, pt.y, 3, 3);
        ctx.globalAlpha = 1;
      }

      const muted = musicRef.current?.muted ?? false;
      ctx.fillStyle = "rgba(0,0,0,0.45)";
      ctx.fillRect(0, 0, W, 36);
      ctx.fillStyle = "#e2e8f0";
      ctx.font = "600 14px ui-sans-serif, system-ui, sans-serif";
      ctx.fillText(`ЖИЗНИ ${s.lives}`, 16, 24);
      ctx.fillText(`ОЧКИ ${s.score}`, 140, 24);
      ctx.fillText(muted ? "M · звук выкл" : "M · звук", W - 140, 24);

      if (s.phase !== "play") {
        ctx.fillStyle = "rgba(0,0,0,0.62)";
        ctx.fillRect(0, 0, W, H);
        ctx.textAlign = "center";
        ctx.fillStyle = "#f8fafc";
        ctx.font = "700 36px ui-sans-serif, system-ui, sans-serif";
        const title =
          s.phase === "title" ? "ДЕСАНТ" : s.phase === "win" ? "МИССИЯ ВЫПОЛНЕНА" : "GAME OVER";
        ctx.fillText(title, W / 2, H / 2 - 40);
        ctx.font = "500 16px ui-sans-serif, system-ui, sans-serif";
        ctx.fillStyle = "#94a3b8";
        ctx.fillText(
          s.phase === "title"
            ? "Run & Gun в духе классики Dendy · оригинальный чиптюн"
            : s.phase === "win"
              ? `Счёт ${s.score} · Enter — ещё раз`
              : "Enter — начать заново",
          W / 2,
          H / 2,
        );
        ctx.fillStyle = "#38bdf8";
        ctx.fillText("Enter / Space — старт", W / 2, H / 2 + 36);
        ctx.fillStyle = "#64748b";
        ctx.font = "500 13px ui-sans-serif, system-ui, sans-serif";
        ctx.fillText("← → движение · Space прыжок · Z стрельба · M музыка", W / 2, H / 2 + 68);
        ctx.textAlign = "left";
      }
    };

    const loop = (ts: number) => {
      const last = lastRef.current || ts;
      const dt = Math.min(0.033, (ts - last) / 1000);
      lastRef.current = ts;
      update(dt);
      draw();
      rafRef.current = requestAnimationFrame(loop);
    };
    rafRef.current = requestAnimationFrame(loop);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener("keydown", down);
      window.removeEventListener("keyup", up);
      musicRef.current?.dispose();
      musicRef.current = null;
    };
  }, [startGame, syncUi, toggleMute]);

  return (
    <div className="desant-game">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Run &amp; Gun · Dendy spirit</p>
          <h1 className="display mt-2 text-[clamp(1.8rem,4vw,2.6rem)]">Десант</h1>
          <p className="mt-3 max-w-xl text-[1.05rem] leading-relaxed text-ink-dim">
            Боковой шутер в духе Contra: беги, прыгай, стреляй, доберись до флага. Музыка —
            оригинальный чиптюн в браузере (не саундтрек Konami).
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button type="button" className="btn btn-primary" onClick={() => void startGame()}>
            {ui.phase === "play" ? "Заново" : "Играть"}
          </button>
          <button type="button" className="btn btn-ghost" onClick={toggleMute}>
            {ui.muted ? "Включить звук" : "Выключить звук"}
          </button>
        </div>
      </div>

      <div className="overflow-hidden rounded-[20px] border border-line bg-black shadow-[0_0_0_1px_rgba(255,255,255,0.04)]">
        <canvas
          ref={canvasRef}
          width={W}
          height={H}
          className="block h-auto w-full touch-none"
          tabIndex={0}
          aria-label="Игра Десант"
        />
      </div>

      <p className="mt-4 text-sm text-ink-dim">
        Управление: <span className="text-ink">←→</span> / <span className="text-ink">A D</span> ·
        прыжок <span className="text-ink">Space</span> · огонь <span className="text-ink">Z</span> ·
        музыка <span className="text-ink">M</span>. Кликните по полю, если клавиши не реагируют.
      </p>
    </div>
  );
}
