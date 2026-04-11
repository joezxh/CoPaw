/** Enterprise Roles & Permissions API */
import { request } from "../request";

export interface Role {
  id: string;
  name: string;
  description?: string;
  level: number;
  parent_role_id?: string;
  department_id?: string;
  is_system_role: boolean;
  created_at: string;
}

export interface Permission {
  id: string;
  resource: string;
  action: string;
  description?: string;
}

export const enterpriseRolesApi = {
  listRoles: (search?: string) => {
    const q = search ? `?search=${encodeURIComponent(search)}` : "";
    return request<Role[]>(`/api/enterprise/roles${q}`);
  },

  createRole: (data: {
    name: string;
    description?: string;
    parent_role_id?: string;
    department_id?: string;
    is_system_role?: boolean;
  }) =>
    request<Role>("/api/enterprise/roles", {
      method: "POST",
      body: JSON.stringify(data),
    }),

  getRole: (roleId: string) => request<Role>(`/api/enterprise/roles/${roleId}`),

  updateRole: (roleId: string, data: { description?: string; department_id?: string }) =>
    request<Role>(`/api/enterprise/roles/${roleId}`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),

  deleteRole: (roleId: string) =>
    request<{ detail: string }>(`/api/enterprise/roles/${roleId}`, {
      method: "DELETE",
    }),

  getRolePermissions: (roleId: string) =>
    request<Permission[]>(`/api/enterprise/roles/${roleId}/permissions`),

  setRolePermissions: (roleId: string, permissionIds: string[]) =>
    request<{ detail: string }>(
      `/api/enterprise/roles/${roleId}/permissions`,
      { method: "PUT", body: JSON.stringify({ permission_ids: permissionIds }) }
    ),

  listPermissions: () => request<Permission[]>("/api/enterprise/permissions"),

  createPermission: (data: {
    resource: string;
    action: string;
    description?: string;
  }) =>
    request<Permission>("/api/enterprise/permissions", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};
