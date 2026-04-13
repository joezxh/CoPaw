/** Enterprise Audit Log API */
import { request } from "../request";

export interface AuditLogEntry {
  id: number;
  timestamp: string;
  user_id?: string;
  user_role?: string;
  action_type: string;
  resource_type: string;
  resource_id?: string;
  action_result?: string;
  client_ip?: string;
  is_sensitive: boolean;
  context?: Record<string, unknown>;
}

export interface AuditLogResponse {
  total: number;
  offset: number;
  limit: number;
  items: AuditLogEntry[];
}

export const enterpriseAuditApi = {
  query: (params?: {
    user_id?: string;
    action_type?: string;
    resource_type?: string;
    result?: string;
    from?: string;
    to?: string;
    is_sensitive?: boolean;
    offset?: number;
    limit?: number;
  }) => {
    const q = new URLSearchParams();
    Object.entries(params || {}).forEach(([k, v]) => {
      if (v !== undefined) q.set(k, String(v));
    });
    return request<AuditLogResponse>(`/enterprise/audit?${q}`);
  },
};
