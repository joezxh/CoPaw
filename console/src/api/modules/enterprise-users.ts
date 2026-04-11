/** Enterprise Users API */
import { request } from "../request";

export interface User {
  id: string;
  username: string;
  email?: string;
  display_name?: string;
  department_id?: string;
  status: "active" | "disabled" | "vacation";
  mfa_enabled: boolean;
  last_login_at?: string;
  created_at: string;
}

export interface UserListResponse {
  total: number;
  offset: number;
  limit: number;
  items: User[];
}

export interface CreateUserRequest {
  username: string;
  password: string;
  email?: string;
  display_name?: string;
  department_id?: string;
  status?: string;
}

export interface UpdateUserRequest {
  email?: string;
  display_name?: string;
  department_id?: string;
  status?: string;
}

export const enterpriseUsersApi = {
  list: (params?: {
    search?: string;
    status?: string;
    department_id?: string;
    offset?: number;
    limit?: number;
  }) => {
    const q = new URLSearchParams();
    if (params?.search) q.set("search", params.search);
    if (params?.status) q.set("status", params.status);
    if (params?.department_id) q.set("department_id", params.department_id);
    if (params?.offset !== undefined) q.set("offset", String(params.offset));
    if (params?.limit !== undefined) q.set("limit", String(params.limit));
    return request<UserListResponse>(`/api/enterprise/users?${q}`);
  },

  create: (data: CreateUserRequest) =>
    request<User>("/api/enterprise/users", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  get: (userId: string) => request<User>(`/api/enterprise/users/${userId}`),

  update: (userId: string, data: UpdateUserRequest) =>
    request<User>(`/api/enterprise/users/${userId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  disable: (userId: string) =>
    request<{ detail: string }>(`/api/enterprise/users/${userId}`, {
      method: "DELETE",
    }),

  getRoles: (userId: string) =>
    request<{ id: string; name: string; level: number }[]>(
      `/api/enterprise/users/${userId}/roles`
    ),

  assignRoles: (userId: string, roleIds: string[]) =>
    request<{ detail: string }>(`/api/enterprise/users/${userId}/roles`, {
      method: "PUT",
      body: JSON.stringify({ role_ids: roleIds }),
    }),
};
