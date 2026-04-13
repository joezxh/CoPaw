/**
 * Enterprise Organization Management API
 * 
 * 组织机构管理 API - 基于 Department 模块增强
 */

export interface Organization {
  id: string;
  name: string;
  parent_id: string | null;
  manager_id: string | null;
  level: number;
  description: string | null;
  created_at: string;
  children?: Organization[];
}

export interface OrgMember {
  id: string;
  username: string;
  display_name: string | null;
  email: string;
  status: string;
}

export interface OrgStats {
  id: string;
  name: string;
  member_count: number;
  sub_department_count: number;
  level: number;
}

import { request } from "../request";

// Get organization tree (nested structure)
export const getOrgTree = async () => {
  return request<Organization[]>("/enterprise/departments/tree");
};

// Create organization
export const createOrg = async (data: { 
  name: string; 
  parent_id?: string; 
  manager_id?: string; 
  description?: string;
}) => {
  return request<Organization>("/enterprise/departments", {
    method: "POST",
    body: JSON.stringify(data),
  });
};

// Update organization
export const updateOrg = async (id: string, data: { 
  name?: string; 
  parent_id?: string; 
  manager_id?: string; 
  description?: string;
}) => {
  return request<Organization>(`/enterprise/departments/${id}`, {
    method: "PUT",
    body: JSON.stringify(data),
  });
};

// Delete organization
export const deleteOrg = async (id: string) => {
  return request<{ detail: string }>(`/enterprise/departments/${id}`, {
    method: "DELETE",
  });
};

// Get organization members
export const getOrgMembers = async (orgId: string) => {
  return request<OrgMember[]>(`/enterprise/departments/${orgId}/members`);
};

// Add members to organization
export const addOrgMembers = async (orgId: string, userIds: string[]) => {
  return request<{ added: number; total_requested: number }>(
    `/enterprise/departments/${orgId}/members`,
    {
      method: "POST",
      body: JSON.stringify({ user_ids: userIds }),
    }
  );
};

// Remove member from organization
export const removeOrgMember = async (orgId: string, userId: string) => {
  return request<{ detail: string }>(
    `/enterprise/departments/${orgId}/members/${userId}`,
    {
      method: "DELETE",
    }
  );
};

// Get organization statistics
export const getOrgStats = async (orgId: string) => {
  return request<OrgStats>(`/enterprise/departments/${orgId}/stats`);
};
