export interface UserGroup {
  id: string;
  name: string;
  description: string | null;
  department_id: string | null;
  created_at: string;
}

export interface GroupMember {
  user_id: string;
  username: string;
  display_name: string | null;
  joined_at: string;
}

import { request } from "../request";

export const getGroups = async (params?: { department_id?: string; offset?: number; limit?: number }) => {
  const qs = new URLSearchParams();
  if (params?.department_id) qs.set("department_id", params.department_id);
  if (params?.offset !== undefined) qs.set("offset", String(params.offset));
  if (params?.limit !== undefined) qs.set("limit", String(params.limit));
  
  return request<{ total: number; items: UserGroup[] }>(`/api/enterprise/user-groups?${qs.toString()}`);
};

export const createGroup = async (data: { name: string; description?: string; department_id?: string }) => {
  return request<UserGroup>("/api/enterprise/user-groups", {
    method: "POST",
    body: JSON.stringify(data),
  });
};

export const updateGroup = async (id: string, data: { name?: string; description?: string; department_id?: string }) => {
  return request<UserGroup>(`/api/enterprise/user-groups/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
};

export const deleteGroup = async (id: string) => {
  return request<{ detail: string }>(`/api/enterprise/user-groups/${id}`, {
    method: "DELETE",
  });
};

export const getGroupMembers = async (groupId: string) => {
  return request<GroupMember[]>(`/api/enterprise/user-groups/${groupId}/members`);
};

export const addGroupMembers = async (groupId: string, userIds: string[]) => {
  return request<{ detail: string; added: number; existing: number }>(`/api/enterprise/user-groups/${groupId}/members`, {
    method: "POST",
    body: JSON.stringify({ user_ids: userIds }),
  });
};

export const removeGroupMembers = async (groupId: string, userIds: string[]) => {
  return request<{ detail: string; removed: number }>(`/api/enterprise/user-groups/${groupId}/members`, {
    method: "DELETE",
    body: JSON.stringify(userIds),
  });
};
