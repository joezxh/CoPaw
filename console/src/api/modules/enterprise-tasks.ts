/** Enterprise Tasks API */
import { request } from "../request";

export type TaskStatus = "pending" | "in_progress" | "blocked" | "completed" | "cancelled";
export type TaskPriority = "high" | "medium" | "low";

export interface Task {
  id: string;
  title: string;
  description?: string;
  status: TaskStatus;
  priority: TaskPriority;
  creator_id?: string;
  assignee_id?: string;
  due_date?: string;
  completed_at?: string;
  created_at: string;
  updated_at: string;
}

export interface TaskListResponse {
  total: number;
  items: Task[];
}

export const enterpriseTasksApi = {
  list: (params?: {
    assignee_id?: string;
    status?: TaskStatus;
    priority?: TaskPriority;
    workflow_id?: string;
    offset?: number;
    limit?: number;
  }) => {
    const q = new URLSearchParams();
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v !== undefined) q.set(k, String(v));
    });
    return request<TaskListResponse>(`/api/enterprise/tasks?${q}`);
  },

  create: (data: {
    title: string;
    description?: string;
    priority?: TaskPriority;
    assignee_id?: string;
    due_date?: string;
    workflow_id?: string;
    metadata?: Record<string, unknown>;
  }) =>
    request<Task>("/api/enterprise/tasks", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  get: (taskId: string) => request<Task>(`/api/enterprise/tasks/${taskId}`),

  update: (taskId: string, data: Partial<Pick<Task, "title" | "description" | "priority" | "assignee_id" | "due_date">>) =>
    request<Task>(`/api/enterprise/tasks/${taskId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  changeStatus: (taskId: string, status: TaskStatus) =>
    request<Task>(`/api/enterprise/tasks/${taskId}/status`, {
      method: "PUT",
      body: JSON.stringify({ status }),
    }),

  delete: (taskId: string) =>
    request<{ detail: string }>(`/api/enterprise/tasks/${taskId}`, {
      method: "DELETE",
    }),

  listComments: (taskId: string) =>
    request<{ id: string; content: string; author_id?: string; created_at: string }[]>(
      `/api/enterprise/tasks/${taskId}/comments`
    ),

  addComment: (taskId: string, content: string) =>
    request<{ id: string; content: string; created_at: string }>(
      `/api/enterprise/tasks/${taskId}/comments`,
      { method: "POST", body: JSON.stringify({ content }) }
    ),
};
