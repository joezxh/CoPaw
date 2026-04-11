export interface DLPRule {
  id?: string;
  rule_name: string;
  description: string | null;
  pattern_regex: string;
  action: "mask" | "alert" | "block";
  is_active: boolean;
  is_builtin: boolean;
  created_at?: string;
}

export interface DLPEvent {
  id: string;
  rule_name: string;
  action_taken: string;
  content_summary: string | null;
  user_id: string | null;
  context_path: string | null;
  triggered_at: string;
}

import { request } from "../request";

export const getBuiltinRules = async () => {
  return request<DLPRule[]>("/api/enterprise/dlp/rules/builtin");
};

export const getRules = async (params?: { is_active?: boolean; offset?: number; limit?: number }) => {
  const qs = new URLSearchParams();
  if (params?.is_active !== undefined) qs.set("is_active", String(params.is_active));
  if (params?.offset !== undefined) qs.set("offset", String(params.offset));
  if (params?.limit !== undefined) qs.set("limit", String(params.limit));

  return request<{ total: number; items: DLPRule[] }>(`/api/enterprise/dlp/rules?${qs.toString()}`);
};

export const createRule = async (data: Omit<DLPRule, "id" | "is_builtin" | "created_at">) => {
  return request<DLPRule>("/api/enterprise/dlp/rules", {
    method: "POST",
    body: JSON.stringify(data),
  });
};

export const updateRule = async (id: string, data: Partial<Omit<DLPRule, "id" | "is_builtin" | "created_at">>) => {
  return request<DLPRule>(`/api/enterprise/dlp/rules/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
};

export const deleteRule = async (id: string) => {
  return request<{ detail: string }>(`/api/enterprise/dlp/rules/${id}`, {
    method: "DELETE",
  });
};

export const getEvents = async (params?: { rule_name?: string; action_taken?: string; offset?: number; limit?: number }) => {
  const qs = new URLSearchParams();
  if (params?.rule_name) qs.set("rule_name", params.rule_name);
  if (params?.action_taken) qs.set("action_taken", params.action_taken);
  if (params?.offset !== undefined) qs.set("offset", String(params.offset));
  if (params?.limit !== undefined) qs.set("limit", String(params.limit));

  return request<{ total: number; items: DLPEvent[] }>(`/api/enterprise/dlp/events?${qs.toString()}`);
};
