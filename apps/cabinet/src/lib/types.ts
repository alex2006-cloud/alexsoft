// Mirrors artifacts/api/bl.openapi.yaml

export type RunStatus = "queued" | "running" | "succeeded" | "failed";

export interface Quota {
  daily_limit: number;
  used_today: number;
  remaining: number;
  resets_at: string;
}

export interface Me {
  sub: string;
  username: string;
  email: string;
  name: string;
  roles: string[];
  groups: string[];
  quota: Quota;
}

export interface Agent {
  id: string;
  title: string;
  description: string;
  kind: "echo" | "langgraph";
  enabled: boolean;
  input_hint?: string | null;
}

export interface Run {
  id: string;
  agent_id: string;
  user_sub: string;
  username?: string | null;
  status: RunStatus;
  input: string;
  output?: string | null;
  error?: string | null;
  thread_id?: string | null;
  trace_id?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface Page<T> {
  items: T[];
  total: number;
}

export interface AdminUser {
  id: number;
  username: string;
  email: string;
  name: string;
  is_active: boolean;
  groups: string[];
  date_joined?: string | null;
  last_login?: string | null;
}

export interface Stats {
  runs_total: number;
  runs_today: number;
  failed_today: number;
  active_users_today: number;
  by_agent: { agent_id: string; runs: number }[];
}
