import { request } from "../request";

export interface DifyConnector {
  id: string;
  name: string;
  description?: string;
  api_url: string;
  is_active: boolean;
}

export interface DifyConnectorCreate {
  name: string;
  description?: string;
  api_url: string;
  api_key: string;
  is_active: boolean;
}

export interface DifyConnectorUpdate {
  name?: string;
  description?: string;
  api_url?: string;
  api_key?: string;
  is_active?: boolean;
}

export const difyConnectorsApi = {
  list: () =>
    request.get<DifyConnector[]>("/enterprise/dify/connectors"),

  create: (data: DifyConnectorCreate) =>
    request.post<DifyConnector>("/enterprise/dify/connectors", data),

  update: (id: string, data: DifyConnectorUpdate) =>
    request.put<DifyConnector>(`/enterprise/dify/connectors/${id}`, data),

  delete: (id: string) =>
    request.delete(`/enterprise/dify/connectors/${id}`),
};
