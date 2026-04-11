/** Enterprise Workflows API — supports Dify categories */
import { request } from "../request";

export type WorkflowCategory = "dify" | "dify_chatflow" | "dify_agent" | "internal";
export type WorkflowStatus = "draft" | "active" | "archived";

export interface Workflow {
  id: string;
  name: string;
  category: WorkflowCategory;
  description?: string;
  version: number;
  status: WorkflowStatus;
  creator_id?: string;
  definition: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  triggered_by?: string;
  status: "pending" | "running" | "paused" | "completed" | "failed" | "cancelled";
  input_data?: Record<string, unknown>;
  output_data?: Record<string, unknown>;
  started_at?: string;
  completed_at?: string;
  error_message?: string;
  created_at: string;
}

export const enterpriseWorkflowsApi = {
  list: (params?: {
    category?: WorkflowCategory;
    status?: WorkflowStatus;
    offset?: number;
    limit?: number;
  }) => {
    const q = new URLSearchParams();
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v !== undefined) q.set(k, String(v));
    });
    return request<{ total: number; items: Workflow[] }>(
      `/api/enterprise/workflows?${q}`
    );
  },

  create: (data: {
    name: string;
    category: WorkflowCategory;
    description?: string;
    definition?: Record<string, unknown>;
  }) =>
    request<Workflow>("/api/enterprise/workflows", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  get: (id: string) => request<Workflow>(`/api/enterprise/workflows/${id}`),

  update: (
    id: string,
    data: Partial<{
      name: string;
      description: string;
      definition: Record<string, unknown>;
      status: WorkflowStatus;
      category: WorkflowCategory;
    }>
  ) =>
    request<Workflow>(`/api/enterprise/workflows/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  delete: (id: string) =>
    request<{ detail: string }>(`/api/enterprise/workflows/${id}`, {
      method: "DELETE",
    }),

  execute: (id: string, inputData?: Record<string, unknown>) =>
    request<WorkflowExecution>(`/api/enterprise/workflows/${id}/execute`, {
      method: "POST",
      body: JSON.stringify({ input_data: inputData }),
    }),

  listExecutions: (id: string, params?: { status?: string; offset?: number; limit?: number }) => {
    const q = new URLSearchParams();
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v !== undefined) q.set(k, String(v));
    });
    return request<WorkflowExecution[]>(
      `/api/enterprise/workflows/${id}/executions?${q}`
    );
  },
};
