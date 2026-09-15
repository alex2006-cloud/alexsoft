"use client";

import { useCallback, useEffect, useMemo, useState } from "react";

type NodeKind = "person" | "system" | "external";

type GameNode = {
  id: string;
  label: string;
  kind: NodeKind;
  hint: string;
  x: number;
  y: number;
};

type EdgeDef = {
  id: string;
  from: string;
  to: string;
  label: string;
};

const NODES: GameNode[] = [
  {
    id: "visitor",
    label: "Посетитель",
    kind: "person",
    hint: "Person",
    x: 50,
    y: 12,
  },
  {
    id: "alexsoft",
    label: "alexsoft",
    kind: "system",
    hint: "Software System",
    x: 50,
    y: 48,
  },
  {
    id: "llm",
    label: "LLM API",
    kind: "external",
    hint: "External",
    x: 18,
    y: 84,
  },
  {
    id: "github",
    label: "GitHub",
    kind: "external",
    hint: "External",
    x: 82,
    y: 84,
  },
];

const CORRECT: EdgeDef[] = [
  {
    id: "visitor-alexsoft",
    from: "visitor",
    to: "alexsoft",
    label: "Открывает лендинг",
  },
  {
    id: "alexsoft-llm",
    from: "alexsoft",
    to: "llm",
    label: "Запросы агентов",
  },
  {
    id: "alexsoft-github",
    from: "alexsoft",
    to: "github",
    label: "CI и артефакты",
  },
];

const kindStyles: Record<NodeKind, string> = {
  person: "border-[#7dd3fc] bg-[#0c4a6e]/40 text-[#e0f2fe]",
  system: "border-[#a5b4fc] bg-[#312e81]/50 text-[#e0e7ff]",
  external: "border-[#86efac] bg-[#14532d]/35 text-[#dcfce7]",
};

function edgeKey(a: string, b: string) {
  return [a, b].sort().join("::");
}

function nodeById(id: string) {
  return NODES.find((n) => n.id === id)!;
}

export function ContourGame() {
  const [selected, setSelected] = useState<string | null>(null);
  const [placed, setPlaced] = useState<string[]>([]);
  const [moves, setMoves] = useState(0);
  const [mistakes, setMistakes] = useState(0);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [shakeId, setShakeId] = useState<string | null>(null);
  const [elapsed, setElapsed] = useState(0);
  const [running, setRunning] = useState(true);

  const won = placed.length === CORRECT.length;

  useEffect(() => {
    if (!running || won) return;
    const id = window.setInterval(() => setElapsed((t) => t + 1), 1000);
    return () => window.clearInterval(id);
  }, [running, won]);

  useEffect(() => {
    if (won) setRunning(false);
  }, [won]);

  const placedEdges = useMemo(
    () => CORRECT.filter((e) => placed.includes(e.id)),
    [placed],
  );

  const reset = useCallback(() => {
    setSelected(null);
    setPlaced([]);
    setMoves(0);
    setMistakes(0);
    setFeedback(null);
    setShakeId(null);
    setElapsed(0);
    setRunning(true);
  }, []);

  const onNodeClick = (id: string) => {
    if (won) return;

    if (!selected) {
      setSelected(id);
      setFeedback("Выберите второй блок — куда ведёт связь.");
      return;
    }

    if (selected === id) {
      setSelected(null);
      setFeedback(null);
      return;
    }

    setMoves((m) => m + 1);
    const match = CORRECT.find(
      (e) =>
        (e.from === selected && e.to === id) ||
        (e.from === id && e.to === selected),
    );

    if (!match) {
      setMistakes((n) => n + 1);
      setShakeId(edgeKey(selected, id));
      setFeedback("Так на контекстной диаграмме не связано. Попробуйте иначе.");
      window.setTimeout(() => setShakeId(null), 420);
      setSelected(null);
      return;
    }

    if (placed.includes(match.id)) {
      setFeedback("Эта связь уже есть.");
      setSelected(null);
      return;
    }

    const next = [...placed, match.id];
    setPlaced(next);
    setSelected(null);
    setFeedback(
      next.length === CORRECT.length
        ? "Контур собран — это упрощённый System Context alexsoft."
        : `Связь «${match.label}» на месте. Осталось ${CORRECT.length - next.length}.`,
    );
  };

  return (
    <div className="contour-game">
      <div className="mb-6 flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="eyebrow">Уровень 1 · System Context</p>
          <h1 className="display mt-2 text-[clamp(1.8rem,4vw,2.6rem)]">Контур</h1>
          <p className="mt-3 max-w-xl text-[1.05rem] leading-relaxed text-ink-dim">
            Соедините блоки так, как на C4 Level 1: посетитель пользуется платформой, alexsoft
            ходит во внешние системы. Клик по первому блоку, затем по второму.
          </p>
        </div>
        <div className="flex flex-wrap gap-3 text-sm text-ink/80">
          <Stat label="Связи" value={`${placed.length}/${CORRECT.length}`} />
          <Stat label="Ходы" value={String(moves)} />
          <Stat label="Ошибки" value={String(mistakes)} />
          <Stat label="Время" value={formatTime(elapsed)} />
        </div>
      </div>

      <div className="mb-4 flex flex-wrap gap-2 text-xs text-ink-dim">
        <Legend swatch="border-[#7dd3fc] bg-[#0c4a6e]/40" label="Person" />
        <Legend swatch="border-[#a5b4fc] bg-[#312e81]/50" label="Software System" />
        <Legend swatch="border-[#86efac] bg-[#14532d]/35" label="External" />
      </div>

      <div
        className={`relative overflow-hidden rounded-[28px] border border-line bg-panel ${
          shakeId ? "contour-shake" : ""
        }`}
        style={{ minHeight: "min(62vh, 520px)" }}
      >
        <svg
          className="pointer-events-none absolute inset-0 h-full w-full"
          aria-hidden
        >
          {placedEdges.map((edge) => {
            const a = nodeById(edge.from);
            const b = nodeById(edge.to);
            return (
              <g key={edge.id}>
                <line
                  x1={`${a.x}%`}
                  y1={`${a.y}%`}
                  x2={`${b.x}%`}
                  y2={`${b.y}%`}
                  stroke="#2997ff"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                />
                <text
                  x={`${(a.x + b.x) / 2}%`}
                  y={`${(a.y + b.y) / 2 - 2}%`}
                  textAnchor="middle"
                  className="fill-ink text-[11px]"
                  style={{ fill: "#86868b" }}
                >
                  {edge.label}
                </text>
              </g>
            );
          })}
          {selected
            ? NODES.filter((n) => n.id !== selected).map((n) => {
                const a = nodeById(selected);
                return (
                  <line
                    key={`preview-${n.id}`}
                    x1={`${a.x}%`}
                    y1={`${a.y}%`}
                    x2={`${n.x}%`}
                    y2={`${n.y}%`}
                    stroke="#2a2a2c"
                    strokeWidth="1.5"
                    strokeDasharray="4 6"
                  />
                );
              })
            : null}
        </svg>

        {NODES.map((node) => {
          const isSelected = selected === node.id;
          const isConnected = placedEdges.some(
            (e) => e.from === node.id || e.to === node.id,
          );
          return (
            <button
              key={node.id}
              type="button"
              onClick={() => onNodeClick(node.id)}
              className={`absolute w-[min(42%,11.5rem)] -translate-x-1/2 -translate-y-1/2 rounded-2xl border px-3 py-3 text-left transition-[transform,box-shadow,border-color] duration-200 ${
                kindStyles[node.kind]
              } ${
                isSelected
                  ? "scale-[1.04] shadow-[0_0_0_2px_rgba(41,151,255,0.85)]"
                  : "hover:scale-[1.02]"
              } ${isConnected ? "ring-1 ring-white/15" : ""}`}
              style={{ left: `${node.x}%`, top: `${node.y}%` }}
              aria-pressed={isSelected}
            >
              <span className="block text-[0.65rem] uppercase tracking-[0.08em] opacity-70">
                {node.hint}
              </span>
              <span className="mt-1 block font-display text-[1.05rem] font-semibold tracking-tight">
                {node.label}
              </span>
            </button>
          );
        })}

        {won ? (
          <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/55 px-6 backdrop-blur-[2px]">
            <div className="max-w-md rounded-[24px] border border-white/10 bg-panel px-6 py-7 text-center shadow-2xl">
              <p className="eyebrow text-link">Победа</p>
              <h2 className="display mt-2 text-[1.8rem]">Контур собран</h2>
              <p className="mt-3 text-sm leading-relaxed text-ink-dim">
                {moves} ход{moves === 1 ? "" : moves < 5 ? "а" : "ов"}, {mistakes}{" "}
                ошиб{mistakes === 1 ? "ка" : mistakes > 1 && mistakes < 5 ? "ки" : "ок"},{" "}
                {formatTime(elapsed)}.
              </p>
              <button type="button" className="btn btn-primary mt-6" onClick={reset}>
                Ещё раз
              </button>
            </div>
          </div>
        ) : null}
      </div>

      <div className="mt-5 flex flex-wrap items-center justify-between gap-3">
        <p className="min-h-[1.5rem] text-sm text-ink-dim" role="status">
          {feedback}
        </p>
        <button
          type="button"
          className="btn btn-ghost text-sm"
          onClick={reset}
        >
          Сбросить
        </button>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-line bg-black/40 px-3.5 py-2">
      <p className="text-[0.65rem] uppercase tracking-[0.08em] text-ink-dim">{label}</p>
      <p className="mt-0.5 font-medium tabular-nums text-ink">{value}</p>
    </div>
  );
}

function Legend({ swatch, label }: { swatch: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-2 rounded-full border border-line px-2.5 py-1">
      <span className={`h-2.5 w-2.5 rounded-full border ${swatch}`} />
      {label}
    </span>
  );
}

function formatTime(total: number) {
  const m = Math.floor(total / 60);
  const s = total % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}
