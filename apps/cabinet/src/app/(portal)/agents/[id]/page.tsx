import Link from "next/link";
import { notFound } from "next/navigation";
import { AgentChat } from "@/components/AgentChat";
import { ErrorPanel, PageTitle } from "@/components/ui";
import { BlError, blJson } from "@/lib/bl";
import { requireSession } from "@/lib/session";
import type { Agent, Me } from "@/lib/types";

export default async function AgentPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const session = await requireSession(`/app/agents/${id}`);
  let me: Me;
  let agent: Agent | undefined;
  try {
    const [m, list] = await Promise.all([
      blJson<Me>("/v1/me", undefined, session),
      blJson<{ items: Agent[] }>("/v1/agents", undefined, session),
    ]);
    me = m;
    agent = list.items.find((a) => a.id === id);
  } catch (e) {
    return <ErrorPanel detail={e instanceof BlError ? `${e.status}: ${e.message}` : String(e)} />;
  }
  if (!agent) notFound();

  return (
    <>
      <Link href="/" className="mb-4 inline-block text-sm text-link">
        ← Все агенты
      </Link>
      <PageTitle eyebrow={agent.kind === "echo" ? "Демо" : "Агент"} title={agent.title} />
      <p className="-mt-4 mb-8 max-w-2xl text-ink-dim">{agent.description}</p>
      <AgentChat
        agentId={agent.id}
        hint={agent.input_hint}
        initialRemaining={me.quota.remaining}
        dailyLimit={me.quota.daily_limit}
      />
    </>
  );
}
