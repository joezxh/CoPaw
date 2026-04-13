export interface AlertRule {
  id: string;
  rule_type: string;
  description: string | null;
  threshold: number;
  window_seconds: number;
  notify_channels: string[];
  is_active: boolean;
  created_at: string;
}

export interface AlertEvent {
  id: string;
  rule_type: string;
  triggered_at: string;
  context: object | null;
  notify_status: string | null;
}

import { request } from "../request";

export const getAlertRules = async (params?: { is_active?: boolean }) => {
  const qs = new URLSearchParams();
  if (params?.is_active !== undefined) qs.set("is_active", String(params.is_active));

  return request<AlertRule[]>(`/enterprise/alerts/rules?${qs.toString()}`);
};

export const createAlertRule = async (data: Omit<AlertRule, "id" | "created_at">) => {
  return request<AlertRule>("/enterprise/alerts/rules", {
    method: "POST",
    body: JSON.stringify(data),
  });
};

export const updateAlertRule = async (id: string, data: Partial<Omit<AlertRule, "id" | "rule_type" | "created_at">>) => {
  return request<AlertRule>(`/enterprise/alerts/rules/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
};

export const deleteAlertRule = async (id: string) => {
  return request<{ detail: string }>(`/enterprise/alerts/rules/${id}`, {
    method: "DELETE",
  });
};

export const getAlertEvents = async (params?: { rule_type?: string; offset?: number; limit?: number }) => {
  const qs = new URLSearchParams();
  if (params?.rule_type) qs.set("rule_type", params.rule_type);
  if (params?.offset !== undefined) qs.set("offset", String(params.offset));
  if (params?.limit !== undefined) qs.set("limit", String(params.limit));

  return request<{ total: number; items: AlertEvent[] }>(`/enterprise/alerts/events?${qs.toString()}`);
};

export const testNotification = async (message: string) => {
  return request<{ detail: string }>("/enterprise/alerts/test", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
};
